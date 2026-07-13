#!/usr/bin/env python3
"""Guard generated PERF-14 promotion metric reads.

EU5/Jomini treats zero-valued globals as absent in some `global_var:` reads. The
PERF-14 promotion generator intentionally uses per-good scratch globals whose
natural default is zero. Generated code must therefore read those globals only
behind `has_global_variable`, with an explicit temporary/default value.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

GUARDED_GLOBALS = {
    "cbp_perf14_promotion_market_total_capacity",
    "cbp_perf14_promotion_market_eligible_country_count",
    "cbp_perf14_promotion_market_allocated_quantity",
    "cbp_perf14_promotion_market_negative_capacity_failure",
}

BLOCK_START_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)(?P<kind>save_temporary_scope_value_as|set_global_variable)\s*=\s*\{"
)
IDENT_RE = re.compile(r"[A-Za-z0-9_:.|$\-/]+")


def find_matching_brace(source: str, open_index: int) -> int:
    """Return the index just after the brace matching source[open_index]."""

    if open_index >= len(source) or source[open_index] != "{":
        raise ValueError("find_matching_brace called without an opening brace")

    depth = 0
    in_string = False
    index = open_index
    while index < len(source):
        char = source[index]

        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
        elif char == "#":
            newline = source.find("\n", index)
            if newline < 0:
                return len(source)
            index = newline
            continue
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                raise ValueError("brace depth became negative")
        index += 1

    raise ValueError("unterminated brace block")


def skip_ws_and_comments(source: str, index: int) -> int:
    while index < len(source):
        if source[index].isspace():
            index += 1
            continue
        if source[index] == "#":
            newline = source.find("\n", index)
            if newline < 0:
                return len(source)
            index = newline + 1
            continue
        break
    return index


def parse_scalar_or_block(source: str, index: int) -> tuple[str, int]:
    index = skip_ws_and_comments(source, index)
    if index >= len(source):
        return "", index

    if source[index] == "{":
        end = find_matching_brace(source, index)
        return source[index:end], end

    if source[index] == '"':
        end = index + 1
        while end < len(source):
            if source[end] == "\\":
                end += 2
                continue
            if source[end] == '"':
                return source[index : end + 1], end + 1
            end += 1
        raise ValueError("unterminated quoted string")

    match = IDENT_RE.match(source, index)
    if match is None:
        return source[index], index + 1
    return match.group(0), match.end()


def parse_top_level_assignments(block_inner: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    index = 0
    while index < len(block_inner):
        index = skip_ws_and_comments(block_inner, index)
        if index >= len(block_inner):
            break

        key_match = IDENT_RE.match(block_inner, index)
        if key_match is None:
            index += 1
            continue

        key = key_match.group(0)
        index = skip_ws_and_comments(block_inner, key_match.end())
        if index >= len(block_inner) or block_inner[index] != "=":
            index += 1
            continue

        value, index = parse_scalar_or_block(block_inner, index + 1)
        assignments[key] = value.strip()

    return assignments


def block_inner(block: str) -> str:
    open_index = block.find("{")
    close_index = block.rfind("}")
    if open_index < 0 or close_index < open_index:
        raise ValueError("malformed block")
    return block[open_index + 1 : close_index]


def is_immediately_guarded(source: str, block_start: int, block_indent: str, glob: str) -> bool:
    """Detect the guarded branch shape emitted by this postprocessor.

    This deliberately checks the immediate surrounding `if`/`limit` lines instead
    of allowing any earlier `has_global_variable` mention to mask an unsafe read.
    """

    if not block_indent:
        return False

    parent_indent = block_indent[:-1] if block_indent[-1] in "\t " else block_indent
    line_start = source.rfind("\n", 0, block_start) + 1
    prefix = source[max(0, line_start - 600) : line_start]
    nonempty_lines = [line.rstrip() for line in prefix.splitlines() if line.strip()]
    if len(nonempty_lines) < 2:
        return False

    return (
        nonempty_lines[-2] == f"{parent_indent}if = {{"
        and nonempty_lines[-1] == f"{block_indent}limit = {{ has_global_variable = {glob} }}"
    )


def render_guarded_save(indent: str, temp: str, glob: str) -> str:
    return (
        f"{indent}save_temporary_scope_value_as = {{ name = {temp} value = 0 }}\n"
        f"{indent}if = {{\n"
        f"{indent}\tlimit = {{ has_global_variable = {glob} }}\n"
        f"{indent}\tsave_temporary_scope_value_as = {{\n"
        f"{indent}\t\tname = {temp}\n"
        f"{indent}\t\tvalue = global_var:{glob}\n"
        f"{indent}\t}}\n"
        f"{indent}}}"
    )


def render_guarded_accumulator(indent: str, glob: str, add_value: str) -> str:
    add_value = add_value.strip()
    return (
        f"{indent}if = {{\n"
        f"{indent}\tlimit = {{ has_global_variable = {glob} }}\n"
        f"{indent}\tset_global_variable = {{\n"
        f"{indent}\t\tname = {glob}\n"
        f"{indent}\t\tvalue = {{\n"
        f"{indent}\t\t\tvalue = global_var:{glob}\n"
        f"{indent}\t\t\tadd = {add_value}\n"
        f"{indent}\t\t}}\n"
        f"{indent}\t}}\n"
        f"{indent}}}\n"
        f"{indent}else = {{\n"
        f"{indent}\tset_global_variable = {{ name = {glob} value = {add_value} }}\n"
        f"{indent}}}"
    )


def replacement_for_block(source: str, match: re.Match[str], block: str) -> str | None:
    indent = match.group("indent")
    kind = match.group("kind")
    assignments = parse_top_level_assignments(block_inner(block))

    if kind == "save_temporary_scope_value_as":
        temp = assignments.get("name")
        value = assignments.get("value")
        if temp is None or value is None or not value.startswith("global_var:"):
            return None
        glob = value.removeprefix("global_var:")
        if glob not in GUARDED_GLOBALS:
            return None
        if is_immediately_guarded(source, match.start(), indent, glob):
            return None
        return render_guarded_save(indent, temp, glob)

    glob = assignments.get("name")
    value_block = assignments.get("value")
    if glob not in GUARDED_GLOBALS or value_block is None or not value_block.startswith("{"):
        return None

    value_assignments = parse_top_level_assignments(value_block[1:-1])
    if value_assignments.get("value") != f"global_var:{glob}" or "add" not in value_assignments:
        return None
    if is_immediately_guarded(source, match.start(), indent, glob):
        return None
    return render_guarded_accumulator(indent, glob, value_assignments["add"])


def rewrite_unsafe_generated_reads(text: str) -> str:
    pieces: list[str] = []
    position = 0
    search_from = 0

    while True:
        match = BLOCK_START_RE.search(text, search_from)
        if match is None:
            break

        open_index = text.find("{", match.start(), match.end())
        end = find_matching_brace(text, open_index)
        block = text[match.start() : end]
        replacement = replacement_for_block(text, match, block)

        if replacement is not None:
            pieces.append(text[position : match.start()])
            pieces.append(replacement)
            position = end

        search_from = end

    pieces.append(text[position:])
    return "".join(pieces)


def iter_direct_unsafe_reads(text: str) -> list[tuple[int, str]]:
    unsafe: list[tuple[int, str]] = []
    search_from = 0
    while True:
        match = BLOCK_START_RE.search(text, search_from)
        if match is None:
            break

        open_index = text.find("{", match.start(), match.end())
        end = find_matching_brace(text, open_index)
        block = text[match.start() : end]
        indent = match.group("indent")
        kind = match.group("kind")
        assignments = parse_top_level_assignments(block_inner(block))
        glob: str | None = None

        if kind == "save_temporary_scope_value_as":
            value = assignments.get("value", "")
            if value.startswith("global_var:"):
                candidate = value.removeprefix("global_var:")
                if candidate in GUARDED_GLOBALS:
                    glob = candidate
        else:
            name = assignments.get("name")
            value_block = assignments.get("value", "")
            if name in GUARDED_GLOBALS and value_block.startswith("{"):
                value_assignments = parse_top_level_assignments(value_block[1:-1])
                if value_assignments.get("value") == f"global_var:{name}" and "add" in value_assignments:
                    glob = name

        if glob is not None and not is_immediately_guarded(text, match.start(), indent, glob):
            line_no = text.count("\n", 0, match.start()) + 1
            unsafe.append((line_no, glob))

        search_from = end

    return unsafe


def assert_no_unguarded_generated_reads(text: str) -> None:
    """Reject only direct unsafe generated source shapes.

    Guarded replacements still contain `global_var:<name>` inside an explicit
    `has_global_variable` branch, so this check does not fail merely because the
    guarded read remains present inside that branch.
    """

    unsafe = iter_direct_unsafe_reads(text)
    if unsafe:
        details = "\n".join(f"line {line_no}: {glob}" for line_no, glob in unsafe[:20])
        raise SystemExit(f"unguarded PERF-14 promotion global reads remain:\n{details}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: postprocess_perf14_promotion_guards.py <cbp_stock_goods_generated.txt>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    text = path.read_text()
    updated = rewrite_unsafe_generated_reads(text)
    assert_no_unguarded_generated_reads(updated)

    path.write_text(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

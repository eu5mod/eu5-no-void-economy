#!/usr/bin/env python3
"""Generate the US-04 vanilla pop_demand runtime probe.

The generator reads the installed EU5 `common/goods_demand/pop_demands.txt`,
preserves the complete vanilla file, and wraps only explicitly selected goods
(default: wheat) with a ModeU5 location × good multiplier script value.

The generated files are local build artifacts and are intentionally ignored by
Git. They are installed only through the optional Rebalance Economy package.
The probe must pass in EU5 before the wrapper is generalized to every good.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn


IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True)
class Assignment:
    key: str
    rhs_start: int
    rhs_end: int
    indent: str


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def skip_string(text: str, index: int) -> int:
    assert text[index] == '"'
    index += 1
    escaped = False
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return index + 1
        index += 1
    fail("Unclosed quoted string while parsing vanilla pop_demands.txt")


def skip_comment(text: str, index: int) -> int:
    while index < len(text) and text[index] != "\n":
        index += 1
    return index


def skip_space_and_comments(text: str, index: int, end: int) -> int:
    while index < end:
        if text[index].isspace():
            index += 1
            continue
        if text[index] == "#":
            index = skip_comment(text, index)
            continue
        break
    return index


def find_matching_brace(text: str, open_index: int) -> int:
    if text[open_index] != "{":
        fail(f"Expected opening brace at offset {open_index}")
    depth = 1
    index = open_index + 1
    while index < len(text):
        char = text[index]
        if char == '"':
            index = skip_string(text, index)
            continue
        if char == "#":
            index = skip_comment(text, index)
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    fail(f"Unclosed block starting at offset {open_index}")


def find_top_level_object(text: str, object_name: str) -> tuple[int, int]:
    index = 0
    depth = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            index = skip_string(text, index)
            continue
        if char == "#":
            index = skip_comment(text, index)
            continue
        if char == "{":
            depth += 1
            index += 1
            continue
        if char == "}":
            depth -= 1
            index += 1
            continue
        if depth == 0:
            match = IDENTIFIER_RE.match(text, index)
            if match:
                key = match.group(0)
                cursor = skip_space_and_comments(text, match.end(), len(text))
                if cursor < len(text) and text[cursor] == "=":
                    cursor = skip_space_and_comments(text, cursor + 1, len(text))
                    if key == object_name and cursor < len(text) and text[cursor] == "{":
                        return cursor, find_matching_brace(text, cursor)
                index = match.end()
                continue
        index += 1
    fail(f"Could not find top-level `{object_name} = {{ ... }}` in vanilla pop_demands.txt")


def line_indent(text: str, index: int) -> str:
    line_start = text.rfind("\n", 0, index) + 1
    prefix = text[line_start:index]
    match = re.match(r"[ \t]*", prefix)
    return match.group(0) if match else ""


def parse_direct_assignments(text: str, block_open: int, block_close: int) -> list[Assignment]:
    assignments: list[Assignment] = []
    index = block_open + 1
    while index < block_close:
        index = skip_space_and_comments(text, index, block_close)
        if index >= block_close:
            break
        match = IDENTIFIER_RE.match(text, index)
        if not match:
            line = text.count("\n", 0, index) + 1
            fail(f"Unexpected token in top-level pop_demand body at line {line}: {text[index:index + 40]!r}")
        key = match.group(0)
        indent = line_indent(text, index)
        cursor = skip_space_and_comments(text, match.end(), block_close)
        if cursor >= block_close or text[cursor] != "=":
            fail(f"Expected `=` after pop_demand key `{key}`")
        rhs_start = skip_space_and_comments(text, cursor + 1, block_close)
        if rhs_start >= block_close:
            fail(f"Missing value for pop_demand key `{key}`")
        if text[rhs_start] == "{":
            rhs_end = find_matching_brace(text, rhs_start) + 1
        elif text[rhs_start] == '"':
            rhs_end = skip_string(text, rhs_start)
        else:
            rhs_end = rhs_start
            while rhs_end < block_close and text[rhs_end] not in "\r\n#":
                rhs_end += 1
            while rhs_end > rhs_start and text[rhs_end - 1].isspace():
                rhs_end -= 1
        assignments.append(Assignment(key=key, rhs_start=rhs_start, rhs_end=rhs_end, indent=indent))
        index = rhs_end
    return assignments


def indent_block(text: str, prefix: str) -> str:
    lines = text.splitlines()
    if len(lines) == 1:
        return text
    return ("\n" + prefix).join(lines)


def wrap_rhs(original_rhs: str, assignment: Assignment) -> str:
    inner_indent = assignment.indent + "\t"
    original = indent_block(original_rhs, inner_indent)
    return (
        "{\n"
        f"{inner_indent}value = {original}\n"
        f'{inner_indent}multiply = "modeu5_us04_live_pop_demand_multiplier_{assignment.key}"\n'
        f"{assignment.indent}}}"
    )


def rewrite_pop_demand(source: str, selected_goods: list[str]) -> tuple[str, list[str]]:
    block_open, block_close = find_top_level_object(source, "pop_demand")
    assignments = parse_direct_assignments(source, block_open, block_close)
    if not assignments:
        fail("Vanilla pop_demand object contains no direct good coefficients")

    counts: dict[str, int] = {}
    for assignment in assignments:
        counts[assignment.key] = counts.get(assignment.key, 0) + 1
    duplicate_keys = sorted(key for key, count in counts.items() if count > 1)
    if duplicate_keys:
        fail("Vanilla pop_demand contains duplicate direct keys: " + ", ".join(duplicate_keys))

    requested = list(dict.fromkeys(selected_goods))
    available = {assignment.key for assignment in assignments}
    missing = [good for good in requested if good not in available]
    if missing:
        fail("Requested US-04 probe goods are absent from vanilla pop_demand: " + ", ".join(missing))

    selected = [assignment for assignment in assignments if assignment.key in requested]
    rewritten = source
    for assignment in reversed(selected):
        original_rhs = source[assignment.rhs_start:assignment.rhs_end]
        rewritten = rewritten[:assignment.rhs_start] + wrap_rhs(original_rhs, assignment) + rewritten[assignment.rhs_end:]

    header = (
        "# Generated by tools/generate_us04_pop_demand_override.py.\n"
        "# Exact-path runtime probe preserving the complete vanilla pop_demands.txt.\n"
        f"# Wrapped probe goods: {', '.join(assignment.key for assignment in selected)}.\n"
        "# Do not edit manually; regenerate after every EU5 update.\n\n"
    )
    return header + rewritten.lstrip("\n"), [assignment.key for assignment in selected]


def generate_script_values(goods: list[str]) -> str:
    lines = [
        "# Generated by tools/generate_us04_pop_demand_override.py.",
        "# Do not edit manually.",
        "# Evaluated from Pop scope by the hardcoded vanilla pop_demand definition.",
        "# Missing, disabled, uninitialized, or invalid ModeU5 state returns 1 (vanilla).",
        "",
    ]
    for good in goods:
        lines.extend(
            [
                f"modeu5_us04_live_pop_demand_multiplier_{good} = {{",
                "\tvalue = 1",
                "\tif = {",
                "\t\tlimit = {",
                "\t\t\thas_global_variable = modeu5_pop_demand_live_integration_enabled",
                "\t\t\thas_global_variable = modeu5_us04_multiplier_initialization_version",
                "\t\t\tglobal_var:modeu5_us04_multiplier_initialization_version >= 1",
                "\t\t\tlocation = {",
                "\t\t\t\thas_variable_map = modeu5_pop_demand_multiplier",
                "\t\t\t\tis_key_in_variable_map = {",
                "\t\t\t\t\tname = modeu5_pop_demand_multiplier",
                f"\t\t\t\t\ttarget = goods:{good}",
                "\t\t\t\t}",
                "\t\t\t}",
                "\t\t}",
                "\t\tvalue = {",
                "\t\t\tlocation = {",
                f'\t\t\t\tvalue = "variable_map(modeu5_pop_demand_multiplier|goods:{good})"',
                "\t\t\t}",
                "\t\t}",
                "\t}",
                "}",
                "",
            ]
        )
    return "\n".join(lines)


def assert_balanced(text: str, label: str) -> None:
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            index = skip_string(text, index)
            continue
        if char == "#":
            index = skip_comment(text, index)
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                fail(f"{label} has an unexpected closing brace")
        index += 1
    if depth != 0:
        fail(f"{label} has {depth} unclosed opening brace(s)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--common-dir",
        type=Path,
        default=Path(os.environ["EU5_GAME_COMMON_DIR"]) if os.environ.get("EU5_GAME_COMMON_DIR") else None,
        help="EU5 game/in_game/common directory; defaults to EU5_GAME_COMMON_DIR",
    )
    parser.add_argument(
        "--package-common-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "packages" / "modeu5_economy_rebalance" / "in_game" / "common",
    )
    parser.add_argument(
        "--goods",
        nargs="+",
        default=["wheat"],
        help="Vanilla pop_demand goods to wrap for the runtime probe (default: wheat)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.common_dir is None:
        fail("Set EU5_GAME_COMMON_DIR or pass --common-dir")
    source_path = args.common_dir / "goods_demand" / "pop_demands.txt"
    if not source_path.is_file():
        fail(f"Missing vanilla Pop-demand source: {source_path}")

    source = source_path.read_text(encoding="utf-8-sig").removeprefix("\ufeff")
    demand_override, goods = rewrite_pop_demand(source, args.goods)
    script_values = generate_script_values(goods)
    assert_balanced(demand_override, "Generated pop_demand override")
    assert_balanced(script_values, "Generated US-04 live script values")

    demand_output = args.package_common_dir / "goods_demand" / "pop_demands.txt"
    values_output = args.package_common_dir / "script_values" / "modeu5_us04_pop_demand_values_generated.txt"
    demand_output.parent.mkdir(parents=True, exist_ok=True)
    values_output.parent.mkdir(parents=True, exist_ok=True)
    demand_output.write_text(demand_override, encoding="utf-8")
    values_output.write_text(script_values, encoding="utf-8")

    print(f"Generated US-04 vanilla Pop-demand probe for {len(goods)} good(s): {', '.join(goods)}.")
    print(f"Source: {source_path}")
    print(f"Output: {demand_output}")
    print(f"Output: {values_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

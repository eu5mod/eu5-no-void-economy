#!/usr/bin/env python3
"""Analyze CBP variable namespaces without modifying repository files."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOTS = [ROOT / "in_game", ROOT / "main_menu", ROOT / "packages"]
SUFFIXES = {".txt", ".gui"}
IDENT = r"[A-Za-z_][A-Za-z0-9_$]*"
ASSIGNMENT_RE = re.compile(r"\b(?P<op>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*")
NAME_RE = re.compile(rf"\bname\s*=\s*(?P<name>{IDENT})")
DIRECT_RE = re.compile(rf"(?P<name>{IDENT})")
SCOPE_ALIAS_RE = re.compile(rf"\bsave_(?:temporary_)?scope_as\s*=\s*(?P<name>{IDENT})")
SCOPE_REF_RE = re.compile(rf"\bscope:(?P<name>{IDENT})")
TOP_LEVEL_RE = re.compile(rf"(?m)^\s*(?P<name>{IDENT})\s*=\s*\{{")
VAR_REF_RE = re.compile(rf"\b(?:var|global_var):(?P<name>{IDENT})")
MAP_REF_RE = re.compile(rf"\bvariable_map\((?P<name>{IDENT})\|")


def is_variable_operation(op: str) -> bool:
    if op == "save_temporary_scope_value_as":
        return True
    return "variable" in op and op.startswith((
        "set_", "change_", "remove_", "has_", "clear_", "add_to_",
        "remove_from_", "is_target_in_", "ordered_", "every_", "random_",
    ))


def matching_brace(text: str, start: int) -> int | None:
    depth = 0
    quote = False
    escape = False
    for i in range(start, len(text)):
        char = text[i]
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                quote = False
            continue
        if char == '"':
            quote = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
    return None


def add(bucket: dict[str, list[str]], name: str, path: Path, offset: int, text: str) -> None:
    line = text.count("\n", 0, offset) + 1
    bucket[name].append(f"{path.relative_to(ROOT)}:{line}")


def main() -> None:
    variables: dict[str, list[str]] = defaultdict(list)
    aliases: dict[str, list[str]] = defaultdict(list)
    scope_refs: dict[str, list[str]] = defaultdict(list)
    top_level: dict[str, list[str]] = defaultdict(list)

    for root in ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8-sig", errors="ignore")

            for match in VAR_REF_RE.finditer(text):
                add(variables, match.group("name"), path, match.start(), text)
            for match in MAP_REF_RE.finditer(text):
                add(variables, match.group("name"), path, match.start(), text)
            for match in SCOPE_ALIAS_RE.finditer(text):
                add(aliases, match.group("name"), path, match.start(), text)
            for match in SCOPE_REF_RE.finditer(text):
                add(scope_refs, match.group("name"), path, match.start(), text)
            for match in TOP_LEVEL_RE.finditer(text):
                add(top_level, match.group("name"), path, match.start(), text)

            for match in ASSIGNMENT_RE.finditer(text):
                if not is_variable_operation(match.group("op")):
                    continue
                cursor = match.end()
                while cursor < len(text) and text[cursor].isspace():
                    cursor += 1
                if cursor >= len(text):
                    continue
                if text[cursor] == "{":
                    end = matching_brace(text, cursor)
                    if end is None:
                        continue
                    name_match = NAME_RE.search(text, cursor + 1, end)
                    if name_match:
                        add(variables, name_match.group("name"), path, name_match.start(), text)
                else:
                    direct = DIRECT_RE.match(text, cursor)
                    if direct:
                        add(variables, direct.group("name"), path, direct.start(), text)

    variable_names = set(variables)
    alias_overlap = sorted(variable_names & set(aliases))
    object_overlap = sorted(variable_names & set(top_level))
    unprefixed = sorted(
        name for name in variable_names
        if not name.startswith(("modeu5_", "nve_", "cbp_", "test_cbp_", "gui_cbp_"))
    )

    report = {
        "variable_count": len(variable_names),
        "saved_scope_alias_count": len(aliases),
        "variable_saved_scope_overlap_count": len(alias_overlap),
        "variable_script_object_overlap_count": len(object_overlap),
        "unprefixed_candidate_count": len(unprefixed),
        "variable_saved_scope_overlap": {
            name: {
                "variable_sites": variables[name],
                "alias_sites": aliases[name],
                "scope_reference_sites": scope_refs.get(name, []),
            }
            for name in alias_overlap
        },
        "variable_script_object_overlap": {
            name: {
                "variable_sites": variables[name],
                "script_object_sites": top_level[name],
            }
            for name in object_overlap
        },
        "unprefixed_candidates": {
            name: variables[name] for name in unprefixed
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

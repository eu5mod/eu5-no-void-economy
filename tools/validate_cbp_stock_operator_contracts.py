#!/usr/bin/env python3
"""Validate explicit stock-operator call contracts.

ModeU5 stock remains country-owned source-of-truth state with a derived market
aggregate/cache. Callers must therefore mutate stock through the central
operators and explicitly declare whether the central operator should also apply
the matching vanilla market-supply delta.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CALL_CONTRACTS = {
    "cbp_add_stock": "only_add_at_country_level",
    "cbp_remove_stock": "only_remove_at_country_level",
}

SCAN_ROOTS = [
    "in_game/common/scripted_effects",
    "packages",
    "tools/templates",
    "tools/generate_us20_promoted_destination_receipt_dispatchers.sh",
]

SCAN_SUFFIXES = {".txt", ".template.txt", ".sh"}


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    operator: str
    required_field: str


def iter_scan_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for item in SCAN_ROOTS:
        path = root / item
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for candidate in path.rglob("*"):
            if candidate.is_file() and (
                candidate.suffix in SCAN_SUFFIXES
                or candidate.name.endswith(".template.txt")
            ):
                files.append(candidate)
    return sorted(set(files))


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def is_comment_match(text: str, offset: int) -> bool:
    line_start = text.rfind("\n", 0, offset) + 1
    return text[line_start:offset].lstrip().startswith("#")


def find_matching_brace(text: str, open_brace: int) -> int | None:
    depth = 0
    in_quote = False
    index = open_brace
    while index < len(text):
        char = text[index]
        if char == '"' and (index == 0 or text[index - 1] != "\\"):
            in_quote = not in_quote
        elif not in_quote:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index
        index += 1
    return None


def iter_operator_blocks(text: str):
    pattern = re.compile(r"\b(cbp_add_stock|cbp_remove_stock)\s*=\s*\{")
    for match in pattern.finditer(text):
        if is_comment_match(text, match.start()):
            continue
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_prefix = text[line_start : match.start()]
        if line_prefix == "":
            continue
        indent = line_prefix if line_prefix.strip() == "" else ""
        inline = line_prefix.strip() != ""
        operator = match.group(1)
        open_brace = text.find("{", match.start())
        close_brace = find_matching_brace(text, open_brace)
        if close_brace is None:
            continue
        yield operator, match.start(), open_brace, close_brace, indent, inline


def find_violations(path: Path, text: str) -> list[Violation]:
    violations: list[Violation] = []
    for operator, start, _open_brace, close_brace, _indent, _inline in iter_operator_blocks(text):
        required_field = CALL_CONTRACTS[operator]
        block = text[start : close_brace + 1]
        if re.search(rf"\b{re.escape(required_field)}\s*=\s*(?:yes|no)\b", block) is None:
            violations.append(
                Violation(
                    path=path,
                    line=line_for_offset(text, start),
                    operator=operator,
                    required_field=required_field,
                )
            )
    return violations


def insert_contract_field(block: str, required_field: str, *, indent: str, inline: bool) -> str:
    cleaned = re.sub(rf"\s+{re.escape(required_field)}\s*=\s*(?:yes|no)(?=\s*}})", "", block)
    cleaned = re.sub(rf"\n[ \t]*{re.escape(required_field)}\s*=\s*(?:yes|no)[ \t]*(?=\n)", "", cleaned)

    if inline or "\n" not in cleaned:
        closing = cleaned.rfind("}")
        return f"{cleaned[:closing].rstrip()} {required_field} = yes {cleaned[closing:]}"

    insertion = f"\n{indent}\t{required_field} = yes"
    closing = cleaned.rfind("}")
    return f"{cleaned[:closing].rstrip()}{insertion}\n{indent}}}"


def fix_text(text: str) -> tuple[str, bool]:
    replacements: list[tuple[int, int, str]] = []
    for operator, start, _open_brace, close_brace, indent, inline in iter_operator_blocks(text):
        required_field = CALL_CONTRACTS[operator]
        block = text[start : close_brace + 1]
        fixed_block = insert_contract_field(block, required_field, indent=indent, inline=inline)
        if fixed_block != block:
            replacements.append((start, close_brace + 1, fixed_block))

    if not replacements:
        return text, False

    fixed = text
    for start, end, replacement in reversed(replacements):
        fixed = fixed[:start] + replacement + fixed[end:]
    return fixed, True


def run(*, fix: bool) -> int:
    all_violations: list[Violation] = []
    changed_files: list[Path] = []
    for path in iter_scan_files():
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        if fix:
            fixed_text, changed = fix_text(text)
            if changed:
                path.write_text(fixed_text, encoding="utf-8")
                changed_files.append(path)
                text = fixed_text
        all_violations.extend(find_violations(path, text))

    if fix and changed_files:
        print("ModeU5 stock-operator contract fixer updated:")
        for path in changed_files:
            print(f"- {path.relative_to(ROOT)}")

    if all_violations:
        print("ModeU5 stock-operator contract validation failed:", file=sys.stderr)
        for violation in all_violations:
            rel = violation.path.relative_to(ROOT)
            print(
                f"- {rel}:{violation.line}: {violation.operator} must include "
                f"{violation.required_field} = yes or {violation.required_field} = no",
                file=sys.stderr,
            )
        return 1

    print("ModeU5 stock-operator contract validation passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="Insert missing explicit stock-operator contract fields")
    args = parser.parse_args()
    return run(fix=args.fix)


if __name__ == "__main__":
    sys.exit(main())

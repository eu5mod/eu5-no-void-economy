#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

BLOCK_TOKEN = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{|[{}]")
ASSIGNMENT = re.compile(
    r"^(\s*(local_merchant_capacity|merchant_capacity_from_building)\s*=\s*)"
    r"(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))(\s*(?:#.*)?)$"
)
FOREIGN_MARKER = re.compile(r"\bis_foreign\s*=\s*yes\b")


def format_decimal(value: float) -> str:
    if value == 0:
        return "0"
    rendered = f"{value:.10f}".rstrip("0").rstrip(".")
    return rendered if "." in rendered else f"{rendered}.0"


def code_without_comment(line: str) -> str:
    return line.split("#", 1)[0]


def transform_file(path: Path, multiplier: float) -> int:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    stack: list[dict[str, object]] = []
    changed = 0

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue

        code = code_without_comment(line)
        for token in BLOCK_TOKEN.finditer(code):
            key = token.group(1)
            if key is not None:
                stack.append({"key": key, "foreign": False})
            elif token.group(0) == "}" and stack:
                stack.pop()

        if stack and FOREIGN_MARKER.search(code):
            # is_foreign is a top-level building property in vanilla building definitions.
            stack[0]["foreign"] = True

        if not stack or not bool(stack[0]["foreign"]):
            continue

        match = ASSIGNMENT.match(line)
        if not match:
            continue

        old_value = float(match.group(3))
        new_value = format_decimal(old_value * multiplier)
        suffix = match.group(4)
        existing_comment = suffix.strip()
        trace = f"# FOREIGN BUILDING x{format_decimal(multiplier)}"
        if trace not in existing_comment:
            suffix = f" {trace}"
            if existing_comment:
                suffix += f"; {existing_comment.lstrip('# ').strip()}"
        lines[index] = f"{match.group(1)}{new_value}{suffix}"
        changed += 1

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Multiply trade capacity on generated foreign-building definitions after "
            "the global US-09 trade-capacity multiplier has been applied."
        )
    )
    parser.add_argument(
        "--building-dir",
        type=Path,
        default=Path("packages/cbp_economy_rebalance/in_game/common/building_types"),
    )
    parser.add_argument("--multiplier", type=float, default=4.0)
    args = parser.parse_args()

    if args.multiplier < 0:
        raise SystemExit("foreign-building trade-capacity multiplier must be non-negative")
    if not args.building_dir.is_dir():
        raise SystemExit(f"Missing generated building directory: {args.building_dir}")

    changed_files = 0
    changed_fields = 0
    for path in sorted(args.building_dir.glob("*.txt")):
        count = transform_file(path, args.multiplier)
        if count:
            changed_files += 1
            changed_fields += count
            print(f"Updated {path}: {count} foreign trade-capacity field(s).")

    if changed_fields == 0:
        raise SystemExit("No foreign-building trade-capacity fields were found.")

    print(
        f"Foreign-building trade capacity composed at x{format_decimal(args.multiplier)} "
        f"across {changed_fields} field(s) in {changed_files} file(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

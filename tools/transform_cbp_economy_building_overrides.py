#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


US09_FIELDS = {
    "output",
    "local_trades_per_burgher",
    "local_merchant_capacity",
    "merchant_capacity_from_building",
}

BLOCK_START = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{")
ASSIGNMENT = re.compile(
    r"^(\s*([A-Za-z0-9_]+)\s*=\s*)"
    r"(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))"
    r"(\s*(?:#.*)?)$"
)


@dataclass(frozen=True)
class MaintenanceRange:
    start: int
    end: int
    trade_building: bool


def format_decimal(value: float) -> str:
    if value == 0:
        return "0"
    formatted = f"{value:.10f}".rstrip("0").rstrip(".")
    return formatted if "." in formatted else f"{formatted}.0"


def code_without_comment(line: str) -> str:
    return line.split("#", 1)[0]


def find_maintenance_blocks(lines: list[str]) -> list[MaintenanceRange]:
    stack: list[dict[str, int | bool]] = []
    ranges: list[MaintenanceRange] = []

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue

        code = code_without_comment(line)
        start_match = BLOCK_START.match(code)
        if start_match:
            stack.append({"start": index, "maintenance": False, "trade": False})

        if re.search(r"\bcategory\s*=\s*trade_category\b", code):
            if stack:
                stack[-1]["trade"] = True

        if re.search(r"\bcategory\s*=\s*building_maintenance\b", code):
            if stack:
                stack[-1]["maintenance"] = True

        for _ in range(code.count("}")):
            if not stack:
                break
            block = stack.pop()
            if block["maintenance"]:
                trade_building = bool(block["trade"]) or any(bool(parent["trade"]) for parent in stack)
                ranges.append(
                    MaintenanceRange(
                        start=int(block["start"]),
                        end=index,
                        trade_building=trade_building,
                    )
                )

    return ranges


def find_maintenance_ranges(lines: list[str]) -> list[tuple[int, int]]:
    return [(block.start, block.end) for block in find_maintenance_blocks(lines)]


def line_is_in_ranges(index: int, ranges: list[tuple[int, int] | MaintenanceRange]) -> bool:
    return maintenance_range_for_line(index, ranges) is not None


def maintenance_range_for_line(
    index: int,
    ranges: list[tuple[int, int] | MaintenanceRange],
) -> MaintenanceRange | tuple[int, int] | None:
    for item in ranges:
        if isinstance(item, MaintenanceRange):
            if item.start <= index <= item.end:
                return item
        else:
            start, end = item
            if start <= index <= end:
                return item
    return None


def transform_lines(
    lines: list[str],
    *,
    source_basename: str,
    output_multiplier: float,
    maintenance_multiplier: float,
    trade_building_maintenance_multiplier: float,
    us07_trade_burghers_estate_power_multiplier: float,
    goods: set[str],
) -> list[str]:
    maintenance_ranges = find_maintenance_blocks(lines)
    transformed: list[str] = []

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            transformed.append(line)
            continue

        match = ASSIGNMENT.match(line)
        if not match:
            transformed.append(line)
            continue

        key = match.group(2)
        value = float(match.group(3))
        new_value: float | None = None

        maintenance_range = maintenance_range_for_line(index, maintenance_ranges)
        if maintenance_range is not None and key in goods:
            multiplier = maintenance_multiplier
            if isinstance(maintenance_range, MaintenanceRange) and maintenance_range.trade_building:
                multiplier = trade_building_maintenance_multiplier
            new_value = value * multiplier
            if value < 0:
                print(
                    f"WARNING: negative building maintenance value in {source_basename}: "
                    f"{key} = {match.group(3)}",
                    file=sys.stderr,
                )

        if key in US09_FIELDS:
            new_value = value * output_multiplier

        if source_basename == "trade_buildings.txt" and key == "local_burghers_estate_power":
            new_value = value * us07_trade_burghers_estate_power_multiplier

        if new_value is None:
            transformed.append(line)
        else:
            transformed.append(f"{match.group(1)}{format_decimal(new_value)}{match.group(4)}")

    return transformed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compose CBP Economy building static overrides from vanilla building_types."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--source-basename", required=True)
    parser.add_argument("--output-multiplier", required=True, type=float)
    parser.add_argument("--maintenance-multiplier", required=True, type=float)
    parser.add_argument("--trade-building-maintenance-multiplier", required=True, type=float)
    parser.add_argument("--us07-trade-burghers-estate-power-multiplier", required=True, type=float)
    parser.add_argument("--goods", nargs="+", required=True)
    args = parser.parse_args()

    if args.maintenance_multiplier < 0:
        raise SystemExit("maintenance multiplier must be non-negative")
    if args.trade_building_maintenance_multiplier < 0:
        raise SystemExit("trade building maintenance multiplier must be non-negative")

    text = args.source.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    transformed = transform_lines(
        lines,
        source_basename=args.source_basename,
        output_multiplier=args.output_multiplier,
        maintenance_multiplier=args.maintenance_multiplier,
        trade_building_maintenance_multiplier=args.trade_building_maintenance_multiplier,
        us07_trade_burghers_estate_power_multiplier=(
            args.us07_trade_burghers_estate_power_multiplier
        ),
        goods=set(args.goods),
    )
    sys.stdout.write("\n".join(transformed))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

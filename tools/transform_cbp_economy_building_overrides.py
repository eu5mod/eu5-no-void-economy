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

MARKETPLACE_CHAIN = {
    "marketplace",
    "merchants_quarters",
    "grand_marketplace",
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
    building_name: str | None


@dataclass(frozen=True)
class NamedBlock:
    name: str
    start: int
    end: int


def format_decimal(value: float) -> str:
    if value == 0:
        return "0"
    formatted = f"{value:.10f}".rstrip("0").rstrip(".")
    return formatted if "." in formatted else f"{formatted}.0"


def code_without_comment(line: str) -> str:
    return line.split("#", 1)[0]


def find_named_blocks(lines: list[str]) -> list[NamedBlock]:
    stack: list[tuple[str, int]] = []
    blocks: list[NamedBlock] = []
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        code = code_without_comment(line)
        start_match = BLOCK_START.match(code)
        if start_match:
            stack.append((start_match.group(1), index))
        for _ in range(code.count("}")):
            if not stack:
                break
            name, start = stack.pop()
            blocks.append(NamedBlock(name=name, start=start, end=index))
    return blocks


def find_maintenance_blocks(lines: list[str]) -> list[MaintenanceRange]:
    stack: list[dict[str, int | bool | str]] = []
    ranges: list[MaintenanceRange] = []
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        code = code_without_comment(line)
        start_match = BLOCK_START.match(code)
        if start_match:
            stack.append({"start": index, "name": start_match.group(1), "maintenance": False, "trade": False})
        if re.search(r"\bcategory\s*=\s*trade_category\b", code) and stack:
            stack[-1]["trade"] = True
        if re.search(r"\bcategory\s*=\s*building_maintenance\b", code) and stack:
            stack[-1]["maintenance"] = True
        for _ in range(code.count("}")):
            if not stack:
                break
            block = stack.pop()
            if block["maintenance"]:
                trade_building = bool(block["trade"]) or any(bool(parent["trade"]) for parent in stack)
                building_name = None
                for parent in reversed(stack):
                    parent_name = str(parent["name"])
                    if parent_name in MARKETPLACE_CHAIN:
                        building_name = parent_name
                        break
                ranges.append(MaintenanceRange(int(block["start"]), index, trade_building, building_name))
    return ranges


def find_maintenance_ranges(lines: list[str]) -> list[tuple[int, int]]:
    return [(block.start, block.end) for block in find_maintenance_blocks(lines)]


def line_is_in_ranges(index: int, ranges: list[tuple[int, int] | MaintenanceRange]) -> bool:
    return maintenance_range_for_line(index, ranges) is not None


def maintenance_range_for_line(index: int, ranges: list[tuple[int, int] | MaintenanceRange]) -> MaintenanceRange | tuple[int, int] | None:
    for item in ranges:
        if isinstance(item, MaintenanceRange):
            if item.start <= index <= item.end:
                return item
        else:
            start, end = item
            if start <= index <= end:
                return item
    return None


def align_marketplace_chain_maintenance(lines: list[str], goods: set[str]) -> list[str]:
    ranges = find_maintenance_blocks(lines)
    marketplace_range = next((item for item in ranges if item.building_name == "marketplace"), None)
    if marketplace_range is None:
        return lines
    baseline: dict[str, str] = {}
    for index in range(marketplace_range.start, marketplace_range.end + 1):
        match = ASSIGNMENT.match(lines[index])
        if match and match.group(2) in goods:
            baseline[match.group(2)] = match.group(3)
    if not baseline:
        return lines
    targets = [item for item in ranges if item.building_name in {"merchants_quarters", "grand_marketplace"}]
    transformed: list[str] = []
    for index, line in enumerate(lines):
        in_target = any(item.start <= index <= item.end for item in targets)
        if not in_target:
            transformed.append(line)
            continue
        match = ASSIGNMENT.match(line)
        if not match or match.group(2) not in goods:
            transformed.append(line)
            continue
        key = match.group(2)
        if key not in baseline:
            continue
        transformed.append(f"{match.group(1)}{baseline[key]}{match.group(4)}")
    return transformed


def disable_market_warehouse(lines: list[str], source_basename: str) -> list[str]:
    if source_basename != "market_buildings.txt":
        return lines
    warehouse = next((block for block in find_named_blocks(lines) if block.name == "market_warehouse"), None)
    if warehouse is None:
        return lines
    warehouse_lines = lines[warehouse.start : warehouse.end + 1]
    if any(re.match(r"^\s*country_potential\s*=\s*\{", line) for line in warehouse_lines):
        return lines
    insertion_index = next((index for index in range(warehouse.start + 1, warehouse.end) if re.match(r"^\s*location_potential\s*=\s*\{", lines[index])), warehouse.start + 1)
    block = ["\tcountry_potential = {", "\t\talways = no", "\t}", ""]
    return lines[:insertion_index] + block + lines[insertion_index:]


def transform_lines(lines: list[str], *, source_basename: str, output_multiplier: float, maintenance_multiplier: float, trade_building_maintenance_multiplier: float, us07_trade_burghers_estate_power_multiplier: float, goods: set[str]) -> list[str]:
    maintenance_ranges = find_maintenance_blocks(lines)
    transformed: list[str] = []
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
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
                print(f"WARNING: negative building maintenance value in {source_basename}: {key} = {match.group(3)}", file=sys.stderr)
        if key in US09_FIELDS:
            new_value = value * output_multiplier
        if source_basename == "trade_buildings.txt" and key == "local_burghers_estate_power":
            new_value = value * us07_trade_burghers_estate_power_multiplier
        transformed.append(line if new_value is None else f"{match.group(1)}{format_decimal(new_value)}{match.group(4)}")
    if source_basename == "trade_buildings.txt":
        transformed = align_marketplace_chain_maintenance(transformed, goods)
    return disable_market_warehouse(transformed, source_basename)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose CBP Economy building static overrides from vanilla building_types.")
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
    lines = args.source.read_text(encoding="utf-8-sig").splitlines()
    transformed = transform_lines(lines, source_basename=args.source_basename, output_multiplier=args.output_multiplier, maintenance_multiplier=args.maintenance_multiplier, trade_building_maintenance_multiplier=args.trade_building_maintenance_multiplier, us07_trade_burghers_estate_power_multiplier=args.us07_trade_burghers_estate_power_multiplier, goods=set(args.goods))
    sys.stdout.write("\n".join(transformed) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


US09_OUTPUT_FIELDS = {
    "output",
}
US09_TRADE_CAPACITY_FIELDS = {
    # "local_trades_per_burgher",
    "local_merchant_capacity",
    "merchant_capacity_from_building",
}
STOCKPILE_CAPACITY_FIELD = "maximum_stockpile_capacity"
COMMENTED_STOCKPILE_CAPACITY = re.compile(
    r"^\s*#\s*maximum_stockpile_capacity\s*=\s*"
    r"(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))"
    r"(?:\s+#.*)?$"
)
MARKETPLACE_BUILDINGS = {
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
    building_key: str | None = None


@dataclass(frozen=True)
class NamedBlockRange:
    key: str
    start: int
    end: int
    depth: int


def format_decimal(value: float) -> str:
    if value == 0:
        return "0"
    formatted = f"{value:.10f}".rstrip("0").rstrip(".")
    return formatted if "." in formatted else f"{formatted}.0"


def code_without_comment(line: str) -> str:
    return line.split("#", 1)[0]


def find_named_blocks(lines: list[str]) -> list[NamedBlockRange]:
    stack: list[tuple[str, int, int]] = []
    ranges: list[NamedBlockRange] = []

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        code = code_without_comment(line)
        start_match = BLOCK_START.match(code)
        if start_match:
            stack.append((start_match.group(1), index, len(stack)))
        for _ in range(code.count("}")):
            if not stack:
                break
            key, start, depth = stack.pop()
            ranges.append(NamedBlockRange(key=key, start=start, end=index, depth=depth))
    return ranges


def find_maintenance_blocks(lines: list[str]) -> list[MaintenanceRange]:
    stack: list[dict[str, int | bool | str]] = []
    ranges: list[MaintenanceRange] = []

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue

        code = code_without_comment(line)
        start_match = BLOCK_START.match(code)
        if start_match:
            stack.append(
                {
                    "start": index,
                    "maintenance": False,
                    "trade": False,
                    "key": start_match.group(1),
                }
            )

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
                trade_building = bool(block["trade"]) or any(
                    bool(parent["trade"]) for parent in stack
                )
                building_key = None
                for parent in reversed(stack):
                    candidate = str(parent["key"])
                    if candidate in MARKETPLACE_BUILDINGS:
                        building_key = candidate
                        break
                ranges.append(
                    MaintenanceRange(
                        start=int(block["start"]),
                        end=index,
                        trade_building=trade_building,
                        building_key=building_key,
                    )
                )

    return ranges


def find_maintenance_ranges(lines: list[str]) -> list[tuple[int, int]]:
    return [(block.start, block.end) for block in find_maintenance_blocks(lines)]


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


def line_is_in_ranges(index: int, ranges: list[tuple[int, int] | MaintenanceRange]) -> bool:
    return maintenance_range_for_line(index, ranges) is not None


def marketplace_base_maintenance(
    lines: list[str], maintenance_ranges: list[MaintenanceRange], goods: set[str]
) -> dict[str, float]:
    result: dict[str, float] = {}
    for index, line in enumerate(lines):
        maintenance_range = maintenance_range_for_line(index, maintenance_ranges)
        if not isinstance(maintenance_range, MaintenanceRange):
            continue
        if maintenance_range.building_key != "marketplace":
            continue
        match = ASSIGNMENT.match(line)
        if match and match.group(2) in goods:
            result[match.group(2)] = float(match.group(3))
    return result


def disable_market_warehouse(lines: list[str], source_basename: str) -> list[str]:
    if source_basename != "market_buildings.txt":
        return lines

    blocks = [
        block
        for block in find_named_blocks(lines)
        if block.key == "market_warehouse" and block.depth == 0
    ]
    if not blocks:
        return lines
    block = blocks[0]
    result = list(lines)

    child_blocks = [
        child
        for child in find_named_blocks(result)
        if block.start < child.start < block.end and child.depth == block.depth + 1
    ]

    country_potential_blocks = [
        child for child in child_blocks if child.key == "country_potential"
    ]
    if not country_potential_blocks:
        insertion = [
            "",
            "\tcountry_potential = {",
            "\t\talways = no",
            "\t}",
        ]
        result = result[: block.start + 1] + insertion + result[block.start + 1 :]
        block = [
            refreshed
            for refreshed in find_named_blocks(result)
            if refreshed.key == "market_warehouse" and refreshed.depth == 0
        ][0]

    child_blocks = [
        child
        for child in find_named_blocks(result)
        if block.start < child.start < block.end and child.depth == block.depth + 1
    ]
    location_potential_blocks = [
        child for child in child_blocks if child.key == "location_potential"
    ]
    replacement = [
        "\tlocation_potential = {",
        "\t\talways = no",
        "\t}",
    ]
    if location_potential_blocks:
        target = location_potential_blocks[0]
        result = result[: target.start] + replacement + result[target.end + 1 :]
    else:
        insert_after = block.start + 1
        country_potential_blocks = [
            child for child in child_blocks if child.key == "country_potential"
        ]
        if country_potential_blocks:
            insert_after = country_potential_blocks[0].end + 1
        result = result[:insert_after] + [""] + replacement + result[insert_after:]

    return result


def transform_lines(
    lines: list[str],
    *,
    source_basename: str,
    output_multiplier: float,
    trade_capacity_multiplier: float,
    maintenance_multiplier: float,
    trade_building_maintenance_multiplier: float,
    us07_trade_burghers_estate_power_multiplier: float,
    goods: set[str],
) -> list[str]:
    maintenance_ranges = find_maintenance_blocks(lines)
    marketplace_maintenance = marketplace_base_maintenance(lines, maintenance_ranges, goods)
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

        if key == STOCKPILE_CAPACITY_FIELD:
            indentation = line[: len(line) - len(line.lstrip())]
            transformed.append(
                f"{indentation}# {STOCKPILE_CAPACITY_FIELD} = {match.group(3)}{match.group(4)}"
            )
            continue

        maintenance_range = maintenance_range_for_line(index, maintenance_ranges)
        if maintenance_range is not None and key in goods:
            multiplier = maintenance_multiplier
            if isinstance(maintenance_range, MaintenanceRange) and maintenance_range.trade_building:
                multiplier = trade_building_maintenance_multiplier
            source_value = value
            if (
                isinstance(maintenance_range, MaintenanceRange)
                and maintenance_range.building_key in MARKETPLACE_BUILDINGS
            ):
                if key in marketplace_maintenance:
                    source_value = marketplace_maintenance[key]
                elif maintenance_range.building_key != "marketplace":
                    continue
            new_value = source_value * multiplier
            if value < 0:
                print(
                    f"WARNING: negative building maintenance value in {source_basename}: "
                    f"{key} = {match.group(3)}",
                    file=sys.stderr,
                )

        if key in US09_OUTPUT_FIELDS:
            new_value = value * output_multiplier

        if key in US09_TRADE_CAPACITY_FIELDS:
            new_value = value * trade_capacity_multiplier

        if source_basename == "trade_buildings.txt" and key == "local_burghers_estate_power":
            new_value = value * us07_trade_burghers_estate_power_multiplier

        rendered_value = match.group(3) if new_value is None else format_decimal(new_value)
        transformed.append(f"{match.group(1)}{rendered_value}{match.group(4)}")

    return disable_market_warehouse(transformed, source_basename)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compose CBP Economy building static overrides from vanilla building_types."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--source-basename", required=True)
    parser.add_argument("--output-multiplier", required=True, type=float)
    parser.add_argument("--trade-capacity-multiplier", required=True, type=float)
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
        trade_capacity_multiplier=args.trade_capacity_multiplier,
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

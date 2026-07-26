#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
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
MINTING_INCOME_FIELD = "minting_income_factor"
POLITICAL_MONTHLY_FIELDS = {
    "stability_investment",
    "monthly_legitimacy",
    "monthly_republican_tradition",
    "monthly_devotion",
    "monthly_horde_unity",
    "monthly_tribal_cohesion",
}
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
BLOCK_TOKEN = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{|[{}]")
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


@dataclass(frozen=True)
class BuildingChange:
    building: str
    field: str
    action: str
    old_value: str | None
    new_value: str | None


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
    depth = 0

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        code = code_without_comment(line)
        for token in BLOCK_TOKEN.finditer(code):
            key = token.group(1)
            if key is not None:
                stack.append((key, index, depth))
                depth += 1
                continue
            if token.group(0) == "{":
                depth += 1
                continue
            depth -= 1
            if depth < 0:
                raise ValueError(f"unexpected closing brace at line {index + 1}")
            if stack and stack[-1][2] == depth:
                block_key, start, block_depth = stack.pop()
                ranges.append(
                    NamedBlockRange(
                        key=block_key,
                        start=start,
                        end=index,
                        depth=block_depth,
                    )
                )
    if depth != 0 or stack:
        open_blocks = ", ".join(key for key, _, _ in stack)
        raise ValueError(f"unclosed block(s): {open_blocks}")
    return ranges


def top_level_buildings(lines: list[str]) -> list[NamedBlockRange]:
    buildings = sorted(
        (block for block in find_named_blocks(lines) if block.depth == 0),
        key=lambda block: block.start,
    )
    names = [building.key for building in buildings]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate top-level building(s): {', '.join(duplicates)}")
    return buildings


def building_for_line(index: int, buildings: list[NamedBlockRange]) -> str:
    for building in buildings:
        if building.start <= index <= building.end:
            return building.key
    raise ValueError(f"target assignment at line {index + 1} is outside a top-level building")


def find_maintenance_blocks(lines: list[str]) -> list[MaintenanceRange]:
    blocks = find_named_blocks(lines)
    ranges: list[MaintenanceRange] = []

    def innermost_block(index: int) -> NamedBlockRange | None:
        containing = [block for block in blocks if block.start <= index <= block.end]
        return max(containing, key=lambda block: block.depth, default=None)

    trade_blocks: set[tuple[int, int]] = set()
    maintenance_blocks: dict[tuple[int, int], NamedBlockRange] = {}
    for index, line in enumerate(lines):
        code = code_without_comment(line)
        containing = innermost_block(index)
        if containing is None:
            continue
        identity = (containing.start, containing.end)
        if re.search(r"\bcategory\s*=\s*trade_category\b", code):
            trade_blocks.add(identity)
        if re.search(r"\bcategory\s*=\s*building_maintenance\b", code):
            maintenance_blocks[identity] = containing

    for block in maintenance_blocks.values():
        ancestors = [
            candidate
            for candidate in blocks
            if candidate.start <= block.start and candidate.end >= block.end
        ]
        trade_building = any(
            (candidate.start, candidate.end) in trade_blocks for candidate in ancestors
        )
        building_key = next(
            (
                candidate.key
                for candidate in sorted(ancestors, key=lambda item: item.depth, reverse=True)
                if candidate.key in MARKETPLACE_BUILDINGS
            ),
            None,
        )
        ranges.append(
            MaintenanceRange(
                start=block.start,
                end=block.end,
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


def transform_lines_with_plan(
    lines: list[str],
    *,
    source_basename: str,
    output_multiplier: float,
    trade_capacity_multiplier: float,
    maintenance_multiplier: float,
    trade_building_maintenance_multiplier: float,
    us07_trade_burghers_estate_power_multiplier: float,
    minting_income_multiplier: float,
    goods: set[str],
    political_modifier_multiplier: float = 0.75,
    comment_stockpile_capacity: bool = True,
) -> tuple[list[str], list[BuildingChange], int]:
    buildings = top_level_buildings(lines)
    maintenance_ranges = find_maintenance_blocks(lines)
    marketplace_maintenance = marketplace_base_maintenance(lines, maintenance_ranges, goods)
    transformed: list[str] = []
    changes: list[BuildingChange] = []

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

        if key == STOCKPILE_CAPACITY_FIELD and comment_stockpile_capacity:
            indentation = line[: len(line) - len(line.lstrip())]
            existing_comment = match.group(4).strip().lstrip("# ").strip()
            trace = f"# VANILLA = {match.group(3)}; CBP = disabled"
            if existing_comment:
                trace += f"; {existing_comment}"
            new_line = (
                f"{indentation}# {STOCKPILE_CAPACITY_FIELD} = "
                f"{match.group(3)} {trace}"
            )
            transformed.append(
                new_line
            )
            changes.append(
                BuildingChange(
                    building=building_for_line(index, buildings),
                    field=STOCKPILE_CAPACITY_FIELD,
                    action="comment_out",
                    old_value=match.group(3),
                    new_value=None,
                )
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
                    changes.append(
                        BuildingChange(
                            building=building_for_line(index, buildings),
                            field=f"maintenance:{key}",
                            action="remove",
                            old_value=match.group(3),
                            new_value=None,
                        )
                    )
                    continue
            new_value = source_value * multiplier
            if value < 0:
                print(
                    f"WARNING: negative building maintenance value in {source_basename}: "
                    f"{key} = {match.group(3)}",
                    file=sys.stderr,
                )

        if key in US09_OUTPUT_FIELDS and output_multiplier != 1:
            new_value = value * output_multiplier

        if key in US09_TRADE_CAPACITY_FIELDS and trade_capacity_multiplier != 1:
            new_value = value * trade_capacity_multiplier

        if (
            source_basename == "trade_buildings.txt"
            and key == "local_burghers_estate_power"
            and us07_trade_burghers_estate_power_multiplier != 1
        ):
            new_value = value * us07_trade_burghers_estate_power_multiplier

        if key == MINTING_INCOME_FIELD and minting_income_multiplier != 1:
            new_value = value * minting_income_multiplier

        if key in POLITICAL_MONTHLY_FIELDS and political_modifier_multiplier != 1:
            new_value = value * political_modifier_multiplier

        rendered_value = match.group(3) if new_value is None else format_decimal(new_value)
        suffix = match.group(4)
        if rendered_value != match.group(3):
            trace = f"# VANILLA = {match.group(3)}"
            existing_comment = suffix.strip().lstrip("# ").strip()
            suffix = f" {trace}"
            if existing_comment:
                suffix += f"; {existing_comment}"
        transformed.append(f"{match.group(1)}{rendered_value}{suffix}")

        if rendered_value != match.group(3):
            field = key
            if maintenance_range is not None and key in goods:
                field = f"maintenance:{key}"
            changes.append(
                BuildingChange(
                    building=building_for_line(index, buildings),
                    field=field,
                    action="replace",
                    old_value=match.group(3),
                    new_value=rendered_value,
                )
            )

    warehouse_disabled = disable_market_warehouse(transformed, source_basename)
    if warehouse_disabled != transformed:
        changes.append(
            BuildingChange(
                building="market_warehouse",
                field="availability",
                action="disable",
                old_value="vanilla_potential",
                new_value="always_no",
            )
        )

    changes.sort(key=lambda change: (change.building, change.field, change.action))
    return warehouse_disabled, changes, len(buildings)


def transform_lines(
    lines: list[str],
    *,
    source_basename: str,
    output_multiplier: float,
    trade_capacity_multiplier: float,
    maintenance_multiplier: float,
    trade_building_maintenance_multiplier: float,
    us07_trade_burghers_estate_power_multiplier: float,
    minting_income_multiplier: float,
    goods: set[str],
    political_modifier_multiplier: float = 0.75,
    comment_stockpile_capacity: bool = True,
) -> list[str]:
    transformed, _, _ = transform_lines_with_plan(
        lines,
        source_basename=source_basename,
        output_multiplier=output_multiplier,
        trade_capacity_multiplier=trade_capacity_multiplier,
        maintenance_multiplier=maintenance_multiplier,
        trade_building_maintenance_multiplier=trade_building_maintenance_multiplier,
        us07_trade_burghers_estate_power_multiplier=(
            us07_trade_burghers_estate_power_multiplier
        ),
        minting_income_multiplier=minting_income_multiplier,
        goods=goods,
        political_modifier_multiplier=political_modifier_multiplier,
        comment_stockpile_capacity=comment_stockpile_capacity,
    )
    return transformed


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_generated_text(
    body: list[str],
    *,
    source_label: str,
    source_basename: str,
    output_multiplier: float,
    trade_capacity_multiplier: float,
    maintenance_multiplier: float,
    trade_building_maintenance_multiplier: float,
    us07_trade_burghers_estate_power_multiplier: float,
    minting_income_multiplier: float,
    political_modifier_multiplier: float,
) -> str:
    header = [
        "# Generated by tools/generate_us09_economy_overrides.sh.",
        "# Do not edit manually.",
        f"# Source: {source_label}",
        f"# Output multiplier: {format_decimal(output_multiplier)} "
        f"({format_decimal((output_multiplier - 1) * 100)}%)",
        f"# Trade capacity multiplier: {format_decimal(trade_capacity_multiplier)} "
        f"({format_decimal((trade_capacity_multiplier - 1) * 100)}%)",
        f"# Building maintenance multiplier: {format_decimal(maintenance_multiplier)}",
        "# Trade-building maintenance multiplier: "
        f"{format_decimal(trade_building_maintenance_multiplier)}",
        f"# Minting income multiplier: {format_decimal(minting_income_multiplier)}",
        "# Fixed monthly political modifier multiplier: "
        f"{format_decimal(political_modifier_multiplier)}",
        "",
    ]
    if source_basename == "trade_buildings.txt":
        header.extend(
            [
                "# US-07 composed trade-building estate-power multiplier: "
                f"{format_decimal(us07_trade_burghers_estate_power_multiplier)}",
                "",
            ]
        )
    return "\n".join(header + body) + "\n"


def build_manifest(
    *,
    source_file: Path,
    source_label: str,
    generated_text: str,
    changes: list[BuildingChange],
    building_count: int,
) -> dict[str, object]:
    changed_buildings: dict[str, list[dict[str, str | None]]] = {}
    for change in changes:
        changed_buildings.setdefault(change.building, []).append(
            {
                "field": change.field,
                "action": change.action,
                "old_value": change.old_value,
                "new_value": change.new_value,
            }
        )
    return {
        "schema_version": 1,
        "source_file": source_label,
        "source_sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
        "generated_sha256": sha256_text(generated_text),
        "changed_buildings": changed_buildings,
        "changed_building_count": len(changed_buildings),
        "unchanged_building_count": building_count - len(changed_buildings),
    }


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
    parser.add_argument("--minting-income-multiplier", required=True, type=float)
    parser.add_argument("--political-modifier-multiplier", type=float, default=0.75)
    parser.add_argument("--goods", nargs="+", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--source-label")
    args = parser.parse_args()

    if args.maintenance_multiplier < 0:
        raise SystemExit("maintenance multiplier must be non-negative")
    if args.trade_building_maintenance_multiplier < 0:
        raise SystemExit("trade building maintenance multiplier must be non-negative")
    if args.minting_income_multiplier < 0:
        raise SystemExit("minting income multiplier must be non-negative")

    text = args.source.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    try:
        transformed, changes, building_count = transform_lines_with_plan(
            lines,
            source_basename=args.source_basename,
            output_multiplier=args.output_multiplier,
            trade_capacity_multiplier=args.trade_capacity_multiplier,
            maintenance_multiplier=args.maintenance_multiplier,
            trade_building_maintenance_multiplier=args.trade_building_maintenance_multiplier,
            us07_trade_burghers_estate_power_multiplier=(
                args.us07_trade_burghers_estate_power_multiplier
            ),
            minting_income_multiplier=args.minting_income_multiplier,
            goods=set(args.goods),
            political_modifier_multiplier=args.political_modifier_multiplier,
        )
    except ValueError as error:
        raise SystemExit(f"Unsupported or ambiguous building structure in {args.source}: {error}")

    if not changes:
        if args.output:
            args.output.unlink(missing_ok=True)
        if args.manifest:
            args.manifest.unlink(missing_ok=True)
        return 3

    if bool(args.output) != bool(args.manifest):
        raise SystemExit("--output and --manifest must be provided together")

    if args.output:
        source_label = args.source_label or args.source.name
        generated_text = render_generated_text(
            transformed,
            source_label=source_label,
            source_basename=args.source_basename,
            output_multiplier=args.output_multiplier,
            trade_capacity_multiplier=args.trade_capacity_multiplier,
            maintenance_multiplier=args.maintenance_multiplier,
            trade_building_maintenance_multiplier=(
                args.trade_building_maintenance_multiplier
            ),
            us07_trade_burghers_estate_power_multiplier=(
                args.us07_trade_burghers_estate_power_multiplier
            ),
            minting_income_multiplier=args.minting_income_multiplier,
            political_modifier_multiplier=args.political_modifier_multiplier,
        )
        manifest = build_manifest(
            source_file=args.source,
            source_label=source_label,
            generated_text=generated_text,
            changes=changes,
            building_count=building_count,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(generated_text, encoding="utf-8")
        args.manifest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    else:
        sys.stdout.write("\n".join(transformed))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

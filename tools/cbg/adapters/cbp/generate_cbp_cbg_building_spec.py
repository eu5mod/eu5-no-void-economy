#!/usr/bin/env python3
"""Compile #188 building edge-case analysis into a focused CBG specification."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.transform_cbp_economy_building_overrides import (
    ASSIGNMENT,
    BuildingChange,
    find_named_blocks,
    format_decimal,
    render_generated_text,
    top_level_buildings,
    transform_lines_with_plan,
)

TRADE_CAPACITY_ASSIGNMENT = re.compile(
    r"^(\s*merchant_capacity_from_building\s*=\s*)"
    r"(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))(\s*(?:#.*)?)$"
)
FOREIGN_MARKER = re.compile(r"\bis_foreign\s*=\s*yes\b")
ADDITIVE_MODIFIER_FIELDS = {
    "local_burghers_estate_power",
    "local_merchant_capacity",
    "maximum_stockpile_capacity",
    "merchant_capacity_from_building",
    "minting_income_factor",
    "monthly_devotion",
    "monthly_horde_unity",
    "monthly_legitimacy",
    "monthly_republican_tradition",
    "monthly_tribal_cohesion",
}
MODIFIER_BLOCKS = {
    "capital_country_modifier",
    "capital_modifier",
    "foreign_country_modifier",
    "market_center_modifier",
    "modifier",
    "raw_modifier",
}


def load_goods(repo_root: Path) -> set[str]:
    text = (repo_root / "tools/cbp_goods.sh").read_text(encoding="utf-8")
    match = re.search(r"cbp_goods=\(\s*(.*?)\s*\)", text, re.DOTALL)
    if not match:
        raise ValueError("tools/cbp_goods.sh does not contain cbp_goods=(...)")
    body = "\n".join(line.split("#", 1)[0] for line in match.group(1).splitlines())
    goods = set(body.split())
    if not goods or any(not re.fullmatch(r"[a-z][a-z0-9_]*", good) for good in goods):
        raise ValueError("tools/cbp_goods.sh contains an invalid cbp_goods token")
    return goods


def apply_foreign_trade_capacity_multiplier(
    lines: list[str], multiplier: float
) -> tuple[list[str], set[str]]:
    """Compose a foreign-building multiplier after the global US-09 multiplier."""
    result = list(lines)
    changed_buildings: set[str] = set()
    for building in top_level_buildings(result):
        block = result[building.start : building.end + 1]
        if not any(FOREIGN_MARKER.search(line.split("#", 1)[0]) for line in block):
            continue
        for index in range(building.start, building.end + 1):
            match = TRADE_CAPACITY_ASSIGNMENT.match(result[index])
            if not match:
                continue
            old_value = float(match.group(2))
            new_value = format_decimal(old_value * multiplier)
            suffix = match.group(3)
            trace = f"# FOREIGN BUILDING x{format_decimal(multiplier)}"
            existing_comment = suffix.strip().lstrip("# ").strip()
            suffix = f" {trace}"
            if existing_comment:
                suffix += f"; {existing_comment}"
            result[index] = f"{match.group(1)}{new_value}{suffix}"
            changed_buildings.add(building.key)
    return result, changed_buildings


def header_for(
    source_basename: str,
    *,
    output_multiplier: float,
    trade_capacity_multiplier: float,
    foreign_trade_capacity_multiplier: float,
    maintenance_multiplier: float,
    trade_maintenance_multiplier: float,
    estate_power_multiplier: float,
    minting_multiplier: float,
    political_multiplier: float,
) -> list[str]:
    rendered = render_generated_text(
        [],
        source_label=f"<EU5_GAME_COMMON_DIR>/building_types/{source_basename}",
        source_basename=source_basename,
        output_multiplier=output_multiplier,
        trade_capacity_multiplier=trade_capacity_multiplier,
        maintenance_multiplier=maintenance_multiplier,
        trade_building_maintenance_multiplier=trade_maintenance_multiplier,
        us07_trade_burghers_estate_power_multiplier=estate_power_multiplier,
        minting_income_multiplier=minting_multiplier,
        political_modifier_multiplier=political_multiplier,
    )
    header = rendered.splitlines()[:-1]
    header.insert(
        5,
        "# Foreign-building merchant capacity multiplier: "
        f"{format_decimal(foreign_trade_capacity_multiplier)}",
    )
    return header


def requires_complete_replace(change: BuildingChange) -> bool:
    """Return whether INJECT cannot safely express this mutation."""
    return (
        change.action in {"disable", "remove"}
        or change.field == "output"
        or change.field.startswith("maintenance:")
    )


def modifier_assignments(
    building_lines: list[str],
) -> dict[tuple[str, str], tuple[float, str]]:
    """Read additive modifier fields as ``(modifier block, field)`` values."""
    blocks = find_named_blocks(building_lines)
    assignments: dict[tuple[str, str], tuple[float, str]] = {}
    for index, line in enumerate(building_lines):
        match = ASSIGNMENT.match(line)
        if match is None or match.group(2) not in ADDITIVE_MODIFIER_FIELDS:
            continue
        ancestors = sorted(
            (
                block
                for block in blocks
                if block.start <= index <= block.end
            ),
            key=lambda block: block.depth,
        )
        path = tuple(block.key for block in ancestors[1:])
        if len(path) != 1 or path[0] not in MODIFIER_BLOCKS:
            raise ValueError(
                f"{ancestors[0].key}.{match.group(2)} is not in one supported "
                "additive modifier block"
            )
        key = (path[0], match.group(2))
        if key in assignments:
            raise ValueError(
                f"{ancestors[0].key} contains duplicate modifier assignment "
                f"{path[0]}.{match.group(2)}"
            )
        assignments[key] = (float(match.group(3)), match.group(3))
    return assignments


def build_injection_fragment(
    source_lines: list[str],
    transformed_lines: list[str],
    building: str,
) -> list[str]:
    """Render a sparse INJECT fragment whose deltas produce the target values."""
    source_blocks = {block.key: block for block in top_level_buildings(source_lines)}
    transformed_blocks = {
        block.key: block for block in top_level_buildings(transformed_lines)
    }
    source = source_blocks[building]
    transformed = transformed_blocks[building]
    before = modifier_assignments(source_lines[source.start : source.end + 1])
    after = modifier_assignments(
        transformed_lines[transformed.start : transformed.end + 1]
    )

    deltas: dict[str, list[tuple[str, str]]] = {}
    for key, (old_value, old_literal) in before.items():
        modifier_block, field = key
        target = after.get(key)
        if target is None:
            if field != "maximum_stockpile_capacity":
                raise ValueError(
                    f"{building}.{modifier_block}.{field} disappeared from a "
                    "supposedly additive injection"
                )
            target_value = 0.0
            target_literal = "0"
        else:
            target_value, target_literal = target
        if target_value == old_value:
            continue
        delta = format_decimal(target_value - old_value)
        trace = f"# VANILLA = {old_literal}; TARGET = {target_literal}"
        deltas.setdefault(modifier_block, []).append(
            (field, f"{delta} {trace}")
        )

    if not deltas:
        raise ValueError(f"{building} was selected for INJECT but has no modifier delta")

    rendered = [f"{building} = {{"]
    for modifier_block in sorted(deltas):
        rendered.append(f"\t{modifier_block} = {{")
        for field, value in sorted(deltas[modifier_block]):
            rendered.append(f"\t\t{field} = {value}")
        rendered.append("\t}")
    rendered.append("}")
    return rendered


def build_spec(args: argparse.Namespace) -> dict[str, object]:
    common_dir = args.game_root / "in_game/common"
    goods = load_goods(args.repo_root)
    transformations: list[dict[str, object]] = []
    owned_outputs: list[str] = []
    for source in sorted((common_dir / "building_types").glob("*.txt")):
        if source.name == "readme.txt":
            continue
        source_lines = source.read_text(encoding="utf-8-sig").splitlines()
        transformed, changes, _ = transform_lines_with_plan(
            source_lines,
            source_basename=source.name,
            output_multiplier=args.output_multiplier,
            trade_capacity_multiplier=args.trade_capacity_multiplier,
            maintenance_multiplier=args.maintenance_multiplier,
            trade_building_maintenance_multiplier=args.trade_maintenance_multiplier,
            us07_trade_burghers_estate_power_multiplier=args.estate_power_multiplier,
            minting_income_multiplier=args.minting_multiplier,
            political_modifier_multiplier=args.political_multiplier,
            goods=goods,
        )
        transformed, foreign_changed = apply_foreign_trade_capacity_multiplier(
            transformed, args.foreign_trade_capacity_multiplier
        )
        changed_buildings = {change.building for change in changes} | foreign_changed
        if not changed_buildings:
            continue
        complete_replacements = {
            change.building for change in changes if requires_complete_replace(change)
        }
        injected_buildings = changed_buildings - complete_replacements
        blocks = {block.key: block for block in top_level_buildings(transformed)}
        relative = f"in_game/common/building_types/{source.name}"
        header = header_for(
            source.name,
            output_multiplier=args.output_multiplier,
            trade_capacity_multiplier=args.trade_capacity_multiplier,
            foreign_trade_capacity_multiplier=args.foreign_trade_capacity_multiplier,
            maintenance_multiplier=args.maintenance_multiplier,
            trade_maintenance_multiplier=args.trade_maintenance_multiplier,
            estate_power_multiplier=args.estate_power_multiplier,
            minting_multiplier=args.minting_multiplier,
            political_multiplier=args.political_multiplier,
        )
        for building in sorted(complete_replacements):
            block = blocks[building]
            transformations.append({
                "file": relative,
                "object": building,
                "field": "__object__",
                "operation": "replace_object",
                "value": transformed[block.start : block.end + 1],
                "provenance": "preserve",
                "render_mode": "replace_objects",
                "header": header,
            })
        if complete_replacements:
            owned_outputs.append(
                f"in_game/common/building_types/cbp_{source.name}"
            )
        for building in sorted(injected_buildings):
            transformations.append({
                "file": relative,
                "object": building,
                "field": "__object__",
                "operation": "replace_object",
                "value": build_injection_fragment(
                    source_lines,
                    transformed,
                    building,
                ),
                "provenance": "preserve",
                "render_mode": "inject_objects",
                "header": header,
            })
        if injected_buildings:
            owned_outputs.append(
                f"in_game/common/building_types/cbp_inject_{source.name}"
            )
    return {
        "schema_version": 1,
        "mod_id": "cbp-economy-rebalance-buildings",
        "business_rule": (
            "Apply configured production, global trade-capacity, foreign-building "
            "merchant-capacity, maintenance, minting, and stockpile policies to Vanilla buildings."
        ),
        "transformations": transformations,
        "scope_contract": {
            "owned_outputs": owned_outputs,
            "phase": "building-overrides",
            "packaging": (
                "CBP-prefixed complete REPLACE:<building> objects for structural "
                "mutations, plus sparse INJECT:<building> modifier deltas when "
                "Vanilla plus the generated delta equals the configured target"
            ),
            "edge_case_compiler": "transform_cbp_economy_building_overrides.transform_lines_with_plan",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-multiplier", type=float, required=True)
    parser.add_argument("--trade-capacity-multiplier", type=float, required=True)
    parser.add_argument("--foreign-trade-capacity-multiplier", type=float, default=2.0)
    parser.add_argument("--maintenance-multiplier", type=float, required=True)
    parser.add_argument("--trade-maintenance-multiplier", type=float, required=True)
    parser.add_argument("--estate-power-multiplier", type=float, default=0.5)
    parser.add_argument("--minting-multiplier", type=float, required=True)
    parser.add_argument("--political-multiplier", type=float, default=0.75)
    args = parser.parse_args()
    if args.foreign_trade_capacity_multiplier < 0:
        raise SystemExit("foreign trade-capacity multiplier must be non-negative")
    payload = build_spec(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    replace_count = sum(
        rule.get("render_mode") == "replace_objects"
        for rule in payload["transformations"]
    )
    inject_count = sum(
        rule.get("render_mode") == "inject_objects"
        for rule in payload["transformations"]
    )
    print(
        f"Generated {args.output} with {len(payload['transformations'])} "
        f"CBG building mutations ({replace_count} REPLACE, {inject_count} INJECT)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

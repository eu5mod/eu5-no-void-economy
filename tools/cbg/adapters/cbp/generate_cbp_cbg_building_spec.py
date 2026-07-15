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
    format_decimal,
    render_generated_text,
    top_level_buildings,
    transform_lines_with_plan,
)


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


def header_for(
    source_basename: str,
    *,
    output_multiplier: float,
    trade_capacity_multiplier: float,
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
    return rendered.splitlines()[:-1]


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
        if not changes:
            continue
        blocks = {block.key: block for block in top_level_buildings(transformed)}
        relative = f"in_game/common/building_types/{source.name}"
        header = header_for(
            source.name,
            output_multiplier=args.output_multiplier,
            trade_capacity_multiplier=args.trade_capacity_multiplier,
            maintenance_multiplier=args.maintenance_multiplier,
            trade_maintenance_multiplier=args.trade_maintenance_multiplier,
            estate_power_multiplier=args.estate_power_multiplier,
            minting_multiplier=args.minting_multiplier,
            political_multiplier=args.political_multiplier,
        )
        for building in sorted({change.building for change in changes}):
            block = blocks[building]
            transformations.append({
                "file": relative,
                "object": building,
                "field": "__object__",
                "operation": "replace_object",
                "value": transformed[block.start : block.end + 1],
                "provenance": "preserve",
                "render_mode": "verbatim_with_header",
                "header": header,
            })
        owned_outputs.append(relative)
    return {
        "schema_version": 1,
        "mod_id": "cbp-economy-rebalance-buildings",
        "transformations": transformations,
        "scope_contract": {
            "owned_outputs": owned_outputs,
            "phase": "building-overrides",
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
    parser.add_argument("--maintenance-multiplier", type=float, required=True)
    parser.add_argument("--trade-maintenance-multiplier", type=float, required=True)
    parser.add_argument("--estate-power-multiplier", type=float, default=0.5)
    parser.add_argument("--minting-multiplier", type=float, required=True)
    parser.add_argument("--political-multiplier", type=float, default=0.75)
    args = parser.parse_args()
    payload = build_spec(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Generated {args.output} with {len(payload['transformations'])} "
        "CBG building object replacements."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

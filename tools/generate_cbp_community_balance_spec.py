#!/usr/bin/env python3
"""Export the #188 CBP balance policies as one Community Balance Generator spec."""

from __future__ import annotations

import argparse
import json
import os
import re
from decimal import Decimal
from pathlib import Path

try:
    from tools.community_balance_generator import ASSIGNMENT, field_matches, scan_objects
    from tools.generate_political_reward_overrides import centralizable_script_values
except ModuleNotFoundError:  # Direct `python3 tools/...py` execution.
    from community_balance_generator import ASSIGNMENT, field_matches, scan_objects
    from generate_political_reward_overrides import centralizable_script_values


EVENT_FIELDS = (
    "add_stability",
    "add_legitimacy",
    "add_republican_tradition",
    "add_devotion",
    "add_horde_unity",
    "add_tribal_cohesion",
    "add_government_power",
)
MONTHLY_FIELDS = (
    "stability_investment",
    "monthly_legitimacy",
    "monthly_republican_tradition",
    "monthly_devotion",
    "monthly_horde_unity",
    "monthly_tribal_cohesion",
)
PROFIT_FIELDS = (
    "rural_profit_margin",
    "guild_profit_margin",
    "workshop_profit_margin",
    "manufactory_profit_margin",
    "mills_profit_margin",
)
MASTER_BUILDING_FIELDS = {
    "output",
    "local_merchant_capacity",
    "merchant_capacity_from_building",
    "maximum_stockpile_capacity",
    "minting_income_factor",
    "local_burghers_estate_power",
}
MARKETPLACE_BUILDINGS = {"marketplace", "merchants_quarters", "grand_marketplace"}


def env_number(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError as exc:
        raise ValueError(f"{name} must be numeric") from exc


def canonical_goods() -> tuple[str, ...]:
    text = Path("tools/cbp_goods.sh").read_text(encoding="utf-8")
    match = re.search(r"cbp_goods=\((?P<body>.*?)\n\)", text, re.DOTALL)
    if not match:
        raise ValueError("Cannot read canonical cbp_goods registry")
    return tuple(re.findall(r"[A-Za-z0-9_]+", match.group("body")))


def food_transformations(game_root: Path) -> list[dict[str, object]]:
    divisor = env_number("MODEU5_US177_FOOD_PRODUCTION_DIVISOR", 3)
    if divisor <= 0:
        raise ValueError("MODEU5_US177_FOOD_PRODUCTION_DIVISOR must be positive")
    result: list[dict[str, object]] = []
    for source in sorted((game_root / "in_game/common/goods").glob("*.txt")):
        lines = source.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        for obj in scan_objects(lines):
            if len(obj.path) != 1:
                continue
            matches = field_matches(lines, obj, "food")
            if len(matches) != 1:
                continue
            match = ASSIGNMENT.match(lines[matches[0]].rstrip("\r\n"))
            if not match:
                continue
            value = float(match.group("value"))
            if value <= 0:
                continue
            result.append({
                "file": source.relative_to(game_root).as_posix(),
                "object": obj.path[0],
                "field": "food",
                "operation": "replace",
                "value": f"{value / divisor:.10f}".rstrip("0").rstrip("."),
            })
    return result


def game_root_from_environment() -> Path:
    common = os.environ.get("EU5_GAME_COMMON_DIR")
    if not common:
        raise SystemExit("Set EU5_GAME_COMMON_DIR or pass --game-root")
    path = Path(common).expanduser().resolve()
    return path.parent.parent if path.name == "common" and path.parent.name == "in_game" else path


def marketplace_transformations(game_root: Path, factor: float) -> list[dict[str, object]]:
    """Unify upgraded marketplaces on Vanilla marketplace maintenance."""
    result: list[dict[str, object]] = []
    source = game_root / "in_game/common/building_types/trade_buildings.txt"
    lines = source.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    objects = scan_objects(lines)
    goods = set(canonical_goods())

    def maintenance(building: str):
        candidates = []
        for obj in objects:
            if not obj.path or obj.path[0] != building:
                continue
            values = {}
            for good in goods:
                matches = field_matches(lines, obj, good)
                if len(matches) == 1:
                    match = ASSIGNMENT.match(lines[matches[0]].rstrip("\r\n"))
                    if match:
                        values[good] = Decimal(match.group("value").strip())
            if values:
                candidates.append((obj, values))
        if len(candidates) != 1:
            raise ValueError(f"Expected one maintenance block for {building}; found {len(candidates)}")
        return candidates[0]

    _base_obj, base = maintenance("marketplace")
    relative = source.relative_to(game_root).as_posix()
    for building in sorted(MARKETPLACE_BUILDINGS):
        obj, current = maintenance(building)
        for good in sorted(current):
            entry: dict[str, object] = {
                "file": relative,
                "object": "/".join(obj.path),
                "field": good,
                "operation": "replace" if good in base else "remove",
            }
            if good in base:
                value = base[good] * Decimal(str(factor))
                entry["value"] = format(value.normalize(), "f")
            result.append(entry)
    return result


def bulk_rules(
    patterns: str | list[str],
    fields: tuple[str, ...],
    factor: float,
    excluded: tuple[str, ...] = (),
    excluded_files: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    return [
        {
            "file": patterns,
            "object": "**",
            "field": field,
            "operation": "multiply",
            "value": factor,
            "occurrences": "all",
            "on_missing": "skip",
            "exclude_values": list(excluded),
            "exclude_files": list(excluded_files),
        }
        for field in fields
    ]


def political_transformations(game_root: Path) -> list[dict[str, object]]:
    centralized_policy = centralizable_script_values(game_root)
    centralized = tuple(sorted(centralized_policy))
    result: list[dict[str, object]] = []
    # Master rules discover matching assignments directly in the current
    # Vanilla tree. The old generated-file manifest is not a file selector.
    result.extend(bulk_rules(
        "in_game/events/**/*.txt",
        EVENT_FIELDS,
        0.5,
        centralized,
        ("in_game/events/debug/**/*.txt",),
    ))
    result.extend(bulk_rules(
        "in_game/common/**/*.txt",
        EVENT_FIELDS,
        0.5,
        centralized,
        ("in_game/common/effect_localization/**/*.txt",),
    ))
    result.extend(bulk_rules("in_game/common/**/*.txt", MONTHLY_FIELDS, 0.75, centralized))
    result.extend(
        {
            "file": "main_menu/common/script_values/default_values.txt",
            "object": "",
            "field": name,
            "operation": "multiply",
            "value": factor,
        }
        for name, factor in sorted(
            (name, float(factor)) for name, factor in centralized_policy.items()
        )
    )
    return result


def build_spec(game_root: Path, package_root: Path) -> dict[str, object]:
    transformations: list[dict[str, object]] = []
    # Keep broad business policies first so the generated spec remains readable;
    # exact structural exceptions follow them.
    transformations.extend(political_transformations(game_root))
    output_multiplier = 1 + env_number("MODEU5_US09_BONUS_PERCENT", 5) / 100
    trade_capacity_multiplier = 1 + env_number(
        "MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT", 15
    ) / 100
    minting_multiplier = env_number("MODEU5_US177_MINTING_MULTIPLIER", 2)
    maintenance_multiplier = env_number("MODEU5_US08_BUILDING_MAINTENANCE_MULTIPLIER", 0.7)
    trade_maintenance_multiplier = env_number(
        "MODEU5_US08_TRADE_BUILDING_MAINTENANCE_MULTIPLIER", 0.5
    )
    transformations.extend(bulk_rules(
        "in_game/common/building_types/*.txt", ("output",), output_multiplier
    ))
    transformations.extend(food_transformations(game_root))
    food_price = env_number("MODEU5_US177_FOOD_PRICE", 0.3)
    transformations.append({
        "file": "loading_screen/common/defines/00_defines.txt",
        "object": "NMarket",
        "field": "FOOD_PRICE",
        "operation": "replace",
        "value": food_price,
    })
    rgo_gold = round(100 / output_multiplier, 2)
    for price in (
        "expand_rgo_mining", "expand_rgo_farming", "expand_rgo_hunting",
        "expand_rgo_gathering", "expand_rgo_forestry",
    ):
        transformations.append({
            "file": "in_game/common/prices/00_hardcoded.txt",
            "object": price,
            "field": "gold",
            "operation": "replace",
            "value": rgo_gold,
        })
    for pop_type, env_name in (
        ("burghers", "EXTRA_BURGHER_PROMOTION_SPEED"),
        ("laborers", "EXTRA_LABORER_PROMOTION_SPEED"),
    ):
        found = False
        for source in sorted((game_root / "in_game/common/pop_types").glob("*.txt")):
            lines = source.read_text(encoding="utf-8-sig").splitlines(keepends=True)
            objects = [obj for obj in scan_objects(lines) if obj.path == (pop_type,)]
            if objects and field_matches(lines, objects[0], "promotion_factor"):
                transformations.append({
                    "file": source.relative_to(game_root).as_posix(),
                    "object": pop_type,
                    "field": "promotion_factor",
                    "operation": "multiply",
                    "value": 1 + env_number(env_name, 10) / 100,
                })
                found = True
        if not found:
            raise ValueError(f"No promotion_factor found for {pop_type}")
    transformations.extend(bulk_rules(
        "in_game/common/building_types/*.txt",
        ("local_merchant_capacity", "merchant_capacity_from_building"),
        trade_capacity_multiplier,
    ))
    transformations.extend([
        {
            "file": "in_game/common/building_types/*.txt",
            "object": "**",
            "field": "maximum_stockpile_capacity",
            "operation": "comment_out",
            "occurrences": "all",
            "on_missing": "skip",
        },
        {
            "file": "in_game/common/building_types/trade_buildings.txt",
            "object": "**",
            "field": "local_burghers_estate_power",
            "operation": "multiply",
            "value": 0.5,
            "occurrences": "all",
            "on_missing": "skip",
        },
        {
            "file": "in_game/common/building_types/market_buildings.txt",
            "object": "market_warehouse",
            "field": "location_potential",
            "operation": "upsert_block",
            "value": {"always": "no"},
        },
        {
            "file": "in_game/common/building_types/market_buildings.txt",
            "object": "market_warehouse",
            "field": "country_potential",
            "operation": "upsert_block",
            "value": {"always": "no"},
            "position": {"after": "location_potential"},
        },
    ])
    transformations.extend(bulk_rules(
        "in_game/common/**/*.txt", ("minting_income_factor",), minting_multiplier
    ))
    transformations.extend(bulk_rules(
        "main_menu/common/static_modifiers/**/*.txt",
        ("minting_income_factor",),
        minting_multiplier,
    ))
    for good in canonical_goods():
        for factor, trade_condition in (
            (maintenance_multiplier, {"not_inside": [{"category": "trade_category"}]}),
            (trade_maintenance_multiplier, {"inside": [{"category": "trade_category"}]}),
        ):
            transformations.append({
                "file": "in_game/common/building_types/*.txt",
                "object": "**",
                "field": good,
                "operation": "multiply",
                "value": factor,
                "occurrences": "all",
                "on_missing": "skip",
                "where": {
                    "inside": [
                        {"category": "building_maintenance"},
                        *trade_condition.get("inside", []),
                    ],
                    "not_inside": trade_condition.get("not_inside", []),
                },
                "exclude_objects": sorted(MARKETPLACE_BUILDINGS),
            })
    transformations.extend(
        {
            "file": "main_menu/common/script_values/default_values.txt",
            "object": "",
            "field": field,
            "operation": "multiply",
            "value": 1.1,
        }
        for field in PROFIT_FIELDS
    )
    transformations.extend([
        {
            "file": "main_menu/common/static_modifiers/location.txt",
            "object": "expensive_food_in_location",
            "field": "local_population_growth",
            "operation": "replace",
            "value": 0,
        },
        {
            "file": "main_menu/common/static_modifiers/location.txt",
            "object": "cheap_food_in_location",
            "field": "local_population_growth",
            "operation": "replace",
            "value": 0.001,
        },
        {
            "file": "main_menu/common/static_modifiers/location.txt",
            "object": "market_center",
            "field": "maximum_stockpile_capacity",
            "operation": "replace",
            "value": 0,
        },
        {
            "file": "main_menu/common/static_modifiers/location.txt",
            "object": "surplus_jobs",
            "field": "local_migration_attraction",
            "operation": "replace",
            "value": 0.2,
        },
    ])
    transformations.extend(marketplace_transformations(game_root, trade_maintenance_multiplier))
    return {
        "schema_version": 1,
        "mod_id": "cbp-economy-rebalance",
        "transformations": transformations,
        "parity_contract": {
            "reference": "PR #188 generators",
            "known_structural_gaps": [],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--package-root", type=Path, default=Path("packages/cbp_economy_rebalance"))
    parser.add_argument("--output", type=Path, default=Path("tools/specs/cbp_pr188_balance.generated.json"))
    args = parser.parse_args()
    game_root = (args.game_root or game_root_from_environment()).resolve()
    package_root = args.package_root.resolve()
    try:
        spec = build_spec(game_root, package_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"CBP CBG spec generation failed: {exc}") from exc
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Generated {args.output} with {len(spec['transformations'])} transformations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

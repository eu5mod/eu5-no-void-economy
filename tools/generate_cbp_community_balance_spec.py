#!/usr/bin/env python3
"""Export the #188 CBP balance policies as one Community Balance Generator spec."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

try:
    from tools.community_balance_generator import ASSIGNMENT, field_matches, scan_objects
except ModuleNotFoundError:  # Direct `python3 tools/...py` execution.
    from community_balance_generator import ASSIGNMENT, field_matches, scan_objects


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


def game_root_from_environment() -> Path:
    common = os.environ.get("EU5_GAME_COMMON_DIR")
    if not common:
        raise SystemExit("Set EU5_GAME_COMMON_DIR or pass --game-root")
    path = Path(common).expanduser().resolve()
    return path.parent.parent if path.name == "common" and path.parent.name == "in_game" else path


def scalar_candidates(lines: list[str], building: str, field: str, old: str) -> list[tuple[str, ...]]:
    result: list[tuple[str, ...]] = []
    for obj in scan_objects(lines):
        if not obj.path or obj.path[0] != building:
            continue
        for index in field_matches(lines, obj, field):
            match = ASSIGNMENT.match(lines[index].rstrip("\r\n"))
            if match and match.group("value").strip() == old:
                result.append(obj.path)
    return result


def building_transformations(game_root: Path, package_root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    manifest_root = package_root / "cbp_generated/us09_buildings"
    for manifest_path in sorted(manifest_root.glob("*.json")):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        source = game_root / "in_game/common/building_types" / f"{manifest_path.stem}.txt"
        if not source.is_file():
            raise ValueError(f"Missing Vanilla building source: {source}")
        lines = source.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        relative = source.relative_to(game_root).as_posix()
        consumed: dict[tuple[str, str, str], int] = {}
        for building, changes in payload.get("changed_buildings", {}).items():
            for change in changes:
                action = change["action"]
                if action == "disable":
                    # Availability blocks need structured block upsert support;
                    # retained as an explicit gap in the parity report for now.
                    continue
                logical_field = change["field"]
                field = logical_field.split(":", 1)[1] if logical_field.startswith("maintenance:") else logical_field
                if field in MONTHLY_FIELDS:
                    # The generic monthly political rule below owns these
                    # fields across every common file, including buildings.
                    continue
                old = change.get("old_value")
                candidates = scalar_candidates(lines, building, field, old)
                identity = (building, field, str(old))
                candidate_index = consumed.get(identity, 0)
                if candidate_index >= len(candidates):
                    raise ValueError(
                        f"Cannot map {manifest_path.name}:{building}:{logical_field}: "
                        f"manifest occurrence {candidate_index + 1} exceeds the "
                        f"{len(candidates)} compatible Vanilla assignments with value {old}"
                    )
                consumed[identity] = candidate_index + 1
                candidate = candidates[candidate_index]
                operation = "comment_out" if action == "comment_out" else "remove" if action == "remove" else "replace"
                entry: dict[str, object] = {
                    "file": relative,
                    "object": "/".join(candidate),
                    "field": field,
                    "operation": operation,
                }
                if operation == "replace":
                    entry["value"] = change["new_value"]
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


def political_transformations(package_root: Path) -> list[dict[str, object]]:
    manifest_path = package_root / "cbp_generated/political_reward_overrides_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    centralized = tuple(sorted(payload.get("central_script_values", {})))
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
        for name, factor in sorted(payload.get("central_script_values", {}).items())
    )
    return result


def build_spec(game_root: Path, package_root: Path) -> dict[str, object]:
    transformations: list[dict[str, object]] = []
    # Keep broad business policies first so the generated spec remains readable;
    # exact structural exceptions follow them.
    transformations.extend(political_transformations(package_root))
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
    transformations.extend(building_transformations(game_root, package_root))
    return {
        "schema_version": 1,
        "mod_id": "cbp-economy-rebalance",
        "transformations": transformations,
        "parity_contract": {
            "reference": "PR #188 generators",
            "known_structural_gaps": ["market_warehouse availability block upsert"],
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

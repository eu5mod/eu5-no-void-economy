#!/usr/bin/env python3
"""Export CBG rules for Vanilla food-production overrides using US-177 discovery."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.cbg.community_balance_generator import display_path
from tools.generate_us177_food_goods_manifest import (
    build_manifest_payload,
    format_generated_decimal,
)


def game_root_from_environment() -> Path:
    common = os.environ.get("EU5_GAME_COMMON_DIR")
    if not common:
        raise SystemExit("Set EU5_GAME_COMMON_DIR or pass --game-root")
    path = Path(common).expanduser().resolve()
    return path.parent.parent if path.name == "common" and path.parent.name == "in_game" else path


def build_spec(game_root: Path, divisor: Decimal) -> dict[str, object]:
    payload = build_manifest_payload(game_root)
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry in payload["food_goods"]:
        grouped[str(entry["source_path"])].append(entry)
    transformations = []
    for source_path, entries in sorted(grouped.items()):
        for entry in sorted(entries, key=lambda item: str(item["good"])):
            transformations.append({
                "file": source_path,
                "object": str(entry["good"]),
                "field": "food",
                "operation": "replace",
                "value": format_generated_decimal(Decimal(str(entry["food_value"])) / divisor),
                "provenance": "preserve",
            })
    return {
        "schema_version": 1,
        "mod_id": "cbp-economy-rebalance-food-production",
        "business_rule": "Divide Vanilla food production by the configured divisor while preserving each food-good definition.",
        "transformations": transformations,
        "scope_contract": {
            "owned_outputs": sorted(grouped),
            "phase": "food-production",
            "discovery": "generate_us177_food_goods_manifest.build_manifest_payload",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--divisor", type=Decimal, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.divisor <= 0:
        raise SystemExit("--divisor must be positive")
    game_root = (args.game_root or game_root_from_environment()).resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_spec(game_root, args.divisor), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {display_path(args.output)} with US-177 food CBG policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Export the focused CBG policy for CBP's central default script values."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.generate_political_reward_overrides import (
    PROFIT_MARGIN_FACTOR,
    PROFIT_MARGIN_FIELDS,
    centralizable_script_values,
)


TARGET = "main_menu/common/script_values/default_values.txt"


def game_root_from_environment() -> Path:
    common = os.environ.get("EU5_GAME_COMMON_DIR")
    if not common:
        raise SystemExit("Set EU5_GAME_COMMON_DIR or pass --game-root")
    path = Path(common).expanduser().resolve()
    return path.parent.parent if path.name == "common" and path.parent.name == "in_game" else path


def build_spec(game_root: Path) -> dict[str, object]:
    policies = centralizable_script_values(game_root)
    factors = {
        **policies,
        **{name: PROFIT_MARGIN_FACTOR for name in PROFIT_MARGIN_FIELDS},
    }
    return {
        "schema_version": 1,
        "mod_id": "cbp-economy-rebalance-default-values",
        "business_rule": "Scale centralized political intensity values and production profit-margin targets from Vanilla.",
        "transformations": [
            {
                "file": TARGET,
                "object": "",
                "field": name,
                "operation": "multiply",
                "value": float(factor),
                "provenance": "vanilla",
            }
            for name, factor in sorted(factors.items())
        ],
        "scope_contract": {
            "owned_outputs": [TARGET],
            "phase": "default-values-only",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    game_root = (args.game_root or game_root_from_environment()).resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_spec(game_root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {args.output} with default_values.txt-only CBG policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

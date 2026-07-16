#!/usr/bin/env python3
"""Validate the lean market-only US-17/US-20 package boundary."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages/cbp_trade_logistics_standalone"


def main() -> int:
    failures: list[str] = []
    required = [
        "descriptor.mod",
        ".metadata/metadata.json",
        "in_game/common/on_action/cbp_trade_logistics_on_actions.txt",
        "in_game/common/script_values/cbp_trade_logistics_values.txt",
        "in_game/common/scripted_effects/cbp_trade_logistics_effects.txt",
    ]
    for relative in required:
        if not (PACKAGE / relative).is_file():
            failures.append(f"missing {relative}")

    texts = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in PACKAGE.rglob("*.txt")
    )
    required_fragments = [
        "monthly_country_pulse",
        "every_trade = {",
        "trade_maintenance",
        "modifier:merchant_maintenance_efficiency",
        "add_gold = scope:cbp_trade_logistics_money_delta",
        "add_goods_supply = {",
    ]
    for fragment in required_fragments:
        if fragment not in texts:
            failures.append(f"missing runtime contract: {fragment}")

    forbidden = [
        "variable_map(cmm",
        "has_variable_map = cmm",
        "country_market_good_stock",
        "cbp_add_stock",
        "cbp_remove_stock",
        "cbp_transfer_stock",
        "promoted_market",
    ]
    for fragment in forbidden:
        if fragment in texts:
            failures.append(f"standalone boundary violation: {fragment}")

    if failures:
        print("CBP US-17/US-20 standalone validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("CBP US-17/US-20 standalone market-only validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

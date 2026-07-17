#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFINES = (
    ROOT
    / "packages"
    / "cbp_economy_rebalance"
    / "loading_screen"
    / "common"
    / "defines"
    / "cbp_market_resource_balance_defines.txt"
)


def main() -> int:
    failures: list[str] = []
    if not DEFINES.is_file():
        failures.append(f"Missing market-price speed override: {DEFINES.relative_to(ROOT)}")
    else:
        text = DEFINES.read_text(encoding="utf-8-sig")
        assignments = re.findall(
            r"^\s*MONTHLY_PRICE_CHANGE\s*=\s*([^\s#]+)", text, re.MULTILINE
        )
        if assignments != ["0.10"]:
            failures.append(
                "NMarket.MONTHLY_PRICE_CHANGE must be set exactly once to 0.10; "
                f"found {assignments}"
            )
        if "VANILLA = 0.05" not in text:
            failures.append("Market-price speed override must preserve the Vanilla 0.05 reference")
        if re.search(r"^\s*FOOD_PRICE_IMPACT_ON_PRICES\s*=", text, re.MULTILINE):
            failures.append(
                "Market and resource balance override must not modify "
                "FOOD_PRICE_IMPACT_ON_PRICES"
            )

    if failures:
        print("CBP market-price speed validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("CBP market prices close 10% of the target-price gap per month (Vanilla: 5%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

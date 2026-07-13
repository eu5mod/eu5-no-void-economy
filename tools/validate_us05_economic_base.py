#!/usr/bin/env python3
"""Validate the US-05 slider-cost reconciliation contract."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
VALUE_FILE = ROOT / "in_game/common/script_values/modeu5_us05_economic_base_values.txt"


def main() -> int:
    errors: list[str] = []
    if not VALUE_FILE.is_file():
        print(f"Missing {VALUE_FILE.relative_to(ROOT)}")
        return 1

    text = VALUE_FILE.read_text(encoding="utf-8")

    required = {
        r"(?m)^modeu5_slider_cost_target_base\s*=\s*\{": "missing target base",
        r"(?m)^modeu5_slider_cost_vanilla_base\s*=\s*\{": "missing vanilla comparison base",
        r"(?m)^modeu5_slider_cost_reconciliation_modifier\s*=\s*\{": "missing reconciliation modifier",
        r"value\s*=\s*var:cbp_country_wealth_endpoint": "wealth endpoint is not used",
        r"value\s*=\s*tax_base": "Tax Base denominator component is not used",
        r"add\s*=\s*monthly_trade_income": "monthly_trade_income is not included",
        r"divide\s*=\s*modeu5_slider_cost_vanilla_base": "target is not divided by vanilla base",
        r"subtract\s*=\s*1": "ratio is not converted to an additive modifier",
        r"modeu5_slider_cost_vanilla_base\s*>\s*0": "zero-denominator guard is missing",
        r"(?m)^modeu5_slider_cost_base_wealth_component\s*=\s*\{": "missing wealth diagnostic component",
        r"(?m)^modeu5_slider_cost_base_tax_component\s*=\s*\{": "missing Tax Base diagnostic component",
        r"(?m)^modeu5_slider_cost_base_trade_income_component\s*=\s*\{": "missing trade-income diagnostic component",
    }
    for pattern, message in required.items():
        if re.search(pattern, text) is None:
            errors.append(message)

    forbidden_tokens = (
        "add_gold",
        "add_stability",
        "add_legitimacy",
        "change_stability",
        "change_legitimacy",
    )
    lowered = text.lower()
    for token in forbidden_tokens:
        if token in lowered:
            errors.append(f"forbidden outcome/gold reconciliation token present: {token}")

    if errors:
        print("US-05 slider reconciliation contract failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("US-05 slider reconciliation contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

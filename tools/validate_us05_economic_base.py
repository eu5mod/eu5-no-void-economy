#!/usr/bin/env python3
"""Validate the US-05 slider-cost reconciliation contract."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
VALUE_FILE = ROOT / "in_game/common/script_values/modeu5_us05_economic_base_values.txt"
EFFECT_FILE = ROOT / "in_game/common/scripted_effects/modeu5_us05_economic_base_effects.txt"
ON_ACTION_FILE = ROOT / "in_game/common/on_action/modeu5_stock_on_actions.txt"
MODIFIER_FILE = ROOT / "main_menu/common/static_modifiers/modeu5_us05_slider_cost_modifiers.txt"


def read_required(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def require(pattern: str, text: str, message: str, errors: list[str]) -> None:
    if re.search(pattern, text, flags=re.MULTILINE) is None:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    values = read_required(VALUE_FILE, errors)
    effects = read_required(EFFECT_FILE, errors)
    on_actions = read_required(ON_ACTION_FILE, errors)
    modifiers = read_required(MODIFIER_FILE, errors)

    value_contract = {
        r"^modeu5_slider_cost_target_base\s*=\s*\{": "missing target base",
        r"^modeu5_slider_cost_vanilla_base\s*=\s*\{": "missing vanilla comparison base",
        r"^modeu5_slider_cost_reconciliation_modifier\s*=\s*\{": "missing reconciliation modifier",
        r"value\s*=\s*var:cbp_country_wealth_endpoint": "wealth endpoint is not used",
        r"value\s*=\s*tax_base": "Tax Base denominator component is not used",
        r"add\s*=\s*monthly_trade_income": "monthly_trade_income is not included",
        r"divide\s*=\s*modeu5_slider_cost_vanilla_base": "target is not divided by vanilla base",
        r"subtract\s*=\s*1": "ratio is not converted to an additive modifier",
        r"modeu5_slider_cost_vanilla_base\s*>\s*0": "zero-denominator guard is missing",
    }
    for pattern, message in value_contract.items():
        require(pattern, values, message, errors)

    modifier_contract = {
        r"^modeu5_us05_economic_base_slider_cost_reconciliation\s*=\s*\{": "missing static reconciliation modifier",
        r"court_spending_cost_modifier\s*=\s*1": "court spending modifier is not implemented",
        r"diplomatic_upkeep_modifier\s*=\s*1": "diplomatic upkeep modifier is not implemented",
    }
    for pattern, message in modifier_contract.items():
        require(pattern, modifiers, message, errors)

    effect_contract = {
        r"^modeu5_us05_refresh_safe_slider_cost_reconciliation\s*=\s*\{": "missing monthly refresh effect",
        r"remove_country_modifier\s*=\s*modeu5_us05_economic_base_slider_cost_reconciliation": "old reconciliation modifier is not removed",
        r"modifier\s*=\s*modeu5_us05_economic_base_slider_cost_reconciliation": "reconciliation modifier is not added",
        r"size\s*=\s*modeu5_slider_cost_reconciliation_modifier": "runtime modifier does not use the calculated ratio",
        r"mode\s*=\s*replace": "runtime modifier is not replaced deterministically",
    }
    for pattern, message in effect_contract.items():
        require(pattern, effects, message, errors)

    require(
        r"modeu5_core04_refresh_current_country_location_market_memory\s*=\s*yes[\s\S]*?"
        r"modeu5_us05_refresh_safe_slider_cost_reconciliation\s*=\s*yes",
        on_actions,
        "US-05 refresh must run after the monthly wealth refresh",
        errors,
    )

    combined = "\n".join((values, effects, modifiers))
    forbidden_tokens = (
        "add_gold",
        "add_stability",
        "add_legitimacy",
        "change_stability",
        "change_legitimacy",
    )
    lowered = combined.lower()
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

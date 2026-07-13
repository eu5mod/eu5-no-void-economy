#!/usr/bin/env python3
"""Validate the US-05 per-expense slider reconciliation contract."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
VALUE_FILE = ROOT / "in_game/common/script_values/modeu5_us05_economic_base_values.txt"
EFFECT_FILE = ROOT / "in_game/common/scripted_effects/modeu5_us05_economic_base_effects.txt"
ON_ACTION_FILE = ROOT / "in_game/common/on_action/modeu5_stock_on_actions.txt"
MODIFIER_FILE = ROOT / "main_menu/common/static_modifiers/modeu5_us05_slider_cost_modifiers.txt"
COVERAGE_FILE = ROOT / "docs/technical/US05_SLIDER_MODIFIER_COVERAGE.md"


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
    coverage = read_required(COVERAGE_FILE, errors)

    value_contract = {
        r"^modeu5_us05_vanilla_economic_base\s*=\s*\{": "missing vanilla denominator",
        r"^modeu5_us05_wealth_plus_trade_income_base\s*=\s*\{": "missing shared Wealth + Trade Income base",
        r"^modeu5_us05_court_target_base\s*=\s*\{": "missing Court target base",
        r"^modeu5_us05_court_cost_modifier\s*=\s*\{": "missing Court reconciliation modifier",
        r"^modeu5_us05_diplomatic_target_base\s*=\s*\{": "missing Diplomatic target base",
        r"^modeu5_us05_diplomatic_cost_modifier\s*=\s*\{": "missing Diplomatic reconciliation modifier",
        r"value\s*=\s*var:cbp_country_wealth_endpoint": "wealth endpoint is not used",
        r"value\s*=\s*tax_base": "Tax Base denominator component is not used",
        r"add\s*=\s*monthly_trade_income": "monthly_trade_income is not included",
        r"divide\s*=\s*modeu5_us05_vanilla_economic_base": "expense modifier does not divide by the vanilla denominator",
        r"subtract\s*=\s*1": "ratio is not converted to an additive modifier",
        r"modeu5_us05_vanilla_economic_base\s*>\s*0": "zero-denominator guard is missing",
    }
    for pattern, message in value_contract.items():
        require(pattern, values, message, errors)

    modifier_contract = {
        r"^modeu5_us05_court_cost_reconciliation\s*=\s*\{": "missing Court static modifier",
        r"^modeu5_us05_diplomatic_cost_reconciliation\s*=\s*\{": "missing Diplomatic static modifier",
        r"court_spending_cost_modifier\s*=\s*1": "Court spending modifier is not implemented",
        r"diplomatic_upkeep_modifier\s*=\s*1": "Diplomatic upkeep modifier is not implemented",
    }
    for pattern, message in modifier_contract.items():
        require(pattern, modifiers, message, errors)

    effect_contract = {
        r"^modeu5_us05_refresh_safe_slider_cost_reconciliation\s*=\s*\{": "missing monthly refresh effect",
        r"remove_country_modifier\s*=\s*modeu5_us05_court_cost_reconciliation": "old Court modifier is not removed",
        r"remove_country_modifier\s*=\s*modeu5_us05_diplomatic_cost_reconciliation": "old Diplomatic modifier is not removed",
        r"modifier\s*=\s*modeu5_us05_court_cost_reconciliation": "Court modifier is not added",
        r"modifier\s*=\s*modeu5_us05_diplomatic_cost_reconciliation": "Diplomatic modifier is not added",
        r"size\s*=\s*modeu5_us05_court_cost_modifier": "Court runtime modifier does not use its own ratio",
        r"size\s*=\s*modeu5_us05_diplomatic_cost_modifier": "Diplomatic runtime modifier does not use its own ratio",
        r"mode\s*=\s*replace": "runtime modifiers are not replaced deterministically",
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

    for required_coverage in (
        "stability_cost",
        "diplomatic_spending_cost",
        "Culture investment",
        "Prestige investment",
        "Military spending",
        "Fort spending",
        "Subsidies",
        "Minting",
        "Food spending",
        "population / 1000",
    ):
        if required_coverage not in coverage:
            errors.append(f"coverage document is missing: {required_coverage}")

    forbidden_shared_runtime = (
        "modeu5_us05_economic_base_slider_cost_reconciliation",
        "modeu5_slider_cost_reconciliation_modifier",
    )
    for token in forbidden_shared_runtime:
        if token in "\n".join((effects, modifiers)):
            errors.append(f"legacy shared runtime modifier remains present: {token}")

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
        print("US-05 per-expense reconciliation contract failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("US-05 per-expense reconciliation contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

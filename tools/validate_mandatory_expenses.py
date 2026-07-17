#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cbp_economy_rebalance"


def require_assignment(path: Path, key: str, expected: str, failures: list[str]) -> None:
    text = path.read_text(encoding="utf-8-sig")
    matches = re.findall(rf"^\s*{re.escape(key)}\s*=\s*([^\s#]+)", text, re.MULTILINE)
    if matches != [expected]:
        relative = path.relative_to(ROOT)
        failures.append(f"{relative} must set {key} exactly once to {expected}; found {matches}")


def main() -> int:
    defines = PACKAGE / "loading_screen/common/defines/cbp_mandatory_expenses_defines.txt"
    modifiers = PACKAGE / "main_menu/common/static_modifiers/cbp_mandatory_expenses.txt"
    auto_modifiers = PACKAGE / "in_game/common/auto_modifiers/cbp_mandatory_stability_expense_auto_modifiers.txt"
    effects = PACKAGE / "in_game/common/scripted_effects/cbp_mandatory_expense_effects.txt"
    on_actions = PACKAGE / "in_game/common/on_action/cbp_economy_package_on_actions.txt"
    localization = PACKAGE / "main_menu/localization/english/cbp_mandatory_expenses_l_english.yml"
    paths = (defines, modifiers, auto_modifiers, effects, on_actions, localization)
    failures = [f"Missing mandatory-expense file: {path.relative_to(ROOT)}" for path in paths if not path.is_file()]

    if failures:
        print("CBP mandatory-expense validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    require_assignment(defines, "STABILITY_INVEST_FACTOR", "1", failures)
    require_assignment(defines, "GOV_POWER_INVEST_FACTOR", "3.0", failures)
    require_assignment(modifiers, "stability_investment", "-0.5", failures)
    for government_power in (
        "monthly_legitimacy",
        "monthly_republican_tradition",
        "monthly_devotion",
        "monthly_horde_unity",
        "monthly_tribal_cohesion",
    ):
        require_assignment(modifiers, government_power, "-1", failures)

    modifier_text = modifiers.read_text(encoding="utf-8-sig")
    if "stability_decay" in modifier_text:
        failures.append("Mandatory Stability expense must not use percentage-based stability_decay")

    auto_modifier_text = auto_modifiers.read_text(encoding="utf-8-sig")
    required_offset_fragments = (
        "cbp_positive_stability_expense_offset = {",
        "stability > 0",
        "value = stability",
        "multiply = 0.01",
        "stability_investment = 1",
    )
    for fragment in required_offset_fragments:
        if fragment not in auto_modifier_text:
            failures.append(f"Positive-Stability expense offset must contain: {fragment}")
    if "stability_decay" in auto_modifier_text:
        failures.append("Positive-Stability expense offset must not override Vanilla stability_decay")

    effects_text = effects.read_text(encoding="utf-8-sig")
    for modifier in (
        "cbp_mandatory_stability_expense",
        "cbp_mandatory_government_power_expense",
    ):
        if f"has_country_modifier = {modifier}" not in effects_text:
            failures.append(f"Monthly repair for {modifier} must be idempotently guarded")
    if effects_text.count("days = -1") != 2 or effects_text.count("mode = replace") != 2:
        failures.append("Both mandatory expenses must be permanent replace-mode modifiers")

    on_action_text = on_actions.read_text(encoding="utf-8-sig")
    if on_action_text.count("cbp_apply_mandatory_expenses_to_all_countries = yes") != 1:
        failures.append("Package initialization must apply both expenses to all countries exactly once")
    if on_action_text.count("cbp_ensure_mandatory_stability_expense = yes") != 1:
        failures.append("Monthly country pulse must repair Stability expense for new countries")
    if on_action_text.count("cbp_ensure_mandatory_government_power_expense = yes") != 1:
        failures.append("Monthly country pulse must repair government-power expense for new countries")

    localization_text = localization.read_text(encoding="utf-8-sig")
    if "STATIC_MODIFIER_NAME_cbp_mandatory_stability_expense" not in localization_text:
        failures.append("Mandatory Stability expense modifier name is not localized")
    if "STATIC_MODIFIER_NAME_cbp_mandatory_government_power_expense" not in localization_text:
        failures.append("Mandatory government-power expense modifier name is not localized")
    if "AUTO_MODIFIER_NAME_cbp_positive_stability_expense_offset" not in localization_text:
        failures.append("Positive-Stability expense offset auto-modifier name is not localized")
    if "50%" not in localization_text:
        failures.append("Modifier description must explain the 50% vanilla-neutral slider position")
    if "66.7%" not in localization_text:
        failures.append("Government-power description must explain the 66.7% maintenance point")

    if failures:
        print("CBP mandatory-expense validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("CBP mandatory Stability and government-power expense validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

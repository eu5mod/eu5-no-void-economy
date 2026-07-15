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
    effects = PACKAGE / "in_game/common/scripted_effects/cbp_mandatory_expense_effects.txt"
    on_actions = PACKAGE / "in_game/common/on_action/cbp_economy_package_on_actions.txt"
    localization = PACKAGE / "main_menu/localization/english/cbp_mandatory_expenses_l_english.yml"
    paths = (defines, modifiers, effects, on_actions, localization)
    failures = [f"Missing mandatory-expense file: {path.relative_to(ROOT)}" for path in paths if not path.is_file()]

    if failures:
        print("CBP mandatory-expense validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    require_assignment(defines, "STABILITY_INVEST_FACTOR", "1", failures)
    require_assignment(modifiers, "stability_investment", "-0.5", failures)

    modifier_text = modifiers.read_text(encoding="utf-8-sig")
    if "stability_decay" in modifier_text:
        failures.append("Mandatory Stability expense must not use percentage-based stability_decay")

    effects_text = effects.read_text(encoding="utf-8-sig")
    if "has_country_modifier = cbp_mandatory_stability_expense" not in effects_text:
        failures.append("Monthly repair must be idempotently guarded by has_country_modifier")
    if "days = -1" not in effects_text or "mode = replace" not in effects_text:
        failures.append("Mandatory Stability expense must be a permanent replace-mode modifier")

    on_action_text = on_actions.read_text(encoding="utf-8-sig")
    if on_action_text.count("cbp_apply_mandatory_stability_expense_to_all_countries = yes") != 1:
        failures.append("Package initialization must apply the expense to all countries exactly once")
    if on_action_text.count("cbp_ensure_mandatory_stability_expense = yes") != 1:
        failures.append("Monthly country pulse must repair the expense for newly created countries")

    localization_text = localization.read_text(encoding="utf-8-sig")
    if "STATIC_MODIFIER_NAME_cbp_mandatory_stability_expense" not in localization_text:
        failures.append("Mandatory Stability expense modifier name is not localized")
    if "50%" not in localization_text:
        failures.append("Modifier description must explain the 50% vanilla-neutral slider position")

    if failures:
        print("CBP mandatory-expense validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("CBP mandatory Stability expense validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

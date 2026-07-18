#!/usr/bin/env python3
"""Validate the deliberately narrow standalone US-17 package boundary."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages/cbp_trade_profit_standalone"

ALLOWED_PACKAGE_FILES = {
    ".metadata/metadata.json",
    "README.md",
    "descriptor.mod",
    "in_game/common/auto_modifiers/cbp_trade_profit_auto_modifiers.txt",
    "in_game/common/on_action/cbp_trade_profit_on_actions.txt",
    "in_game/common/script_values/cbp_trade_profit_values.txt",
    "in_game/common/scripted_effects/cbp_trade_profit_effects.txt",
    "main_menu/localization/english/cbp_trade_profit_l_english.yml",
}

EXPECTED_EFFECTS = {
    "cbp_trade_profit_compute_native_corrections",
    "cbp_trade_profit_reconstruct_native_baselines",
    "cbp_trade_profit_refresh_native_modifiers",
}

EXPECTED_AUTO_MODIFIERS = {
    "cbp_trade_profit_selling_efficiency_cancellation",
    "cbp_trade_profit_import_efficiency_cancellation",
    "cbp_trade_profit_merchant_maintenance_reconciliation",
}

FORBIDDEN_FRAGMENTS = {
    "US-20": "US-20 scope",
    "us20": "US-20 identifiers",
    "every_trade": "route iteration",
    "trade_volume": "route-volume accounting",
    "sell_price": "route-price accounting",
    "buy_price": "route-price accounting",
    "to_market": "market traversal",
    "from_market": "market traversal",
    "traded_goods": "goods traversal",
    "add_gold": "treasury reconciliation",
    "add_goods_supply": "market-goods reconciliation",
    "variable_map(cmm": "CMM access",
    "has_variable_map = cmm": "CMM access",
    "cbp_trade_rework_enabled_trigger": "full-mod CMM feature gate",
    "country_market_good_stock": "country-stock accounting",
    "market_good_stock": "market-stock accounting",
    "cbp_add_stock": "NVE stock operators",
    "cbp_remove_stock": "NVE stock operators",
    "cbp_transfer_stock": "NVE stock operators",
    "promoted_market": "promoted-market accounting",
}


def top_level_names(text: str) -> set[str]:
    return set(re.findall(r"(?m)^([a-z0-9_]+)\s*=\s*\{", text))


def main() -> int:
    failures: list[str] = []
    actual_files = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
    }
    if actual_files != ALLOWED_PACKAGE_FILES:
        failures.append(
            "package file boundary changed "
            f"(unexpected={sorted(actual_files - ALLOWED_PACKAGE_FILES)}, "
            f"missing={sorted(ALLOWED_PACKAGE_FILES - actual_files)})"
        )

    effects_path = PACKAGE / "in_game/common/scripted_effects/cbp_trade_profit_effects.txt"
    modifiers_path = PACKAGE / "in_game/common/auto_modifiers/cbp_trade_profit_auto_modifiers.txt"
    on_actions_path = PACKAGE / "in_game/common/on_action/cbp_trade_profit_on_actions.txt"
    values_path = PACKAGE / "in_game/common/script_values/cbp_trade_profit_values.txt"
    existing_paths = [path for path in [effects_path, modifiers_path, on_actions_path, values_path] if path.is_file()]
    runtime_text = "\n".join(path.read_text(encoding="utf-8-sig") for path in existing_paths)

    for fragment, boundary in FORBIDDEN_FRAGMENTS.items():
        if fragment.lower() in runtime_text.lower():
            failures.append(f"standalone boundary violation: {boundary} ({fragment})")

    foreign_cbp_identifiers = sorted(
        identifier
        for identifier in set(re.findall(r"\bcbp_[a-z0-9_]+", runtime_text))
        if not identifier.startswith("cbp_trade_profit_")
    )
    if foreign_cbp_identifiers:
        failures.append(
            "standalone runtime depends on foreign CBP identifiers: "
            + ", ".join(foreign_cbp_identifiers)
        )

    effects = effects_path.read_text(encoding="utf-8-sig") if effects_path.is_file() else ""
    modifiers = modifiers_path.read_text(encoding="utf-8-sig") if modifiers_path.is_file() else ""
    on_actions = on_actions_path.read_text(encoding="utf-8-sig") if on_actions_path.is_file() else ""
    values = values_path.read_text(encoding="utf-8-sig") if values_path.is_file() else ""

    if top_level_names(effects) != EXPECTED_EFFECTS:
        failures.append("scripted effects must contain only the three US-17 native-modifier effects")
    if top_level_names(modifiers) != EXPECTED_AUTO_MODIFIERS:
        failures.append("auto modifiers must contain exactly the three US-17 formula corrections")

    required_effect_fragments = [
        "modifier:selling_efficiency",
        "modifier:import_efficiency",
        "modifier:merchant_maintenance_efficiency",
        "max = cbp_trade_profit_base_merchant_maintenance_cost",
        "cbp_trade_profit_previous_selling_correction",
        "cbp_trade_profit_previous_import_correction",
        "cbp_trade_profit_previous_maintenance_correction",
        "multiply = -1",
    ]
    for fragment in required_effect_fragments:
        if fragment not in effects:
            failures.append(f"missing US-17 formula contract: {fragment}")
    if "divide = 2" in effects or "min = 0" in effects:
        failures.append("combined efficiency must be an unclamped sum capped only by the maintenance-cost define")
    if effects.count("multiply = -1") != 6:
        failures.append(
            "US-17 must contain two efficiency cancellations, one maintenance-baseline subtraction, "
            "and three previous-correction removals"
        )

    for modifier, variable, endpoint in [
        (
            "cbp_trade_profit_selling_efficiency_cancellation",
            "cbp_trade_profit_native_selling_correction",
            "selling_efficiency = 1",
        ),
        (
            "cbp_trade_profit_import_efficiency_cancellation",
            "cbp_trade_profit_native_import_correction",
            "import_efficiency = 1",
        ),
        (
            "cbp_trade_profit_merchant_maintenance_reconciliation",
            "cbp_trade_profit_native_maintenance_correction",
            "merchant_maintenance_efficiency = 1",
        ),
    ]:
        if not all(token in modifiers for token in [modifier, f"has_variable = {variable}", f"var:{variable}", endpoint]):
            failures.append(f"incomplete auto-modifier contract: {modifier}")

    if "define:NCountry|MERCHANT_MAINTENANCE_COST" not in values:
        failures.append("US-17 cap must read the effective Vanilla merchant-maintenance-cost define")
    for hook in ["monthly_country_pulse", "on_policy_changed", "on_reform_change"]:
        if hook not in on_actions:
            failures.append(f"missing refresh hook: {hook}")
    if on_actions.count("cbp_trade_profit_refresh_country") != 4:
        failures.append("the three hooks must share exactly one country refresh dispatcher")

    if failures:
        print("CBP US-17 standalone validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("CBP US-17 standalone formula-only validation passed")
    print("  Runtime files       4")
    print("  Auto modifiers      3")
    print("  Route iterations    0")
    print("  Market mutations    0")
    print("  Treasury mutations  0")
    print("  External CBP deps    0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

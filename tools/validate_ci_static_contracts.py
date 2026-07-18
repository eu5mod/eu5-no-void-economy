#!/usr/bin/env python3
"""Static CI contracts for ModeU5 generated/CMM and US-17/US-20 surfaces.

This validator checks contracts that can be proven before launching EU5,
especially CMM wiring and US-17/US-20 assertions that would otherwise waste a
manual in-game run.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from validate_cbp_stock_operator_contracts import find_goods_supply_violations, find_violations, iter_scan_files

ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []

CMM_MOD_ID = "no_void_economy"
TRADE_REWORK_SETTING = "cbp_general_gameplay_gameplay_trade_rework_settings"
REVIEW_POP_SETTING = "cbp_debug_audit_misc_review_pop_settings"
TRADE_REWORK_FLAG = f"flag:{CMM_MOD_ID}__{TRADE_REWORK_SETTING}"
TRADE_REWORK_VALUE_LINK = f'"variable_map(cmm|{TRADE_REWORK_FLAG})" = 1'

CMM_SETTINGS: dict[str, tuple[str, str, bool]] = {
    "cbp_general_gameplay_gameplay_war_exhaustion_political_pressure_settings": ("cbp_general_gameplay_tab", "cbp_general_gameplay_gameplay_group", False),
    TRADE_REWORK_SETTING: ("cbp_general_gameplay_tab", "cbp_general_gameplay_gameplay_group", True),
    "cbp_general_gameplay_gameplay_empire_military_difficulties_settings": ("cbp_general_gameplay_tab", "cbp_general_gameplay_gameplay_group", False),
    "cbp_general_gameplay_country_level_stocks_countries_have_own_stocks_settings": ("cbp_general_gameplay_tab", "cbp_general_gameplay_country_level_stocks_group", False),
    "cbp_general_gameplay_country_level_stocks_only_sold_goods_create_revenue_settings": ("cbp_general_gameplay_tab", "cbp_general_gameplay_country_level_stocks_group", True),
    "cbp_general_gameplay_country_level_stocks_boycotts_wars_block_resource_buying_settings": ("cbp_general_gameplay_tab", "cbp_general_gameplay_country_level_stocks_group", True),
    "cbp_general_gameplay_other_extra_revenue_to_ai_settings": ("cbp_general_gameplay_tab", "cbp_general_gameplay_other_group", True),
    "cbp_economic_balance_design_activate_goods_decay_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_design_group", True),
    "cbp_economic_balance_design_sliders_adjustments_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_design_group", True),
    "cbp_economic_balance_design_pop_consumption_influenced_by_offer_demand_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_design_group", True),
    "cbp_economic_balance_balance_remove_control_penalty_on_research_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_balance_group", True),
    "cbp_economic_balance_balance_increased_location_specialisation_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_mandatorybase_group", True),
    "cbp_economic_balance_balance_marketplace_burgher_power_reduction_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_mandatorybase_group", True),
    "cbp_economic_balance_mandatorybase_fixed_rgo_prices_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_mandatorybase_group", True),
    "cbp_economic_balance_mandatorybase_maintenance_price_stabilisation_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_mandatorybase_group", True),
    "cbp_economic_balance_mandatorybase_economy_10_percent_faster_settings": ("cbp_economic_balance_tab", "cbp_economic_balance_mandatorybase_group", True),
    "cbp_war_subjects_balance_general_difficulty_settings": ("cbp_war_subjects_balance_tab", "cbp_war_subjects_balance_general_group", True),
    "cbp_war_subjects_balance_design_overlord_declares_war_settings": ("cbp_war_subjects_balance_tab", "cbp_war_subjects_balance_design_group", True),
    "cbp_war_subjects_balance_design_persistence_of_resources_settings": ("cbp_war_subjects_balance_tab", "cbp_war_subjects_balance_design_group", True),
    "cbp_war_subjects_balance_balance_shorter_wars_settings": ("cbp_war_subjects_balance_tab", "cbp_war_subjects_balance_balance_group", True),
    "cbp_war_subjects_balance_balance_adjust_rebel_threshold_settings": ("cbp_war_subjects_balance_tab", "cbp_war_subjects_balance_balance_group", True),
    "cbp_debug_audit_debug_audit_debug_messages_settings": ("cbp_debug_audit_tab", "cbp_debug_audit_debug_audit_group", True),
    "cbp_debug_audit_debug_audit_monthly_stock_check_settings": ("cbp_debug_audit_tab", "cbp_debug_audit_debug_audit_group", True),
    "cbp_debug_audit_debug_audit_save_mode_settings": ("cbp_debug_audit_tab", "cbp_debug_audit_debug_audit_group", True),
    REVIEW_POP_SETTING: ("cbp_debug_audit_tab", "cbp_debug_audit_misc_group", True),
}

REQUIRED_FILES = [
    ".metadata/metadata.json",
    "docs/technical/GAME_LOAD_LIFECYCLE.md",
    "in_game/common/on_action/cbp_configuration_on_actions.txt",
    "in_game/common/on_action/cbp_stock_on_actions.txt",
    "in_game/common/on_action/cbp__cmm_on_actions.txt",
    "in_game/common/on_action/cbp_cmm_runtime_on_action.txt",
    "in_game/common/on_action/cbp_country_governance_on_actions.txt",
    "in_game/common/auto_modifiers/cbp_us17_native_trade_profit_auto_modifiers.txt",
    "in_game/common/script_values/zzz_trade_reconciliation_values.txt",
    "in_game/common/scripted_effects/cbp__cmm_effects.txt",
    "in_game/common/scripted_effects/cbp_cmm_runtime_effects.txt",
    "in_game/common/scripted_effects/cbp_configuration_effects.txt",
    "in_game/common/scripted_effects/cbp_core04_market_entry_effects.txt",
    "in_game/common/scripted_effects/cbp_country_trade_owner_effects.txt",
    "in_game/common/scripted_effects/cbp_performance_effects.txt",
    "in_game/common/scripted_effects/cbp_q8_7_global_owner_effects.txt",
    "in_game/common/scripted_effects/cbp_trade_owner_modifier_reconciliation_effects.txt",
    "in_game/common/scripted_effects/cbp_us10_ui_effects.txt",
    "in_game/common/scripted_effects/zzz_trade_reconciliation_effects.txt",
    "in_game/common/scripted_guis/cbp__cmm_scripted_gui.txt",
    "in_game/common/scripted_triggers/cbp_configuration_triggers.txt",
    "main_menu/localization/english/cbp_us17_native_trade_profit_l_english.yml",
    "in_game/gui/cbp_us10_stock_lateralview.gui",
    "in_game/gui/zz_cbp_us10_production_subtabs.gui",
    "in_game/events/cbp_cmm_warning_events.txt",
    "packages/cbp_core_tests/in_game/events/cbp_revalidate_debug_events.txt",
    "packages/cbp_core_tests/in_game/events/cbp_us20_case12_probe_events.txt",
    "packages/cbp_core_tests/in_game/events/cbp_us17_owner_modifier_probe_events.txt",
    "packages/cbp_core_tests/in_game/common/scripted_effects/cbp_us20_case12_probe_effects.txt",
    "packages/cbp_core_tests/in_game/common/scripted_effects/cbp_us17_owner_modifier_test_effects.txt",
    "packages/cbp_core_tests/in_game/localization/cbp_us17_owner_modifier_probe_l_english.yml",
    "packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt",
    "packages/cbp_trade_rebalance/in_game/common/on_action/cbp_trade_package_on_actions.txt",
    "packages/cbp_war_rebalance/in_game/common/on_action/cbp_war_package_on_actions.txt",
    "main_menu/localization/english/cbp__cmm_l_english.yml",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig", errors="ignore")


def expect(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def block(text: str, name: str) -> str:
    marker = f"{name} = {{"
    start = text.find(marker)
    if start < 0:
        failures.append(f"Missing block: {name}")
        return ""
    open_brace = text.find("{", start)
    depth = 0
    in_quote = False
    for index in range(open_brace, len(text)):
        char = text[index]
        if char == '"':
            in_quote = not in_quote
        if not in_quote:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
    failures.append(f"Unclosed block: {name}")
    return ""


def field_value(text: str, field_name: str) -> str:
    match = re.search(rf"^[ \t]*{re.escape(field_name)}[ \t]*=[ \t]*(.*?)[ \t]*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate_required_files() -> None:
    for path in REQUIRED_FILES:
        expect((ROOT / path).is_file(), f"Required CI/static-contract file is missing: {path}")


def validate_no_legacy_review_pop_id(all_text: str) -> None:
    exact_legacy_lines = [
        r"^\s*setting_id\s*=\s*review_pop\s*$",
        r"^\s*tab_id\s*=\s*cbp_general\s*$",
        r"^\s*group_id\s*=\s*cbp_no_void_economy\s*$",
    ]
    for pattern in exact_legacy_lines:
        expect(re.search(pattern, all_text, re.MULTILINE) is None, f"Legacy review-pop CMM assignment must not remain: {pattern}")
    for token in ["flag:no_void_economy__review_pop", "no_void_economy__review_pop"]:
        expect(token not in all_text, f"Legacy review-pop CMM token must not remain: {token}")


def validate_cmm_surface(cmm_effects: str, runtime_effects: str, config_triggers: str, loc: str, scripted_gui: str) -> None:
    register_block_re = re.compile(
        r"cmm_register_(?:global_)?(?:bool|dropdown)_setting\s*=\s*\{(?P<body>.*?)\n\s*\}",
        re.DOTALL,
    )
    registered_settings: set[str] = set()

    for match in register_block_re.finditer(cmm_effects):
        body = match.group("body")
        setting_id = field_value(body, "setting_id")
        tab_id = field_value(body, "tab_id")
        group_id = field_value(body, "group_id")
        registered_settings.add(setting_id)
        expect(setting_id in CMM_SETTINGS, f"Unexpected generated NVE CMM setting id in registration: {setting_id or '<blank>'}")
        if setting_id in CMM_SETTINGS:
            expected_tab_id, expected_group_id, _has_scripted_gui = CMM_SETTINGS[setting_id]
            expect(tab_id == expected_tab_id, f"CMM setting {setting_id} must use tab_id {expected_tab_id}, found {tab_id or '<blank>'}")
            expect(group_id == expected_group_id, f"CMM setting {setting_id} must use group_id {expected_group_id}, found {group_id or '<blank>'}")

    expect(registered_settings == set(CMM_SETTINGS), "Generated NVE CMM registrations must match the expected setting catalog")

    runtime_review_pop = block(runtime_effects, "cbp_cmm_register_review_pop")
    expect(f"setting_id = {REVIEW_POP_SETTING}" in runtime_review_pop, "Runtime review-pop registration must use the standard setting id")
    expect("tab_id = cbp_debug_audit_tab" in runtime_review_pop, "Runtime review-pop registration must use the Debug & Audit tab")
    expect("group_id = cbp_debug_audit_misc_group" in runtime_review_pop, "Runtime review-pop registration must use the Debug & Audit / Misc group")

    for setting_id, (_tab_id, _group_id, has_scripted_gui) in CMM_SETTINGS.items():
        expect(f"setting_id = {setting_id}" in cmm_effects, f"Missing CMM registration for {setting_id}")
        expect(f"{CMM_MOD_ID}__{setting_id}_name" in loc, f"Missing localization name for {setting_id}")
        expect(f"{CMM_MOD_ID}__{setting_id}_desc" in loc, f"Missing localization description for {setting_id}")
        if has_scripted_gui:
            expect(f"{CMM_MOD_ID}__{setting_id}" in scripted_gui, f"Missing scripted GUI handler for {setting_id}")

    expect("no_void_economy__cbp_debug_audit_tab__cbp_debug_audit_misc_group_name" in loc, "Missing localization name for Debug & Audit / Misc group")

    trade_trigger = block(config_triggers, "cbp_trade_rework_enabled_trigger")
    expect("has_variable_map = cmm" in trade_trigger, "Trade rework trigger must require the CMM variable map")
    expect(TRADE_REWORK_FLAG in trade_trigger, "Trade rework trigger must read the normalized CMM trade-rework flag")
    expect(TRADE_REWORK_VALUE_LINK in trade_trigger, "Trade rework trigger must require CMM trade-rework value 1")


def validate_us17_owner_modifier_contract(
    *,
    trade_values: str,
    owner_modifier_effects: str,
    native_auto_modifiers: str,
    country_governance_on_actions: str,
    all_cbp_on_actions: str,
    native_localization: str,
    owner_modifier_probe_events: str,
    owner_modifier_probe_effects: str,
) -> None:
    correction_formula = block(owner_modifier_effects, "cbp_compute_us17_native_profit_corrections_from_baselines")
    reconstruction = block(owner_modifier_effects, "cbp_reconstruct_us17_native_baselines_from_effective_values")
    refresh = block(owner_modifier_effects, "cbp_refresh_us17_native_profit_modifiers_for_current_country")
    live_wrapper = block(owner_modifier_effects, "cbp_run_us20_route_loss_reconciliation")

    for semantic_name, modifier_name in [
        ("buying/import efficiency", "import_efficiency"),
        ("selling efficiency", "selling_efficiency"),
        ("merchant maintenance efficiency", "merchant_maintenance_efficiency"),
    ]:
        expect(
            f"value = modifier:{modifier_name}" in trade_values,
            f"US17 must define a country-scoped script value for {semantic_name} via modifier:{modifier_name}",
        )

    combined_assignment = re.search(
        r"name\s*=\s*cbp_us17_native_combined_efficiency(?P<body>.*?)(?:\n\s*\}|\n\s*save_temporary_scope_value_as)",
        correction_formula,
        re.DOTALL,
    )
    combined_body = combined_assignment.group("body") if combined_assignment else ""
    expect(bool(combined_assignment), "US17 native formula must calculate the import/selling combined efficiency")
    expect("cbp_us17_native_baseline_import_efficiency" in combined_body, "US17 combined efficiency must include import efficiency")
    expect("cbp_us17_native_baseline_selling_efficiency" in combined_body, "US17 combined efficiency must include selling efficiency")
    expect("divide = 2" not in combined_body, "US17 combined efficiency is a sum and must not be divided by two")
    expect(
        "max = cbp_trade_base_merchant_maintenance_cost" in combined_body,
        "US17 combined efficiency must be capped by the loaded merchant-maintenance-cost define",
    )
    expect("min = 0" not in combined_body, "US17 combined efficiency must not have a lower clamp of 0")

    expect("cbp_us17_native_baseline_maintenance_efficiency" in correction_formula, "US17 native formula must consume merchant maintenance efficiency")
    expect("cbp_us17_native_baseline_maintenance_factor" not in correction_formula, "US17 must replace native maintenance efficiency instead of scaling its remaining factor")
    expect(
        re.search(
            r"name\s*=\s*cbp_us17_native_maintenance_correction_result.*?"
            r"value\s*=\s*scope:cbp_us17_native_combined_efficiency.*?"
            r"value\s*=\s*scope:cbp_us17_native_baseline_maintenance_efficiency\s+multiply\s*=\s*-1",
            correction_formula,
            re.DOTALL,
        )
        is not None,
        "US17 maintenance correction must replace the baseline with C through correction C - M",
    )
    expect("divide =" not in correction_formula, "US17 native correction formula must not divide")
    expect("cbp_us17_native_previous_selling_correction" in reconstruction, "US17 refresh must remove its previous selling correction")
    expect("cbp_us17_native_previous_import_correction" in reconstruction, "US17 refresh must remove its previous import correction")
    expect("cbp_us17_native_previous_maintenance_correction" in reconstruction, "US17 refresh must remove its previous maintenance correction")
    expect("cbp_reconstruct_us17_native_baselines_from_effective_values = yes" in refresh, "US17 refresh must reconstruct non-CBP baselines before recalculation")
    expect("cbp_compute_us17_native_profit_corrections_from_baselines = yes" in refresh, "US17 refresh must calculate native modifier corrections")
    expect("cbp_trade_rework_enabled_trigger = yes" in live_wrapper, "US17 owner-modifier wrapper must defensively gate itself")
    expect("add_gold" not in live_wrapper, "US17 live route wrapper must not add a second treasury correction")
    expect("cbp_apply_trade_efficiency_income_reconciliation_to_trade_owner" not in live_wrapper, "US17 live route wrapper must leave money accounting to Vanilla")
    expect("cbp_compute_us20_goods_received_delta = yes" in live_wrapper, "US17 native profit migration must preserve US20 goods reconciliation")

    for modifier_name, variable_name, modifier_type in [
        ("cbp_us17_selling_efficiency_cancellation", "cbp_us17_native_selling_correction", "selling_efficiency"),
        ("cbp_us17_import_efficiency_cancellation", "cbp_us17_native_import_correction", "import_efficiency"),
        ("cbp_us17_merchant_maintenance_reconciliation", "cbp_us17_native_maintenance_correction", "merchant_maintenance_efficiency"),
    ]:
        modifier_block = block(native_auto_modifiers, modifier_name)
        expect(
            re.search(rf"scales_with\s*=\s*\{{[^{{}}]*value\s*=\s*var:{variable_name}[^{{}}]*\}}", modifier_block, re.DOTALL) is not None,
            f"{modifier_name} must scale from its persisted correction through a script-value block",
        )
        expect(f"{modifier_type} = 1" in modifier_block, f"{modifier_name} must write the native {modifier_type} surface")
        expect("cbp_trade_rework_enabled_trigger = yes" in modifier_block, f"{modifier_name} must be gated by the trade-rework setting")
        expect(f"AUTO_MODIFIER_NAME_{modifier_name}" in native_localization, f"Missing visible localization for {modifier_name}")

    policy_hook = block(country_governance_on_actions, "on_policy_changed")
    reform_hook = block(country_governance_on_actions, "on_reform_change")
    shared_dispatcher = block(country_governance_on_actions, "cbp_country_governance_changed")
    expect(re.findall(r"\bcbp_[a-z0-9_]+\b", policy_hook) == ["cbp_country_governance_changed"], "on_policy_changed must list only the shared country-governance dispatcher")
    expect(re.findall(r"\bcbp_[a-z0-9_]+\b", reform_hook) == ["cbp_country_governance_changed"], "on_reform_change must list only the shared country-governance dispatcher")
    expect(
        len(re.findall(r"(?m)^on_policy_changed\s*=", all_cbp_on_actions)) == 1,
        "CBP must declare exactly one shared on_policy_changed registration across Core and companion packages",
    )
    expect(
        len(re.findall(r"(?m)^on_reform_change\s*=", all_cbp_on_actions)) == 1,
        "CBP must declare exactly one shared on_reform_change registration across Core and companion packages",
    )
    expect(shared_dispatcher.count("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes") == 1, "Shared governance dispatcher must refresh US17 exactly once")
    expect(shared_dispatcher.count("scope_type = country") == 1, "Shared governance dispatcher must fail closed outside country scope")
    expect("cbp_us17_native_profit_policy_changed" not in all_cbp_on_actions, "Legacy duplicate US17 policy callback must not return")
    expect("cbp_us17_native_profit_reform_changed" not in all_cbp_on_actions, "Legacy duplicate US17 reform callback must not return")

    expect("namespace = cbp_us17_owner_modifiers" in owner_modifier_probe_events, "US17 owner-modifier probe namespace must remain available")
    expect("cbp_us17_owner_modifiers.1" in owner_modifier_probe_events, "US17 owner-modifier probe entry event must remain available")
    expect("cbp_debug_run_us17_owner_modifier_probe = yes" in owner_modifier_probe_events, "US17 owner-modifier event must call the focused probe")
    expect("cbp_us17_owner_modifiers.11" in owner_modifier_probe_events, "US17 owner-modifier probe must keep its delayed live-modifier check")
    expect("cbp_debug_finish_us17_owner_modifier_probe = yes" in owner_modifier_probe_events, "US17 delayed probe event must verify effective country modifiers")

    for assertion in [
        "positive_combined_efficiency",
        "import_cancelled",
        "selling_cancelled",
        "maintenance_replaced_by_combined_efficiency",
        "capped_native_maintenance_amount_equivalent",
        "negative_sum_preserved",
        "negative_efficiency_increases_maintenance",
        "positive_sum_capped_by_merchant_maintenance_define",
        "maintenance_baseline_fully_replaced",
        "idempotent_recalculation",
        "live_auto_modifier_application",
        "cmm_trade_rework_disabled",
        "mode=native_auto_modifiers",
        "combination=sum_without_division",
        "clamp=merchant_maintenance_cost_define",
        "treasury_reconciliation=none",
    ]:
        expect(assertion in owner_modifier_probe_effects, f"US17 owner-modifier probe must assert {assertion}")


def validate_us17_us20_static_contract(
    *,
    stock_on_actions: str,
    country_trade_owner_effects: str,
    q8_7_global_owner_effects: str,
    trade_reconciliation_effects: str,
    owner_modifier_effects: str,
    revalidate_events: str,
    us20_probe_events: str,
    us20_probe_effects: str,
) -> None:
    country_cycle = block(country_trade_owner_effects, "cbp_run_monthly_country_trade_owner_cycle")
    route_effect = block(trade_reconciliation_effects, "cbp_run_us17_us20_route_reconciliation")
    historical_formula = block(trade_reconciliation_effects, "cbp_compute_us17_us20_route_formula_from_current_values")
    historical_combined_assignment = re.search(
        r"name\s*=\s*gui_cbp_buying_selling_efficiency_clamped(?P<body>.*?)(?:\n\s*\}|\n\s*save_temporary_scope_value_as)",
        historical_formula,
        re.DOTALL,
    )
    historical_combined_body = historical_combined_assignment.group("body") if historical_combined_assignment else ""
    live_hook_call = "cbp_run_us20_route_loss_reconciliation = yes"
    legacy_hook_call = "cbp_run_us17_us20_route_reconciliation = yes"
    e2e_probe_call = "cbp_debug_run_us20_case12_market_loss_probe = yes"

    expect(country_cycle.count(live_hook_call) == 1, "Country trade-owner cycle must call US20 route-loss reconciliation exactly once per trade")
    expect(legacy_hook_call not in country_cycle, "Country trade-owner live cycle must not call the historical seeded reconciliation wrapper")
    expect(country_cycle.count("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes") == 1, "Country trade-owner cycle must refresh US17 native modifiers exactly once before every_trade")
    expect(
        country_cycle.index("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes") < country_cycle.index("every_trade = {"),
        "Country trade-owner cycle must refresh US17 native modifiers before entering every_trade",
    )
    expect("cbp_capture_trade_owner_country_modifier_inputs = yes" not in country_cycle, "Country trade-owner live cycle must not recalculate US17 money per route")
    expect("every_trade = {" in country_cycle, "Country trade-owner cycle must use the native every_trade loop")
    expect("cbp_trade_rework_enabled_trigger = yes" in route_effect, "Historical US-17/US-20 route effect must remain defensively gated for deterministic tests")
    expect("cbp_prepare_trade_efficiency_reconciliation_runtime_metrics_once = yes" in route_effect, "Historical US-17/US-20 route effect must prepare metrics inside the gated body")
    expect(bool(historical_combined_assignment), "Historical US17 formula must calculate combined efficiency")
    expect("divide = 2" not in historical_combined_body, "Historical US17 formula must follow the sum-without-division business rule")
    expect("min = 0" not in historical_combined_body, "Historical US17 combined efficiency must preserve negative values")
    expect(live_hook_call not in q8_7_global_owner_effects, "US20 live hook must not be placed in the Q8.7 market-local body")
    expect(live_hook_call not in stock_on_actions, "US20 live hook must not be placed directly in monthly on_actions")
    expect(
        "every_market_center_in_country = {" not in country_trade_owner_effects + q8_7_global_owner_effects + trade_reconciliation_effects + owner_modifier_effects,
        "Trade-rework runtime must not reintroduce a market-center every_trade scaffold",
    )


    unsafe_global_counter = re.compile(
        r"set_global_variable\s*=\s*\{[^{}]*name\s*=\s*cbp_(?:trade_efficiency|us20)[^{}]*value\s*=\s*\{\s*value\s*=\s*global_var:",
        re.DOTALL,
    )
    expect(
        unsafe_global_counter.search(trade_reconciliation_effects + owner_modifier_effects) is None,
        "US17/US20 counters must not use set_global_variable value={ value=global_var:X add=1 }; use if-unset/set-1 else change_global_variable",
    )
    expect("change_global_variable = { name = cbp_trade_efficiency_routes_seen add = 1 }" in trade_reconciliation_effects, "Route-seen counter must use change_global_variable after first set")
    expect("change_global_variable = { name = cbp_us20_market_goods_supply_loss_routes add = 1 }" in trade_reconciliation_effects, "US20 market-loss counter must use change_global_variable after first set")

    expect("save_temporary_scope_as = cbp_vanilla_market_goods_supply_good" in trade_reconciliation_effects, "US20 market loss must pass the saved route good scope into the central vanilla-supply helper")
    expect("name = cbp_vanilla_market_goods_supply_delta value = scope:gui_cbp_us20_market_goods_supply_delta" in trade_reconciliation_effects, "US20 market loss must pass the computed negative market goods delta into the central vanilla-supply helper")
    expect("cbp_apply_vanilla_market_goods_supply_delta_from_saved_good = yes" in trade_reconciliation_effects, "US20 market loss must apply vanilla supply through the central stock helper")
    expect("cbp_select_us20_goods_receiver_country_for_promoted_market = yes" in trade_reconciliation_effects, "Promoted-destination loss must select a receiver before country-stock loss")

    expect(e2e_probe_call not in revalidate_events, "Experimental US20 E2E probe must stay outside stable full revalidation")
    expect("Step 13/13" in revalidate_events, "Stable full revalidation must end at the US17/US20 route-reconciliation scenario")
    expect(e2e_probe_call in us20_probe_events, "Standalone US20 probe event must call the US20 E2E probe explicitly")
    expect("namespace = cbp_us20_probe" in us20_probe_events, "Standalone US20 probe event namespace must remain available")
    expect("cbp_us20_probe.1" in us20_probe_events, "Standalone US20 probe entry event must remain available")

    required_probe_assertions = [
        "case1_classification_expected=1",
        "case2_classification_expected=1",
        "case3_classification_expected=2",
        "case4_classification_expected=1",
        "market_goods_supply_loss_routes_expected=5",
        "promoted_destination_country_loss_routes_expected=3",
        "explicit_receiver_selected_expected=1",
        "trade_owner_receiver_selected_expected=1",
        "goods_delta_should_not_block",
        "receiver_selection_should_not_block_for_explicit_trade_owner_or_allocator_paths",
        "case5_allocator_receiver",
        "receivers=explicit_plus_trade_owner_plus_allocator",
    ]
    for assertion in required_probe_assertions:
        expect(assertion in us20_probe_effects, f"US20 E2E probe must assert {assertion}")


def validate_native_trade_quantity_contract(
    *, country_trade_owner_effects: str, transport_helpers: str
) -> None:
    capture = block(
        country_trade_owner_effects,
        "cbp_capture_country_trade_owner_trade_quantity",
    )
    expect(
        "value = trade_volume" in capture,
        "Native trade quantity capture must read trade_volume",
    )
    expect(
        "value = scope:cbp_trade_owner_trade_volume" in capture,
        "Native trade quantity must copy trade_volume directly",
    )
    expect(
        "cbp_compute_trade_owner_goods_quantity_from_traded_good" not in capture,
        "Native trade quantity must not pass through static transport_cost conversion",
    )
    expect(
        "cbp_compute_trade_owner_goods_quantity_from_traded_good" not in transport_helpers,
        "Generated transport helpers must not recreate the native trade-owner dispatcher",
    )
    expect(
        "cbp_compute_goods_quantity_from_trade_capacity_good_glass" in transport_helpers,
        "Generic literal-good capacity conversion helpers must remain available",
    )


def validate_us10_test_contract(us10_test_effects: str) -> None:
    """Keep the US-10 harness aligned with the canonical generated ledgers."""

    capacity_conversion = block(
        us10_test_effects,
        "cbp_debug_run_us10_trade_capacity_conversion_tests",
    )
    expect(
        "cbp_compute_goods_quantity_from_trade_capacity_good_glass" in capacity_conversion,
        "US10 capacity conversion probe must use glass instead of a transport_cost=1 good",
    )
    expect(
        "test_cbp_us10_conversion_glass_transport_cost = 0.5" in capacity_conversion,
        "US10 glass probe must assert the explicit transport cost 0.5",
    )
    expect(
        "test_cbp_us10_conversion_glass_quantity = 40" in capacity_conversion,
        "US10 glass probe must assert capacity 20 converts to quantity 40",
    )

    legacy_ledger_patterns = [
        "test_cbp_consumption_wheat_requested_by_market",
        "test_cbp_consumption_wheat_satisfied_by_market",
        "test_cbp_consumption_wheat_unsatisfied_by_market",
        "test_cbp_trade_wheat_requested_by_market",
        "test_cbp_trade_wheat_transferred_by_market",
        "test_cbp_trade_wheat_unsatisfied_by_market",
    ]
    for pattern in legacy_ledger_patterns:
        expect(
            pattern not in us10_test_effects,
            f"US-10 harness must read canonical generated outcome maps, not stale test ledger {pattern}",
        )

    expect(
        "THIS.GetVariable('cbp_us10_ui" not in us10_test_effects,
        "US-10 debug dumps must read gui_cbp_us10_ui* variables, matching the variables they set",
    )


def validate_us10_ui_widget_contract(*, lateralview_gui: str, production_subtabs: str, ui_effects: str, stock_loc: str) -> None:
    expect(
        "template cbp_us10_stock_panel" in lateralview_gui,
        "US-10 stock lateralview file must expose the cbp_us10_stock_panel template",
    )
    expect(
        "widget = { using = cbp_us10_stock_panel }" in production_subtabs,
        "US-10 Production subtab override must mount the cbp_us10_stock_panel template",
    )
    expect(
        not (ROOT / "in_game/gui/scripted_widgets/cbp_us10_stock.txt").exists(),
        "US-10 stock panel must not be registered as a standalone scripted widget",
    )
    expect(
        "THIS.GetVariable('cbp_us10_ui" not in ui_effects + stock_loc,
        "US-10 UI runtime dumps/localization must read gui_cbp_us10_ui* variables, matching the variables they set",
    )
    expect(
        "remove_variable = gui_cbp_us10_ui_" not in ui_effects,
        "US-10 UI refresh must initialize presentation variables to zero instead of leaving them unset",
    )


def validate_perf14_test_contract(perf14_text: str, stock_loc: str) -> None:
    expect(
        "THIS.GetVariable('cbp_perf14_" not in perf14_text,
        "PERF-14 debug dumps must read test_cbp_perf14* or gui_cbp_perf14* variables, matching the variables they set",
    )
    expect(
        "THIS.GetVariable('cbp_perf14_ui_" not in stock_loc,
        "PERF-14 localization dumps must read gui_cbp_perf14_ui* variables, matching the variables they set",
    )
    expect(
        "cbp_no_void_economy_main" not in perf14_text,
        "PERF-14 tests must use the current CMM main-mode setting id, not legacy cbp_no_void_economy_main",
    )


def validate_core04_test_contract(core04_test_effects: str) -> None:
    expect(
        "cbp_no_void_economy_main" not in core04_test_effects,
        "CORE-04 tests must use the current CMM main-mode setting id, not legacy cbp_no_void_economy_main",
    )


def validate_us04_debug_event_contract(us04_debug_events: str) -> None:
    def event_block(event_id: str) -> str:
        return block(us04_debug_events, event_id)

    for event_id in [
        "cbp_us04_debug.31",
        "cbp_us04_debug.32",
        "cbp_us04_debug.40",
        "cbp_us04_debug.51",
        "cbp_us04_debug.52",
    ]:
        expect("orphan = yes" not in event_block(event_id), f"{event_id} has callers and must not be scripted as orphan")

    for event_id in ["cbp_us04_debug.30", "cbp_us04_debug.50"]:
        expect("orphan = yes" in event_block(event_id), f"{event_id} is a direct-console compatibility event and should remain orphan")


def validate_core_stock_test_contract(stock_test_effects: str) -> None:
    expect(
        "test_cbp_wheat_stock_by_market" not in stock_test_effects,
        "CORE stock tests must read cbp_wheat_stock_by_market, not stale test_cbp_wheat_stock_by_market",
    )
    expect(
        "test_cbp_wheat_market_stock" not in stock_test_effects,
        "CORE stock tests must read cbp_wheat_market_stock, not stale test_cbp_wheat_market_stock",
    )
    expect(
        "test_cbp_wheat_active_markets" not in stock_test_effects,
        "CORE stock tests must read cbp_wheat_active_markets, not stale test_cbp_wheat_active_markets",
    )
    expect(
        "THIS.GetVariable('cbp_debug_us11_ui" not in stock_test_effects,
        "US-11 debug dumps must read gui_cbp_debug_us11_ui* variables, matching the variables they set",
    )


def validate_stock_operator_contract() -> None:
    for path in iter_scan_files(ROOT):
        relative = path.relative_to(ROOT)
        if (
            relative.parts[:2] == ("packages", "cbp_economy_rebalance")
            and not path.name.startswith("cbp_")
        ):
            # CBG exact-path outputs preserve Vanilla filenames and Vanilla
            # operators. The contract applies to CBP-authored runtime files.
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for violation in find_violations(path, text):
            rel = violation.path.relative_to(ROOT)
            failures.append(
                f"{rel}:{violation.line}: {violation.operator} must include {violation.required_field} = yes or {violation.required_field} = no"
            )
        for violation in find_goods_supply_violations(path, text):
            rel = violation.path.relative_to(ROOT)
            failures.append(
                f"{rel}:{violation.line}: add_goods_supply must only be called from cbp_stock_effects.txt or packages/cbp_core_tests"
            )


def validate_perf10_13_test_contract(perf10_13_test_effects: str) -> None:
    expect(
        "test_cbp_wheat_active_markets" not in perf10_13_test_effects,
        "PERF-10/13 tests must read cbp_wheat_active_markets, not stale test_cbp_wheat_active_markets",
    )
    expect(
        "THIS.GetVariable('cbp_perf10_13_ui" not in perf10_13_test_effects,
        "PERF-10/13 debug dumps must read gui_cbp_perf10_13_ui* variables, matching the variables they set",
    )


def validate_game_load_lifecycle_contract(
    *,
    configuration_on_actions: str,
    configuration_effects: str,
    stock_on_actions: str,
    stock_effects: str,
    core04_effects: str,
    economy_on_actions: str,
    trade_on_actions: str,
    war_on_actions: str,
    lifecycle_doc: str,
) -> None:
    config_load = block(configuration_on_actions, "on_game_load")
    config_load_action = block(configuration_on_actions, "cbp_configuration_on_game_load")
    expect("cbp_configuration_on_game_load" in config_load, "Configuration on_game_load must call the load-repair on_action")
    expect(
        "cbp_repair_configuration_state_on_game_load = yes" in config_load_action,
        "Configuration load on_action must call the idempotent load-repair effect",
    )
    expect(
        "cbp_initialize_configuration_state_effect = yes" not in config_load_action,
        "Configuration on_game_load must not rerun the full start-game initializer",
    )

    config_repair = block(configuration_effects, "cbp_repair_configuration_state_on_game_load")
    for token in [
        "cbp_core_package_loaded",
        "cbp_core_package_version",
        "cbp_apply_generated_local_runtime_mode = yes",
        "cbp_enter_cbp_performance_mode = yes",
        "cbp_enter_minimal_accounting_persistence = yes",
        "cbp_prepare_performance_mode_human_relevant_markets = yes",
        "cbp_configuration_load_repair_version",
    ]:
        expect(token in config_repair, f"Configuration load repair must maintain {token}")

    stock_load = block(stock_on_actions, "on_game_load")
    stock_load_action = block(stock_on_actions, "cbp_load_game_stock_initialization_pulse")
    expect("delay = { days = 1 }" in stock_load, "Stock on_game_load repair must keep the delayed startup timing")
    expect("cbp_load_game_stock_initialization_pulse" in stock_load, "Stock on_game_load must call the load-repair pulse")
    expect(
        "cbp_repair_stock_lifecycle_on_game_load = yes" in stock_load_action,
        "Stock load pulse must call the idempotent load-repair effect",
    )

    stock_repair = block(stock_effects, "cbp_repair_stock_lifecycle_on_game_load")
    current_schema_repair = block(stock_effects, "cbp_repair_current_schema_runtime_marker")
    stock_dispatcher = block(stock_effects, "cbp_start_game_stock_initialization_dispatcher")
    for token in [
        "has_global_variable = cbp_stock_schema_version",
        "global_var:cbp_stock_schema_version = cbp_current_stock_schema_version",
        "NOT = { cbp_initialization_complete_trigger = yes }",
        "NOT = { cbp_initialization_in_progress_trigger = yes }",
        "NOT = { cbp_initialization_failed_trigger = yes }",
        "global_var:cbp_initialization_failure_code = 21",
        "remove_global_variable = cbp_initialization_failure_detected",
        "remove_global_variable = cbp_initialization_failure_code",
        "NOT = { has_global_variable = cbp_initialization_failure_detected }",
        "NOT = { has_global_variable = cbp_initialization_failure_code }",
        "name = cbp_initialization_state",
        "value = 2",
        "value = 6",
    ]:
        expect(token in current_schema_repair, f"Current-schema load repair must maintain {token}")
    expect(
        "cbp_repair_current_schema_runtime_marker = yes" in stock_dispatcher,
        "Stock initialization dispatcher must repair legacy current-schema readiness markers before fail-closed checks",
    )
    for token in [
        "cbp_initialize_pop_demand_multipliers_once = yes",
        "cbp_repair_current_schema_runtime_marker = yes",
        "cbp_stock_runtime_ready_trigger = yes",
        "cbp_start_game_stock_initialization_dispatcher = yes",
        "cbp_core04_refresh_all_location_market_memory = yes",
        "cbp_stock_load_repair_version",
    ]:
        expect(token in stock_repair, f"Stock load repair must maintain {token}")
    expect(
        "cbp_run_fresh_opening_stock_initialization = yes" not in stock_repair,
        "Stock load repair must delegate through the dispatcher, not force fresh opening-stock initialization",
    )

    memory_refresh = block(core04_effects, "cbp_core04_refresh_all_location_market_memory")
    expect("cbp_stock_runtime_ready_trigger = yes" in memory_refresh, "CORE-04 all-location memory refresh must be stock-runtime guarded")
    expect("cbp_core04_market_memory_snapshot_version" in memory_refresh, "CORE-04 load/start memory refresh must write a snapshot marker")

    for package_name, package_text, loaded_marker, version_marker in [
        ("Rebalance Economy", economy_on_actions, "cbp_economy_rebalance_loaded", "cbp_economy_package_version"),
        ("Rebalance Trade", trade_on_actions, "cbp_trade_rebalance_loaded", "cbp_trade_package_version"),
        ("Rebalance War", war_on_actions, "cbp_war_rebalance_loaded", "cbp_war_package_version"),
    ]:
        package_start = block(package_text, "on_game_start")
        package_load = block(package_text, "on_game_load")
        expect(package_start, f"{package_name} package must keep an on_game_start marker hook")
        expect(package_load, f"{package_name} package must keep an on_game_load marker repair hook")
        expect(loaded_marker in package_text, f"{package_name} on_actions must write {loaded_marker}")
        expect(version_marker in package_text, f"{package_name} on_actions must write {version_marker}")

    trade_load_action = block(trade_on_actions, "cbp_trade_rebalance_package_on_game_load")
    war_load_action = block(war_on_actions, "cbp_war_rebalance_package_on_game_load")
    expect(
        "cbp_trade_rebalance_package_on_game_start = yes" not in trade_load_action,
        "Trade package on_game_load must write markers directly instead of calling its on_game_start action as an effect",
    )
    expect(
        "cbp_war_rebalance_package_on_game_start = yes" not in war_load_action,
        "War package on_game_load must write markers directly instead of calling its on_game_start action as an effect",
    )

    for token in [
        "on_game_load",
        "cbp_configuration_load_repair_version",
        "cbp_stock_load_repair_version",
        "cbp_core04_market_memory_snapshot_version",
        "does not support arbitrary package-set changes mid-campaign",
    ]:
        expect(token in lifecycle_doc, f"Game-load lifecycle documentation must mention {token}")


def main() -> int:
    validate_required_files()
    if failures:
        return 1

    metadata = json.loads(read(".metadata/metadata.json"))
    expect(metadata.get("id") == "cbp_core", "Core metadata id must remain cbp_core")
    expect(
        any(item.get("id") == "community_mod_framework" for item in metadata.get("relationships", [])),
        "Core package must declare CMF as a required dependency",
    )

    stock_on_actions = read("in_game/common/on_action/cbp_stock_on_actions.txt")
    configuration_on_actions = read("in_game/common/on_action/cbp_configuration_on_actions.txt")
    trade_values = read("in_game/common/script_values/zzz_trade_reconciliation_values.txt")
    cmm_effects = read("in_game/common/scripted_effects/cbp__cmm_effects.txt")
    runtime_effects = read("in_game/common/scripted_effects/cbp_cmm_runtime_effects.txt")
    scripted_gui = read("in_game/common/scripted_guis/cbp__cmm_scripted_gui.txt")
    config_triggers = read("in_game/common/scripted_triggers/cbp_configuration_triggers.txt")
    configuration_effects = read("in_game/common/scripted_effects/cbp_configuration_effects.txt")
    stock_effects = read("in_game/common/scripted_effects/cbp_stock_effects.txt")
    core04_effects = read("in_game/common/scripted_effects/cbp_core04_market_entry_effects.txt")
    country_trade_owner_effects = read("in_game/common/scripted_effects/cbp_country_trade_owner_effects.txt")
    transport_helpers = read("in_game/common/scripted_effects/cbp_transport_cost_generated.txt")
    q8_7_global_owner_effects = read("in_game/common/scripted_effects/cbp_q8_7_global_owner_effects.txt")
    trade_reconciliation_effects = read("in_game/common/scripted_effects/zzz_trade_reconciliation_effects.txt")
    owner_modifier_effects = read("in_game/common/scripted_effects/cbp_trade_owner_modifier_reconciliation_effects.txt")
    native_trade_profit_auto_modifiers = read("in_game/common/auto_modifiers/cbp_us17_native_trade_profit_auto_modifiers.txt")
    country_governance_on_actions = read("in_game/common/on_action/cbp_country_governance_on_actions.txt")
    cbp_on_action_paths = sorted((ROOT / "in_game/common/on_action").glob("*.txt"))
    cbp_on_action_paths.extend(sorted(ROOT.glob("packages/*/in_game/common/on_action/*.txt")))
    cbp_on_action_paths = [path for path in cbp_on_action_paths if path.name != "_hardcoded.txt"]
    all_cbp_on_actions = "\n".join(path.read_text(encoding="utf-8") for path in cbp_on_action_paths)
    native_trade_profit_localization = read("main_menu/localization/english/cbp_us17_native_trade_profit_l_english.yml")
    revalidate_events = read("packages/cbp_core_tests/in_game/events/cbp_revalidate_debug_events.txt")
    us20_probe_events = read("packages/cbp_core_tests/in_game/events/cbp_us20_case12_probe_events.txt")
    us20_probe_effects = read("packages/cbp_core_tests/in_game/common/scripted_effects/cbp_us20_case12_probe_effects.txt")
    owner_modifier_probe_events = read("packages/cbp_core_tests/in_game/events/cbp_us17_owner_modifier_probe_events.txt")
    owner_modifier_probe_effects = read("packages/cbp_core_tests/in_game/common/scripted_effects/cbp_us17_owner_modifier_test_effects.txt")
    us10_test_effects = read("packages/cbp_core_tests/in_game/common/scripted_effects/cbp_us10_test_effects.txt")
    stock_test_effects = read("packages/cbp_core_tests/in_game/common/scripted_effects/cbp_stock_test_effects.txt")
    perf10_13_test_effects = read("packages/cbp_core_tests/in_game/common/scripted_effects/cbp_perf10_13_test_effects.txt")
    us10_ui_effects = read("in_game/common/scripted_effects/cbp_us10_ui_effects.txt")
    us10_lateralview_gui = read("in_game/gui/cbp_us10_stock_lateralview.gui")
    us10_production_subtabs = read("in_game/gui/zz_cbp_us10_production_subtabs.gui")
    stock_loc = read("in_game/localization/cbp_stock_l_english.yml")
    perf14_test_effects = read("packages/cbp_core_tests/in_game/common/scripted_effects/cbp_perf14_test_effects.txt")
    perf14_guarded_test_effects = read("packages/cbp_core_tests/in_game/common/scripted_effects/cbp_perf14_guarded_test_effects.txt")
    core04_test_effects = read("packages/cbp_core_tests/in_game/common/scripted_effects/cbp_core04_test_effects.txt")
    us04_debug_events = read("packages/cbp_core_tests/in_game/events/cbp_us04_debug_events.txt")
    loc = read("main_menu/localization/english/cbp__cmm_l_english.yml")
    economy_on_actions = read("packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt")
    trade_on_actions = read("packages/cbp_trade_rebalance/in_game/common/on_action/cbp_trade_package_on_actions.txt")
    war_on_actions = read("packages/cbp_war_rebalance/in_game/common/on_action/cbp_war_package_on_actions.txt")
    lifecycle_doc = read("docs/technical/GAME_LOAD_LIFECYCLE.md")

    validate_no_legacy_review_pop_id("\n".join([cmm_effects, runtime_effects, scripted_gui, loc, read("in_game/events/cbp_review_events.txt"), read("in_game/common/scripted_effects/cbp_review_effects.txt")]))
    validate_cmm_surface(cmm_effects, runtime_effects, config_triggers, loc, scripted_gui)
    validate_us17_owner_modifier_contract(
        trade_values=trade_values,
        owner_modifier_effects=owner_modifier_effects,
        native_auto_modifiers=native_trade_profit_auto_modifiers,
        country_governance_on_actions=country_governance_on_actions,
        all_cbp_on_actions=all_cbp_on_actions,
        native_localization=native_trade_profit_localization,
        owner_modifier_probe_events=owner_modifier_probe_events,
        owner_modifier_probe_effects=owner_modifier_probe_effects,
    )
    validate_native_trade_quantity_contract(
        country_trade_owner_effects=country_trade_owner_effects,
        transport_helpers=transport_helpers,
    )
    validate_us17_us20_static_contract(
        stock_on_actions=stock_on_actions,
        country_trade_owner_effects=country_trade_owner_effects,
        q8_7_global_owner_effects=q8_7_global_owner_effects,
        trade_reconciliation_effects=trade_reconciliation_effects,
        owner_modifier_effects=owner_modifier_effects,
        revalidate_events=revalidate_events,
        us20_probe_events=us20_probe_events,
        us20_probe_effects=us20_probe_effects,
    )
    validate_us10_test_contract(us10_test_effects)
    validate_us10_ui_widget_contract(
        lateralview_gui=us10_lateralview_gui,
        production_subtabs=us10_production_subtabs,
        ui_effects=us10_ui_effects,
        stock_loc=stock_loc,
    )
    validate_perf14_test_contract(perf14_test_effects + "\n" + perf14_guarded_test_effects, stock_loc)
    validate_core04_test_contract(core04_test_effects)
    validate_us04_debug_event_contract(us04_debug_events)
    validate_core_stock_test_contract(stock_test_effects)
    validate_stock_operator_contract()
    validate_perf10_13_test_contract(perf10_13_test_effects)
    validate_game_load_lifecycle_contract(
        configuration_on_actions=configuration_on_actions,
        configuration_effects=configuration_effects,
        stock_on_actions=stock_on_actions,
        stock_effects=stock_effects,
        core04_effects=core04_effects,
        economy_on_actions=economy_on_actions,
        trade_on_actions=trade_on_actions,
        war_on_actions=war_on_actions,
        lifecycle_doc=lifecycle_doc,
    )

    if failures:
        print("ModeU5 CI static contract validation failed:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("ModeU5 CI static contract validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

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

ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []

CMM_MOD_ID = "no_void_economy"
TRADE_REWORK_SETTING = "nve_general_gameplay_gameplay_trade_rework_settings"
REVIEW_POP_SETTING = "nve_debug_audit_misc_review_pop_settings"
TRADE_REWORK_FLAG = f"flag:{CMM_MOD_ID}__{TRADE_REWORK_SETTING}"
TRADE_REWORK_VALUE_LINK = f'"variable_map(cmm|{TRADE_REWORK_FLAG})" = 1'

CMM_SETTINGS: dict[str, tuple[str, str, bool]] = {
    "nve_general_gameplay_gameplay_war_exhaustion_political_pressure_settings": ("nve_general_gameplay_tab", "nve_general_gameplay_gameplay_group", False),
    TRADE_REWORK_SETTING: ("nve_general_gameplay_tab", "nve_general_gameplay_gameplay_group", True),
    "nve_general_gameplay_gameplay_empire_military_difficulties_settings": ("nve_general_gameplay_tab", "nve_general_gameplay_gameplay_group", False),
    "nve_general_gameplay_country_level_stocks_countries_have_own_stocks_settings": ("nve_general_gameplay_tab", "nve_general_gameplay_country_level_stocks_group", False),
    "nve_general_gameplay_country_level_stocks_only_sold_goods_create_revenue_settings": ("nve_general_gameplay_tab", "nve_general_gameplay_country_level_stocks_group", True),
    "nve_general_gameplay_country_level_stocks_boycotts_wars_block_resource_buying_settings": ("nve_general_gameplay_tab", "nve_general_gameplay_country_level_stocks_group", True),
    "nve_general_gameplay_other_extra_revenue_to_ai_settings": ("nve_general_gameplay_tab", "nve_general_gameplay_other_group", True),
    "nve_economic_balance_design_activate_goods_decay_settings": ("nve_economic_balance_tab", "nve_economic_balance_design_group", True),
    "nve_economic_balance_design_sliders_adjustments_settings": ("nve_economic_balance_tab", "nve_economic_balance_design_group", True),
    "nve_economic_balance_balance_increased_location_specialisation_settings": ("nve_economic_balance_tab", "nve_economic_balance_balance_group", True),
    "nve_economic_balance_balance_marketplace_burgher_power_reduction_settings": ("nve_economic_balance_tab", "nve_economic_balance_balance_group", True),
    "nve_war_subjects_balance_general_difficulty_settings": ("nve_war_subjects_balance_tab", "nve_war_subjects_balance_general_group", True),
    "nve_war_subjects_balance_design_overlord_declares_war_settings": ("nve_war_subjects_balance_tab", "nve_war_subjects_balance_design_group", True),
    "nve_war_subjects_balance_design_persistence_of_resources_settings": ("nve_war_subjects_balance_tab", "nve_war_subjects_balance_design_group", True),
    "nve_war_subjects_balance_balance_shorter_wars_settings": ("nve_war_subjects_balance_tab", "nve_war_subjects_balance_balance_group", True),
    "nve_war_subjects_balance_balance_adjust_rebel_threshold_settings": ("nve_war_subjects_balance_tab", "nve_war_subjects_balance_balance_group", True),
    "nve_debug_audit_debug_audit_debug_messages_settings": ("nve_debug_audit_tab", "nve_debug_audit_debug_audit_group", True),
    "nve_debug_audit_debug_audit_monthly_stock_check_settings": ("nve_debug_audit_tab", "nve_debug_audit_debug_audit_group", True),
    "nve_debug_audit_debug_audit_save_mode_settings": ("nve_debug_audit_tab", "nve_debug_audit_debug_audit_group", True),
    REVIEW_POP_SETTING: ("nve_debug_audit_tab", "nve_debug_audit_misc_group", True),
}

REQUIRED_FILES = [
    ".metadata/metadata.json",
    "in_game/common/on_action/modeu5_stock_on_actions.txt",
    "in_game/common/on_action/nve__cmm_on_actions.txt",
    "in_game/common/on_action/nve_cmm_runtime_on_action.txt",
    "in_game/common/script_values/zzz_trade_reconciliation_values.txt",
    "in_game/common/scripted_effects/nve__cmm_effects.txt",
    "in_game/common/scripted_effects/modeu5_cmm_runtime_effects.txt",
    "in_game/common/scripted_effects/modeu5_configuration_effects.txt",
    "in_game/common/scripted_effects/modeu5_country_trade_owner_effects.txt",
    "in_game/common/scripted_effects/modeu5_performance_effects.txt",
    "in_game/common/scripted_effects/modeu5_q8_7_global_owner_effects.txt",
    "in_game/common/scripted_effects/modeu5_trade_owner_modifier_reconciliation_effects.txt",
    "in_game/common/scripted_effects/zzz_trade_reconciliation_effects.txt",
    "in_game/common/scripted_guis/nve__cmm_scripted_gui.txt",
    "in_game/common/scripted_triggers/modeu5_configuration_triggers.txt",
    "in_game/events/modeu5_cmm_warning_events.txt",
    "packages/modeu5_core_tests/in_game/events/modeu5_revalidate_debug_events.txt",
    "packages/modeu5_core_tests/in_game/events/modeu5_us20_case12_probe_events.txt",
    "packages/modeu5_core_tests/in_game/events/modeu5_us17_owner_modifier_probe_events.txt",
    "packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us20_case12_probe_effects.txt",
    "packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us17_owner_modifier_test_effects.txt",
    "packages/modeu5_core_tests/in_game/localization/modeu5_us17_owner_modifier_probe_l_english.yml",
    "main_menu/localization/english/nve__cmm_l_english.yml",
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
    match = re.search(rf"^\s*{re.escape(field_name)}\s*=\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate_required_files() -> None:
    for path in REQUIRED_FILES:
        expect((ROOT / path).is_file(), f"Required CI/static-contract file is missing: {path}")


def validate_no_legacy_review_pop_id(all_text: str) -> None:
    exact_legacy_lines = [
        r"^\s*setting_id\s*=\s*review_pop\s*$",
        r"^\s*tab_id\s*=\s*nve_general\s*$",
        r"^\s*group_id\s*=\s*nve_no_void_economy\s*$",
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

    runtime_review_pop = block(runtime_effects, "modeu5_cmm_register_review_pop")
    expect(f"setting_id = {REVIEW_POP_SETTING}" in runtime_review_pop, "Runtime review-pop registration must use the standard setting id")
    expect("tab_id = nve_debug_audit_tab" in runtime_review_pop, "Runtime review-pop registration must use the Debug & Audit tab")
    expect("group_id = nve_debug_audit_misc_group" in runtime_review_pop, "Runtime review-pop registration must use the Debug & Audit / Misc group")

    for setting_id, (_tab_id, _group_id, has_scripted_gui) in CMM_SETTINGS.items():
        expect(f"setting_id = {setting_id}" in cmm_effects, f"Missing CMM registration for {setting_id}")
        expect(f"{CMM_MOD_ID}__{setting_id}_name" in loc, f"Missing localization name for {setting_id}")
        expect(f"{CMM_MOD_ID}__{setting_id}_desc" in loc, f"Missing localization description for {setting_id}")
        if has_scripted_gui:
            expect(f"{CMM_MOD_ID}__{setting_id}" in scripted_gui, f"Missing scripted GUI handler for {setting_id}")

    expect("no_void_economy__nve_debug_audit_tab__nve_debug_audit_misc_group_name" in loc, "Missing localization name for Debug & Audit / Misc group")

    trade_trigger = block(config_triggers, "modeu5_trade_rework_enabled_trigger")
    expect("has_variable_map = cmm" in trade_trigger, "Trade rework trigger must require the CMM variable map")
    expect(TRADE_REWORK_FLAG in trade_trigger, "Trade rework trigger must read the normalized CMM trade-rework flag")
    expect(TRADE_REWORK_VALUE_LINK in trade_trigger, "Trade rework trigger must require CMM trade-rework value 1")


def validate_us17_owner_modifier_contract(
    *,
    trade_values: str,
    owner_modifier_effects: str,
    owner_modifier_probe_events: str,
    owner_modifier_probe_effects: str,
) -> None:
    capture = block(owner_modifier_effects, "modeu5_capture_trade_owner_country_modifier_inputs")
    maintenance_formula = block(owner_modifier_effects, "modeu5_compute_trade_maintenance_efficiency_delta_from_owner_modifiers")
    formula = block(owner_modifier_effects, "modeu5_compute_us17_us20_route_formula_from_owner_modifiers")
    live_wrapper = block(owner_modifier_effects, "modeu5_run_us17_us20_route_reconciliation_from_owner_modifiers")

    for semantic_name, modifier_name in [
        ("buying/import efficiency", "import_efficiency"),
        ("selling efficiency", "selling_efficiency"),
        ("merchant maintenance efficiency", "merchant_maintenance_efficiency"),
    ]:
        expect(
            f"value = modifier:{modifier_name}" in trade_values,
            f"US17 must define a country-scoped script value for {semantic_name} via modifier:{modifier_name}",
        )

    expect(
        "value = define:NCountry|MERCHANT_MAINTENANCE_COST" in trade_values,
        "US17 must read the effective NCountry MERCHANT_MAINTENANCE_COST define",
    )
    expect("gui_cbp_trade_efficiency_buying_efficiency" in capture, "US17 owner capture must store semantic buying/import efficiency")
    expect("gui_cbp_trade_efficiency_selling_efficiency" in capture, "US17 owner capture must store selling efficiency")
    expect("gui_cbp_trade_efficiency_merchant_maintenance_efficiency" in capture, "US17 owner capture must store merchant maintenance efficiency")
    expect("gui_cbp_trade_efficiency_base_maintenance_unit_cost" in capture, "US17 owner capture must store the effective maintenance define")
    expect("gui_cbp_trade_efficiency_base_maintenance_amount" in capture, "US17 owner capture must derive route base maintenance")
    expect("scope:cbp_trade_owner_trade_volume" in capture, "US17 base maintenance must use route trade volume")
    expect("cbp_trade_efficiency_country_modifier_inputs_available" in capture, "US17 owner capture must expose an availability marker")

    average_assignment = re.search(
        r"name\s*=\s*modeu5_buying_selling_efficiency_clamped(?P<body>.*?)(?:\n\s*\}|\n\s*save_temporary_scope_value_as)",
        formula,
        re.DOTALL,
    )
    average_body = average_assignment.group("body") if average_assignment else ""
    expect(bool(average_assignment), "US17 owner formula must calculate the buying/selling average")
    expect("max = 1" in average_body, "US17 buying/selling average must have an upper cap of 1")
    expect("min = 0" not in average_body, "US17 buying/selling average must not have a lower clamp of 0")

    expect("gui_cbp_trade_efficiency_merchant_maintenance_efficiency" in maintenance_formula, "US17 maintenance helper must consume merchant maintenance efficiency")
    expect("multiply = -1" in maintenance_formula, "US17 maintenance factor must subtract merchant maintenance efficiency")
    expect("min = 0" in maintenance_formula, "US17 maintenance factor must not become negative")
    expect("gui_cbp_trade_efficiency_base_maintenance_amount" in maintenance_formula, "US17 maintenance helper must consume define-derived route base maintenance")
    expect("modeu5_compute_trade_maintenance_efficiency_delta_from_owner_modifiers = yes" in formula, "US17 formula must calculate maintenance saving from owner modifiers")
    expect("modeu5_trade_rework_enabled_trigger = yes" in live_wrapper, "US17 owner-modifier wrapper must defensively gate itself")

    expect("namespace = modeu5_us17_owner_modifiers" in owner_modifier_probe_events, "US17 owner-modifier probe namespace must remain available")
    expect("modeu5_us17_owner_modifiers.1" in owner_modifier_probe_events, "US17 owner-modifier probe entry event must remain available")
    expect("modeu5_debug_run_us17_owner_modifier_probe = yes" in owner_modifier_probe_events, "US17 owner-modifier event must call the focused probe")

    for assertion in [
        "import_efficiency_source",
        "selling_efficiency_source",
        "merchant_maintenance_efficiency_source",
        "base_maintenance_define_source",
        "base_maintenance_amount",
        "negative_average_preserved",
        "positive_average_capped",
        "merchant_maintenance_factor",
        "maintenance_saving",
        "route_money_delta",
        "base_cost=define_NCountry_MERCHANT_MAINTENANCE_COST",
        "clamp=maximum_only",
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
    country_cycle = block(country_trade_owner_effects, "modeu5_run_monthly_country_trade_owner_cycle")
    route_effect = block(trade_reconciliation_effects, "modeu5_run_us17_us20_route_reconciliation")
    live_hook_call = "modeu5_run_us17_us20_route_reconciliation_from_owner_modifiers = yes"
    legacy_hook_call = "modeu5_run_us17_us20_route_reconciliation = yes"
    e2e_probe_call = "modeu5_debug_run_us20_case12_market_loss_probe = yes"

    expect(country_cycle.count(live_hook_call) == 1, "Country trade-owner cycle must call the owner-modifier US-17/US-20 reconciliation exactly once")
    expect(legacy_hook_call not in country_cycle, "Country trade-owner live cycle must not call the historical seeded reconciliation wrapper")
    expect("modeu5_capture_trade_owner_country_modifier_inputs = yes" in country_cycle, "Country trade-owner cycle must capture modifiers in saved owner scope before reconciliation")
    expect("every_trade = {" in country_cycle, "Country trade-owner cycle must use the native every_trade loop")
    expect("modeu5_trade_rework_enabled_trigger = yes" in route_effect, "Historical US-17/US-20 route effect must remain defensively gated for deterministic tests")
    expect("modeu5_prepare_trade_efficiency_reconciliation_runtime_metrics_once = yes" in route_effect, "Historical US-17/US-20 route effect must prepare metrics inside the gated body")
    expect(live_hook_call not in q8_7_global_owner_effects, "US-17/US-20 live hook must not be placed in the Q8.7 market-local body")
    expect(live_hook_call not in stock_on_actions, "US-17/US-20 live hook must not be placed directly in monthly on_actions")
    expect(
        "every_market_center_in_country = {" not in country_trade_owner_effects + q8_7_global_owner_effects + trade_reconciliation_effects + owner_modifier_effects,
        "Trade-rework runtime must not reintroduce a market-center every_trade scaffold",
    )

    unsafe_global_counter = re.compile(
        r"set_global_variable\s*=\s*\{[^{}]*name\s*=\s*modeu5_(?:trade_efficiency|us20)[^{}]*value\s*=\s*\{\s*value\s*=\s*global_var:",
        re.DOTALL,
    )
    expect(
        unsafe_global_counter.search(trade_reconciliation_effects + owner_modifier_effects) is None,
        "US17/US20 counters must not use set_global_variable value={ value=global_var:X add=1 }; use if-unset/set-1 else change_global_variable",
    )
    expect("change_global_variable = { name = cbp_trade_efficiency_routes_seen add = 1 }" in trade_reconciliation_effects, "Route-seen counter must use change_global_variable after first set")
    expect("change_global_variable = { name = cbp_us20_market_goods_supply_loss_routes add = 1 }" in trade_reconciliation_effects, "US20 market-loss counter must use change_global_variable after first set")

    expect("goods = scope:modeu5_trade_owner_good" in trade_reconciliation_effects, "US20 market loss must use the saved route good scope")
    expect("amount = scope:gui_cbp_us20_market_goods_supply_delta" in trade_reconciliation_effects, "US20 market loss must use the computed negative market goods delta")
    expect("modeu5_select_us20_goods_receiver_country_for_promoted_market = yes" in trade_reconciliation_effects, "Promoted-destination loss must select a receiver before country-stock loss")

    expect(e2e_probe_call not in revalidate_events, "Experimental US20 E2E probe must stay outside stable full revalidation")
    expect("Step 13/13" in revalidate_events, "Stable full revalidation must end at the US17/US20 route-reconciliation scenario")
    expect(e2e_probe_call in us20_probe_events, "Standalone US20 probe event must call the US20 E2E probe explicitly")
    expect("namespace = modeu5_us20_probe" in us20_probe_events, "Standalone US20 probe event namespace must remain available")
    expect("modeu5_us20_probe.1" in us20_probe_events, "Standalone US20 probe entry event must remain available")

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


def main() -> int:
    validate_required_files()
    if failures:
        return 1

    metadata = json.loads(read(".metadata/metadata.json"))
    expect(metadata.get("id") == "modeu5_core", "Core metadata id must remain modeu5_core")
    expect(
        any(item.get("id") == "community_mod_framework" for item in metadata.get("relationships", [])),
        "Core package must declare CMF as a required dependency",
    )

    stock_on_actions = read("in_game/common/on_action/modeu5_stock_on_actions.txt")
    trade_values = read("in_game/common/script_values/zzz_trade_reconciliation_values.txt")
    cmm_effects = read("in_game/common/scripted_effects/nve__cmm_effects.txt")
    runtime_effects = read("in_game/common/scripted_effects/modeu5_cmm_runtime_effects.txt")
    scripted_gui = read("in_game/common/scripted_guis/nve__cmm_scripted_gui.txt")
    config_triggers = read("in_game/common/scripted_triggers/modeu5_configuration_triggers.txt")
    country_trade_owner_effects = read("in_game/common/scripted_effects/modeu5_country_trade_owner_effects.txt")
    q8_7_global_owner_effects = read("in_game/common/scripted_effects/modeu5_q8_7_global_owner_effects.txt")
    trade_reconciliation_effects = read("in_game/common/scripted_effects/zzz_trade_reconciliation_effects.txt")
    owner_modifier_effects = read("in_game/common/scripted_effects/modeu5_trade_owner_modifier_reconciliation_effects.txt")
    revalidate_events = read("packages/modeu5_core_tests/in_game/events/modeu5_revalidate_debug_events.txt")
    us20_probe_events = read("packages/modeu5_core_tests/in_game/events/modeu5_us20_case12_probe_events.txt")
    us20_probe_effects = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us20_case12_probe_effects.txt")
    owner_modifier_probe_events = read("packages/modeu5_core_tests/in_game/events/modeu5_us17_owner_modifier_probe_events.txt")
    owner_modifier_probe_effects = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us17_owner_modifier_test_effects.txt")
    loc = read("main_menu/localization/english/nve__cmm_l_english.yml")

    validate_no_legacy_review_pop_id("\n".join([cmm_effects, runtime_effects, scripted_gui, loc, read("in_game/events/modeu5_review_events.txt"), read("in_game/common/scripted_effects/modeu5_review_effects.txt")]))
    validate_cmm_surface(cmm_effects, runtime_effects, config_triggers, loc, scripted_gui)
    validate_us17_owner_modifier_contract(
        trade_values=trade_values,
        owner_modifier_effects=owner_modifier_effects,
        owner_modifier_probe_events=owner_modifier_probe_events,
        owner_modifier_probe_effects=owner_modifier_probe_effects,
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

    if failures:
        print("ModeU5 CI static contract validation failed:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("ModeU5 CI static contract validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Static validation for the ModeU5 CMF/CMM configuration surface.

This validator intentionally checks the stable contract between CMM settings,
local generated runtime configuration, and safe runtime gates. It complements
specialised shell validators for package layout, generated files, persistent
state, and CMM value-link quoting.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []

CMM_MOD_ID = "no_void_economy"
CMM_PREFIX = "nve"

# Naming convention:
#   tab:     <prefix>_<tabname>_tab
#   group:   <prefix>_<tabname>_<groupname>_group
#   setting: <prefix>_<tabname>_<groupname>_<settingname>_settings
CMM_TABS: dict[str, str] = {
    "nve_general_gameplay_tab": "general_gameplay",
    "nve_economic_balance_tab": "economic_balance",
    "nve_war_subjects_balance_tab": "war_subjects_balance",
    "nve_debug_audit_tab": "debug_audit",
}

CMM_GROUPS: dict[str, tuple[str, str]] = {
    "nve_general_gameplay_gameplay_group": ("nve_general_gameplay_tab", "gameplay"),
    "nve_general_gameplay_country_level_stocks_group": ("nve_general_gameplay_tab", "country_level_stocks"),
    "nve_general_gameplay_other_group": ("nve_general_gameplay_tab", "other"),
    "nve_economic_balance_design_group": ("nve_economic_balance_tab", "design"),
    "nve_economic_balance_balance_group": ("nve_economic_balance_tab", "balance"),
    "nve_war_subjects_balance_general_group": ("nve_war_subjects_balance_tab", "general"),
    "nve_war_subjects_balance_design_group": ("nve_war_subjects_balance_tab", "design"),
    "nve_war_subjects_balance_balance_group": ("nve_war_subjects_balance_tab", "balance"),
    "nve_debug_audit_debug_audit_group": ("nve_debug_audit_tab", "debug_audit"),
}

CMM_SETTINGS: dict[str, tuple[str, str, str, bool]] = {
    "nve_general_gameplay_gameplay_war_exhaustion_political_pressure_settings": (
        "nve_general_gameplay_tab",
        "nve_general_gameplay_gameplay_group",
        "war_exhaustion_political_pressure",
        False,
    ),
    "nve_general_gameplay_gameplay_trade_rework_settings": (
        "nve_general_gameplay_tab",
        "nve_general_gameplay_gameplay_group",
        "trade_rework",
        True,
    ),
    "nve_general_gameplay_gameplay_empire_military_difficulties_settings": (
        "nve_general_gameplay_tab",
        "nve_general_gameplay_gameplay_group",
        "empire_military_difficulties",
        False,
    ),
    "nve_general_gameplay_country_level_stocks_countries_have_own_stocks_settings": (
        "nve_general_gameplay_tab",
        "nve_general_gameplay_country_level_stocks_group",
        "countries_have_own_stocks",
        False,
    ),
    "nve_general_gameplay_country_level_stocks_only_sold_goods_create_revenue_settings": (
        "nve_general_gameplay_tab",
        "nve_general_gameplay_country_level_stocks_group",
        "only_sold_goods_create_revenue",
        True,
    ),
    "nve_general_gameplay_country_level_stocks_boycotts_wars_block_resource_buying_settings": (
        "nve_general_gameplay_tab",
        "nve_general_gameplay_country_level_stocks_group",
        "boycotts_wars_block_resource_buying",
        True,
    ),
    "nve_general_gameplay_other_extra_revenue_to_ai_settings": (
        "nve_general_gameplay_tab",
        "nve_general_gameplay_other_group",
        "extra_revenue_to_ai",
        True,
    ),
    "nve_economic_balance_design_activate_goods_decay_settings": (
        "nve_economic_balance_tab",
        "nve_economic_balance_design_group",
        "activate_goods_decay",
        True,
    ),
    "nve_economic_balance_design_sliders_adjustments_settings": (
        "nve_economic_balance_tab",
        "nve_economic_balance_design_group",
        "sliders_adjustments",
        True,
    ),
    "nve_economic_balance_balance_increased_location_specialisation_settings": (
        "nve_economic_balance_tab",
        "nve_economic_balance_balance_group",
        "increased_location_specialisation",
        True,
    ),
    "nve_economic_balance_balance_marketplace_burgher_power_reduction_settings": (
        "nve_economic_balance_tab",
        "nve_economic_balance_balance_group",
        "marketplace_burgher_power_reduction",
        True,
    ),
    "nve_war_subjects_balance_general_difficulty_settings": (
        "nve_war_subjects_balance_tab",
        "nve_war_subjects_balance_general_group",
        "difficulty",
        True,
    ),
    "nve_war_subjects_balance_design_overlord_declares_war_settings": (
        "nve_war_subjects_balance_tab",
        "nve_war_subjects_balance_design_group",
        "overlord_declares_war",
        True,
    ),
    "nve_war_subjects_balance_design_persistence_of_resources_settings": (
        "nve_war_subjects_balance_tab",
        "nve_war_subjects_balance_design_group",
        "persistence_of_resources",
        True,
    ),
    "nve_war_subjects_balance_balance_shorter_wars_settings": (
        "nve_war_subjects_balance_tab",
        "nve_war_subjects_balance_balance_group",
        "shorter_wars",
        True,
    ),
    "nve_war_subjects_balance_balance_adjust_rebel_threshold_settings": (
        "nve_war_subjects_balance_tab",
        "nve_war_subjects_balance_balance_group",
        "adjust_rebel_threshold",
        True,
    ),
    "nve_debug_audit_debug_audit_debug_messages_settings": (
        "nve_debug_audit_tab",
        "nve_debug_audit_debug_audit_group",
        "debug_messages",
        True,
    ),
    "nve_debug_audit_debug_audit_monthly_stock_check_settings": (
        "nve_debug_audit_tab",
        "nve_debug_audit_debug_audit_group",
        "monthly_stock_check",
        True,
    ),
    "nve_debug_audit_debug_audit_save_mode_settings": (
        "nve_debug_audit_tab",
        "nve_debug_audit_debug_audit_group",
        "save_mode",
        True,
    ),
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


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


def validate_cmm_identifier_catalog() -> None:
    for tab_id, tab_name in CMM_TABS.items():
        expected_tab_id = f"{CMM_PREFIX}_{tab_name}_tab"
        expect(tab_id == expected_tab_id, f"CMM tab id {tab_id} must be {expected_tab_id}")
        expect(tab_id.endswith("_tab"), f"CMM tab id {tab_id} must end with _tab")

    for group_id, (tab_id, group_name) in CMM_GROUPS.items():
        tab_name = CMM_TABS[tab_id]
        expected_group_id = f"{CMM_PREFIX}_{tab_name}_{group_name}_group"
        expect(group_id == expected_group_id, f"CMM group id {group_id} must be {expected_group_id}")
        expect(group_id.endswith("_group"), f"CMM group id {group_id} must end with _group")

    for setting_id, (tab_id, group_id, setting_name, _has_scripted_gui) in CMM_SETTINGS.items():
        tab_name = CMM_TABS[tab_id]
        group_name = CMM_GROUPS[group_id][1]
        expected_setting_id = f"{CMM_PREFIX}_{tab_name}_{group_name}_{setting_name}_settings"
        expect(setting_id == expected_setting_id, f"CMM setting id {setting_id} must be {expected_setting_id}")
        expect(setting_id.endswith("_settings"), f"CMM setting id {setting_id} must end with _settings")


def validate_cmm_registration_ids(cmm_effects: str) -> None:
    blank_assignments = re.findall(r"^\s*(setting_id|tab_id|group_id)\s*=\s*$", cmm_effects, flags=re.MULTILINE)
    for field_name in blank_assignments:
        failures.append(f"CMM {field_name} must not be blank")

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

        expect(setting_id in CMM_SETTINGS, f"Unexpected CMM setting id in registration: {setting_id or '<blank>'}")
        expect(tab_id in CMM_TABS, f"Unexpected CMM tab id in registration for {setting_id or '<blank>'}: {tab_id or '<blank>'}")
        expect(group_id in CMM_GROUPS, f"Unexpected CMM group id in registration for {setting_id or '<blank>'}: {group_id or '<blank>'}")
        if setting_id in CMM_SETTINGS:
            expected_tab_id, expected_group_id, _setting_name, _has_scripted_gui = CMM_SETTINGS[setting_id]
            expect(tab_id == expected_tab_id, f"CMM setting {setting_id} must use tab_id {expected_tab_id}, found {tab_id or '<blank>'}")
            expect(group_id == expected_group_id, f"CMM setting {setting_id} must use group_id {expected_group_id}, found {group_id or '<blank>'}")

    expect(registered_settings == set(CMM_SETTINGS), "CMM registrations must match the expected CMM setting catalog")

    for tab_id in re.findall(r"^\s*tab_id\s*=\s*(\S+)\s*$", cmm_effects, flags=re.MULTILINE):
        expect(tab_id.endswith("_tab"), f"CMM tab id {tab_id} must end with _tab")
    for group_id in re.findall(r"^\s*group_id\s*=\s*(\S+)\s*$", cmm_effects, flags=re.MULTILINE):
        expect(group_id.endswith("_group"), f"CMM group id {group_id} must end with _group")
    for setting_id in re.findall(r"^\s*setting_id\s*=\s*(\S+)\s*$", cmm_effects, flags=re.MULTILINE):
        expect(setting_id.endswith("_settings"), f"CMM setting id {setting_id} must end with _settings")


required_files = [
    ".metadata/metadata.json",
    "in_game/common/on_action/nve__cmm_on_actions.txt",
    "in_game/common/on_action/nve_cmm_runtime_on_action.txt",
    "in_game/common/scripted_effects/nve__cmm_effects.txt",
    "in_game/common/scripted_effects/modeu5_cmm_runtime_effects.txt",
    "in_game/common/scripted_effects/modeu5_configuration_effects.txt",
    "in_game/common/scripted_effects/modeu5_performance_effects.txt",
    "in_game/common/scripted_guis/nve__cmm_scripted_gui.txt",
    "in_game/common/scripted_triggers/modeu5_configuration_triggers.txt",
    "in_game/events/modeu5_cmm_warning_events.txt",
    "main_menu/localization/english/nve__cmm_l_english.yml",
]
for path in required_files:
    expect((ROOT / path).is_file(), f"Required CMM/configuration file is missing: {path}")

if failures:
    for item in failures:
        print(f"FAIL: {item}", file=sys.stderr)
    sys.exit(1)

metadata = json.loads(read(".metadata/metadata.json"))
expect(metadata.get("id") == "modeu5_core", "Core metadata id must remain modeu5_core")
expect(
    any(item.get("id") == "community_mod_framework" for item in metadata.get("relationships", [])),
    "Core package must declare CMF as a required dependency",
)

on_actions = read("in_game/common/on_action/nve__cmm_on_actions.txt")
runtime_on_actions = read("in_game/common/on_action/nve_cmm_runtime_on_action.txt")
cmm_effects = read("in_game/common/scripted_effects/nve__cmm_effects.txt")
runtime_effects = read("in_game/common/scripted_effects/modeu5_cmm_runtime_effects.txt")
scripted_gui = read("in_game/common/scripted_guis/nve__cmm_scripted_gui.txt")
config_effects = read("in_game/common/scripted_effects/modeu5_configuration_effects.txt")
config_triggers = read("in_game/common/scripted_triggers/modeu5_configuration_triggers.txt")
performance_effects = read("in_game/common/scripted_effects/modeu5_performance_effects.txt")
warning_events = read("in_game/events/modeu5_cmm_warning_events.txt")
loc = read("main_menu/localization/english/nve__cmm_l_english.yml")

validate_cmm_identifier_catalog()
validate_cmm_registration_ids(cmm_effects)

expect("nve__on_register_cmf_mod" in on_actions, "CMM registration on_action must call nve__on_register_cmf_mod")
expect("nve__on_cmf_callback" in on_actions, "CMM callback on_action must call nve__on_cmf_callback")
expect("modeu5_cmm_runtime_registration_pulse" in runtime_on_actions, "Runtime CMM overlay must hook CMF registration")
expect("modeu5_cmm_runtime_callback_pulse" in runtime_on_actions, "Runtime CMM overlay must hook CMF callback")
expect("modeu5_cmm_refresh_nve_main_enabled = yes" in runtime_on_actions, "Runtime registration must refresh CMM main-mode visibility")

expected_settings = list(CMM_SETTINGS)
scripted_gui_settings = [setting for setting, values in CMM_SETTINGS.items() if values[3]]
main_dropdown_setting = "nve_general_gameplay_country_level_stocks_countries_have_own_stocks_settings"
for tab_id in CMM_TABS:
    expect(f"{CMM_MOD_ID}__{tab_id}_name" in loc, f"Missing localization name for CMM tab {tab_id}")
for group_id, (tab_id, _group_name) in CMM_GROUPS.items():
    expect(f"{CMM_MOD_ID}__{tab_id}__{group_id}_name" in loc, f"Missing localization name for CMM group {group_id}")
for setting in expected_settings:
    expect(f"setting_id = {setting}" in cmm_effects, f"Missing CMM registration for {setting}")
    expect(f"{CMM_MOD_ID}__{setting}_name" in loc, f"Missing localization name for {setting}")
    expect(f"{CMM_MOD_ID}__{setting}_desc" in loc, f"Missing localization description for {setting}")
for setting in scripted_gui_settings:
    expect(f"{CMM_MOD_ID}__{setting}" in scripted_gui, f"Missing scripted GUI handler for {setting}")
expect(f"{CMM_MOD_ID}__{main_dropdown_setting}" in cmm_effects, "Main NVE dropdown must use the normalized CMM setting id")

for text_path, text in {
    "configuration effects": config_effects,
    "configuration triggers": config_triggers,
    "runtime CMM effects": runtime_effects,
    "scripted GUI": scripted_gui,
}.items():
    expect('variable_map(cmm|flag:' not in text.replace('"variable_map(cmm|flag:', ''), f"{text_path} must not use unquoted CMM value links")

init_block = block(config_effects, "modeu5_initialize_configuration_state_effect")
refresh_block = block(config_effects, "modeu5_refresh_configuration_from_cmm_country_scope")
expect("modeu5_apply_generated_local_runtime_mode = yes" in init_block, "Initialization must apply generated local runtime mode")
expect("modeu5_apply_generated_local_runtime_mode = yes" in refresh_block, "Default CMM debug path must reapply generated local runtime mode")
expect("modeu5_debug_level" in refresh_block and "value = 0" in refresh_block, "Default CMM debug path must set debug level 0")
expect("modeu5_enter_debug_runtime_mode = yes" in refresh_block and "value = 2" in refresh_block, "Detailed debug CMM value must derive debug level 2")
expect("modeu5_enter_debug_runtime_mode = yes" in refresh_block and "value = 1" in refresh_block, "Basic debug CMM value must derive debug level 1")
expect("modeu5_enter_test_audit_runtime_mode = yes" in refresh_block and "modeu5_enter_audit_runtime_mode = yes" in refresh_block, "Monthly stock check must enable audit mode")
expect("modeu5_enter_strict_accounting_persistence = yes" in refresh_block, "Complete save value must derive strict persistence")
expect("modeu5_enter_human_relevant_accounting_persistence = yes" in refresh_block, "Balanced save value must derive human-relevant persistence")
expect("modeu5_enter_minimal_accounting_persistence = yes" in init_block and "modeu5_enter_minimal_accounting_persistence = yes" in refresh_block, "Default save mode must derive minimal persistence")
expect("modeu5_refresh_nve_main_mode_from_cmm_country_scope = yes" in refresh_block, "Configuration refresh must derive main NVE mode from CMM")
expect("modeu5_prepare_performance_mode_human_relevant_markets = yes" in init_block and "modeu5_prepare_performance_mode_human_relevant_markets = yes" in refresh_block, "Performance Mode must prepare human-relevant markets")
expect(f"flag:{CMM_MOD_ID}__{main_dropdown_setting}" in config_effects + runtime_effects, "Runtime CMM readers must use the normalized main NVE dropdown id")
expect(f"flag:{CMM_MOD_ID}__nve_debug_audit_debug_audit_debug_messages_settings" in config_effects + runtime_effects, "Runtime CMM readers must use the normalized debug setting id")
expect(f"flag:{CMM_MOD_ID}__nve_debug_audit_debug_audit_monthly_stock_check_settings" in config_effects + runtime_effects, "Runtime CMM readers must use the normalized monthly stock check setting id")
expect(f"flag:{CMM_MOD_ID}__nve_debug_audit_debug_audit_save_mode_settings" in config_effects + runtime_effects, "Runtime CMM readers must use the normalized save mode setting id")

for trigger in [
    "modeu5_performance_mode_enabled_trigger",
    "modeu5_nve_normal_mode_trigger",
    "modeu5_nve_deactivated_trigger",
    "modeu5_detailed_country_market_accounting_enabled_trigger",
    "modeu5_market_level_fallback_required_trigger",
    "modeu5_us00_full_ledger_persistence_allowed_trigger",
    "modeu5_full_validation_allowed_trigger",
]:
    expect(trigger in config_triggers, f"Configuration triggers must expose {trigger}")

expect("modeu5_audit_enabled_trigger" in block(config_triggers, "modeu5_full_validation_allowed_trigger"), "Full validation must be gated by audit mode")
for gate in [
    "modeu5_accounting_strict_persistence_trigger",
    "modeu5_human_relevant_full_ledger_market_trigger",
    "modeu5_debug_enabled_trigger",
    "modeu5_audit_enabled_trigger",
]:
    expect(gate in block(config_triggers, "modeu5_us00_full_ledger_persistence_allowed_trigger"), f"Full US-00 ledger gate must include {gate}")

expect("modeu5_accounting_human_relevant_persistence_trigger" in block(performance_effects, "modeu5_prepare_human_relevant_full_ledger_markets"), "Human-relevant full ledger rebuild must be gated")
expect("modeu5_rebuild_human_relevant_markets = yes" in performance_effects, "Human-relevant persistence must rebuild relevant markets when stale")
expect("trigger_event_non_silently = modeu5_cmm_warning.2" in runtime_effects, "Monthly stock check callback must warn")
expect("trigger_event_non_silently = modeu5_cmm_warning.3" in runtime_effects, "Complete save callback must warn")
expect("modeu5_cmm_warning.2" in warning_events and "modeu5_cmm_warning.3" in warning_events, "Slow warning events must exist")
expect("Warning" in loc, "Slow CMM options must be visibly marked with warnings")
expect("no_void_economy___" not in loc, "CMM localization must not contain empty identifier keys")
expect(not (ROOT / "main_menu/common/game_rules/modeu5_game_rules.txt").exists(), "Legacy ModeU5 game-rule configuration must stay removed")
expect("has_game_rule = modeu5_" not in config_effects + config_triggers, "Configuration must not read legacy ModeU5 game rules")

for path in ("in_game", "main_menu"):
    combined = "\n".join(
        p.read_text(encoding="utf-8-sig", errors="ignore")
        for p in (ROOT / path).rglob("*")
        if p.is_file() and p.suffix in {".txt", ".yml"}
    )
    expect("modeu5_debug_configuration" not in combined and "modeu5_audit_configuration" not in combined, f"Legacy debug/audit game-rule identifiers must not remain under {path}")

if failures:
    print("ModeU5 CMM configuration validation failed:", file=sys.stderr)
    for item in failures:
        print(f"- {item}", file=sys.stderr)
    sys.exit(1)

print("ModeU5 CMM configuration validation passed")
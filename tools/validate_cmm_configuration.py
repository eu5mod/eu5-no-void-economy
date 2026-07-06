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

expect("nve__on_register_cmf_mod" in on_actions, "CMM registration on_action must call nve__on_register_cmf_mod")
expect("nve__on_cmf_callback" in on_actions, "CMM callback on_action must call nve__on_cmf_callback")
expect("modeu5_cmm_runtime_registration_pulse" in runtime_on_actions, "Runtime CMM overlay must hook CMF registration")
expect("modeu5_cmm_runtime_callback_pulse" in runtime_on_actions, "Runtime CMM overlay must hook CMF callback")
expect("modeu5_cmm_refresh_nve_main_enabled = yes" in runtime_on_actions, "Runtime registration must refresh CMM main-mode visibility")

expected_settings = [
    "nve_no_void_economy_main",
    "nve_debug_messages",
    "nve_monthly_stock_check",
    "nve_save_mode",
    "nve_balance_difficulty",
    "nve_decay_activate",
    "activate_trade_cost",
    "nve_balance_war_shorter",
    "nve_balance_war_exhaustion",
    "nve_balance_economy_location_specialisation",
    "nve_balance_economy_main_balance",
    "nve_balance_ai_strategy",
    "nve_rebel_threshold",
    "nve_rebel_war_start",
    "nve_subjects_persistance",
]
for setting in expected_settings:
    expect(f"setting_id = {setting}" in cmm_effects, f"Missing CMM registration for {setting}")
    expect(f"no_void_economy__{setting}" in scripted_gui, f"Missing scripted GUI handler for {setting}")
    expect(f"no_void_economy__{setting}_name" in loc, f"Missing localization name for {setting}")
    expect(f"no_void_economy__{setting}_desc" in loc, f"Missing localization description for {setting}")

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

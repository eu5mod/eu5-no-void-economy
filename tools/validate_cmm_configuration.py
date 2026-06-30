#!/usr/bin/env python3
"""Static validation for the ModeU5 CMF/CMM configuration surface.

The PR still needs in-game smoke tests, but this file turns the repeatable parts
of the manual CMM test plan into CI checks:

* CMF is a required dependency, while NVE optionality remains service-level.
* CMM settings map to safe runtime/debug/audit/save defaults.
* Planned services remain restricted/silent no-op until implementation stories land.
* CMM callbacks do not mutate gameplay stock/capacity/demand state directly.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def fail(message: str) -> None:
    failures.append(message)


def expect(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def iter_named_blocks(text: str, name: str):
    pattern = re.compile(rf"(?<![A-Za-z0-9_.]){re.escape(name)}\s*=\s*\{{")
    for match in pattern.finditer(text):
        open_brace = text.find("{", match.start())
        depth = 0
        in_quote = False
        escape = False
        for index in range(open_brace, len(text)):
            char = text[index]
            if char == "\\" and in_quote:
                escape = not escape
                continue
            if char == '"' and not escape:
                in_quote = not in_quote
            if not in_quote:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        yield text[match.start() : index + 1]
                        break
            escape = False


def top_level_block(text: str, name: str) -> str:
    for block in iter_named_blocks(text, name):
        start = text.find(block)
        line_start = text.rfind("\n", 0, start) + 1
        if text[line_start:start].strip() == "":
            return block
    fail(f"Missing top-level block: {name}")
    return ""


def key_value(block: str, key: str) -> str | None:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*([A-Za-z0-9_.:|+-]+)", block)
    return match.group(1) if match else None


def parse_setting_blocks(text: str, block_name: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for block in iter_named_blocks(text, block_name):
        setting_id = key_value(block, "setting_id")
        if setting_id:
            result[setting_id] = {
                "mod_id": key_value(block, "mod_id") or "",
                "tab_id": key_value(block, "tab_id") or "",
                "group_id": key_value(block, "group_id") or "",
                "default_index": key_value(block, "default_index") or "",
                "default_value": key_value(block, "default_value") or "",
                "option_count": key_value(block, "option_count") or "",
            }
    return result


def localization_keys(text: str) -> set[str]:
    return set(re.findall(r"^\s*([A-Za-z0-9_.]+):", text, re.M))


def localization_value(text: str, key: str) -> str:
    match = re.search(rf'^\s*{re.escape(key)}:\s*"(.*)"\s*$', text, re.M)
    return match.group(1) if match else ""


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
for relative_path in required_files:
    expect((ROOT / relative_path).is_file(), f"Required CMM/configuration file is missing: {relative_path}")

if failures:
    for item in failures:
        print(f"FAIL: {item}", file=sys.stderr)
    sys.exit(1)

metadata = json.loads(read(".metadata/metadata.json"))
expect(metadata.get("id") == "modeu5_core", "Core metadata id must remain modeu5_core")
expect(
    metadata.get("relationships")
    == [
        {
            "rel_type": "dependency",
            "id": "community_mod_framework",
            "display_name": "Community Mod Framework",
            "resource_type": "mod",
            "version": "2.*",
        }
    ],
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

expect(re.search(r"cmf_on_mod_registration\s*=\s*\{.*nve__on_register_cmf_mod", on_actions, re.S) is not None,
       "CMM registration on_action must call nve__on_register_cmf_mod")
expect(re.search(r"cmf_on_callback\s*=\s*\{.*nve__on_cmf_callback", on_actions, re.S) is not None,
       "CMM callback on_action must call nve__on_cmf_callback")
expect(re.search(r"nve__on_register_cmf_mod\s*=\s*\{.*nve__register_cmf_mod\s*=\s*yes", on_actions, re.S) is not None,
       "nve__on_register_cmf_mod must call nve__register_cmf_mod")
expect(re.search(r"nve__on_cmf_callback\s*=\s*\{.*nve__handle_cmf_callback\s*=\s*yes", on_actions, re.S) is not None,
       "nve__on_cmf_callback must call nve__handle_cmf_callback")
expect(re.search(r"cmf_on_mod_registration\s*=\s*\{.*modeu5_cmm_runtime_registration_pulse", runtime_on_actions, re.S) is not None,
       "Runtime CMM overlay must hook cmf_on_mod_registration")
expect(re.search(r"modeu5_cmm_runtime_registration_pulse\s*=\s*\{.*modeu5_cmm_mark_planned_services_restricted\s*=\s*yes", runtime_on_actions, re.S) is not None,
       "Runtime CMM registration pulse must mark planned services restricted")
expect(re.search(r"cmf_on_callback\s*=\s*\{.*modeu5_cmm_runtime_callback_pulse", runtime_on_actions, re.S) is not None,
       "Runtime CMM overlay must hook cmf_on_callback")
expect(re.search(r"modeu5_cmm_runtime_callback_pulse\s*=\s*\{.*modeu5_handle_cmm_runtime_callback\s*=\s*yes", runtime_on_actions, re.S) is not None,
       "Runtime CMM callback pulse must call modeu5_handle_cmm_runtime_callback")
expect("modeu5_cmm_refresh_nve_main_enabled = yes" in runtime_on_actions,
       "Runtime registration pulse must refresh modeu5_cmm_nve_main_enabled at startup")

expected_dropdowns = {
    "nve_no_void_economy_main": ("nve_general", "nve_no_void_economy", "1", "3"),
    "nve_debug_messages": ("nve_general", "nve_general_performance", "1", "3"),
    "nve_monthly_stock_check": ("nve_general", "nve_general_performance", "1", "2"),
    "nve_save_mode": ("nve_general", "nve_general_performance", "1", "3"),
    "nve_balance_difficulty": ("nve_balance", "nve_balance_general", "1", "2"),
}
expected_bools = {
    "nve_decay_activate": ("nve_general", "nve_no_void_economy", "0"),
    "activate_trade_cost": ("nve_general", "nve_general_trade_rework", "0"),
    "nve_balance_war_shorter": ("nve_balance", "nve_balance_war", "0"),
    "nve_balance_war_exhaustion": ("nve_balance", "nve_balance_war", "0"),
    "nve_balance_economy_location_specialisation": ("nve_balance", "nve_balance_economy", "0"),
    "nve_balance_economy_main_balance": ("nve_balance", "nve_balance_economy", "0"),
    "nve_balance_ai_strategy": ("nve_balance", "nve_balance_other", "0"),
    "nve_rebel_threshold": ("nve_rebels_n_subjects", "nve_rebels", "0"),
    "nve_rebel_war_start": ("nve_rebels_n_subjects", "nve_rebels", "0"),
    "nve_subjects_persistance": ("nve_rebels_n_subjects", "Subjects", "0"),
}

dropdowns = parse_setting_blocks(cmm_effects, "cmm_register_dropdown_setting")
bools = parse_setting_blocks(cmm_effects, "cmm_register_bool_setting")
for setting, (tab, group, default_index, option_count) in expected_dropdowns.items():
    expect(setting in dropdowns, f"Missing CMM dropdown registration for {setting}")
    if setting in dropdowns:
        actual = dropdowns[setting]
        expect(actual["mod_id"] == "no_void_economy", f"{setting} dropdown must use mod_id=no_void_economy")
        expect(actual["tab_id"] == tab, f"{setting} dropdown tab_id must be {tab}")
        expect(actual["group_id"] == group, f"{setting} dropdown group_id must be {group}")
        expect(actual["default_index"] == default_index, f"{setting} dropdown default_index must be {default_index}")
        expect(actual["option_count"] == option_count, f"{setting} dropdown option_count must be {option_count}")

for setting, (tab, group, default_value) in expected_bools.items():
    expect(setting in bools, f"Missing CMM bool registration for {setting}")
    if setting in bools:
        actual = bools[setting]
        expect(actual["mod_id"] == "no_void_economy", f"{setting} bool must use mod_id=no_void_economy")
        expect(actual["tab_id"] == tab, f"{setting} bool tab_id must be {tab}")
        expect(actual["group_id"] == group, f"{setting} bool group_id must be {group}")
        expect(actual["default_value"] == default_value, f"{setting} bool default_value must be {default_value}")

add_gui_ids = [key_value(block, "setting_id") for block in iter_named_blocks(cmm_effects, "cmm_add_scripted_gui")]
add_gui_counts = Counter(setting for setting in add_gui_ids if setting)
for setting, count in add_gui_counts.items():
    expect(count == 1, f"cmm_add_scripted_gui must be declared once for {setting}, found {count}")

required_scripted_gui_settings = {
    "nve_decay_activate",
    "activate_trade_cost",
    "nve_debug_messages",
    "nve_monthly_stock_check",
    "nve_save_mode",
    "nve_balance_difficulty",
    "nve_balance_war_shorter",
    "nve_balance_war_exhaustion",
    "nve_balance_economy_location_specialisation",
    "nve_balance_economy_main_balance",
    "nve_balance_ai_strategy",
    "nve_rebel_threshold",
    "nve_rebel_war_start",
    "nve_subjects_persistance",
}
for setting in required_scripted_gui_settings:
    expect(add_gui_counts[setting] == 1, f"{setting} must be wired with cmm_add_scripted_gui exactly once")

gui_defs = set(re.findall(r"^([A-Za-z0-9_.]+)\s*=\s*\{", scripted_gui, re.M))
for setting in add_gui_counts:
    plain_name = f"no_void_economy__{setting}"
    changed_name = f"{plain_name}_on_changed"
    expect(plain_name in gui_defs or changed_name in gui_defs, f"Scripted GUI handler is missing for {setting}")

expect("has_global_variable = modeu5_cmm_nve_main_enabled" in scripted_gui,
       "Dependent NVE scripted GUI blocks must use modeu5_cmm_nve_main_enabled for visibility")

expect(
    re.search(
        r"cmm_sync_dropdown_option_alias\s*=\s*\{[^}]*setting\s*=\s*no_void_economy__nve_no_void_economy_main[^}]*index\s*=\s*3[^}]*alias\s*=\s*variable_mapcmmflagno_void_economy__activate_no_void_economy0",
        cmm_effects,
        re.S,
    )
    is not None,
    "NVE main dropdown must sync the deactivation alias",
)
expect("modeu5_cmm_refresh_nve_main_enabled" in runtime_effects,
       "modeu5_cmm_refresh_nve_main_enabled effect must be present in runtime effects")

planned_restricted_settings = {
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
}
restricted_blocks = parse_setting_blocks(runtime_effects, "cmm_set_requires_unrestricted_tools_enabled")
for setting in planned_restricted_settings:
    expect(setting in restricted_blocks, f"Planned service {setting} must be marked as restricted in the runtime overlay")
    if setting in restricted_blocks:
        expect(restricted_blocks[setting]["mod_id"] == "no_void_economy", f"Restricted planned service {setting} must use mod_id=no_void_economy")

# The generated scripted GUI is still useful as a visual no-op safety net, but
# CMM's actual bool/dropdown controls are disabled through CMMCanEditSetting via
# cmm_set_requires_unrestricted_tools_enabled.
for setting in planned_restricted_settings:
    block = top_level_block(scripted_gui, f"no_void_economy__{setting}_on_changed")
    expect(re.search(r"effect\s*=\s*\{\s*\}", block, re.S) is not None,
           f"Planned service {setting} generated scripted GUI must remain no-op")

for reset_name in (
    "modeu5_cmm_reset_nve_decay_activate",
    "modeu5_cmm_reset_activate_trade_cost",
    "modeu5_cmm_reset_nve_balance_war_shorter",
    "modeu5_cmm_reset_nve_balance_war_exhaustion",
    "modeu5_cmm_reset_nve_balance_economy_location_specialisation",
    "modeu5_cmm_reset_nve_balance_economy_main_balance",
    "modeu5_cmm_reset_nve_balance_ai_strategy",
    "modeu5_cmm_reset_nve_rebel_threshold",
    "modeu5_cmm_reset_nve_rebel_war_start",
    "modeu5_cmm_reset_nve_subjects_persistance",
):
    block = top_level_block(runtime_effects, reset_name)
    expect("remove_from_variable_map" in block and "name = cmm" in block,
           f"{reset_name} must silently reset its CMM map value")

runtime_callback_block = top_level_block(runtime_effects, "modeu5_handle_cmm_runtime_callback")
for forbidden in ("modeu5_cmm_warning.1", "modeu5_cmm_warn_planned_feature", "nve_cmm_warning.1"):
    expect(forbidden not in runtime_callback_block,
           f"Planned service callbacks must not show planned-feature warning popups: found {forbidden}")
expect("trigger_event_non_silently = modeu5_cmm_warning.2" in runtime_effects,
       "Monthly stock check callback must trigger a non-silent warning event")
expect("trigger_event_non_silently = modeu5_cmm_warning.3" in runtime_effects,
       "Complete save callback must trigger a non-silent warning event")
expect("modeu5_cmm_warning.2" in warning_events and "modeu5_cmm_warning.3" in warning_events,
       "Slow monthly check and complete save warning events must exist under in_game/events")
expect("modeu5_cmm_refresh_nve_main_enabled" in runtime_callback_block,
       "Main NVE dropdown callback must refresh the derived visibility marker")

for path, text in {
    "in_game/common/scripted_effects/modeu5_configuration_effects.txt": config_effects,
    "in_game/common/scripted_triggers/modeu5_configuration_triggers.txt": config_triggers,
    "in_game/common/scripted_effects/modeu5_cmm_runtime_effects.txt": runtime_effects,
    "in_game/common/scripted_guis/nve__cmm_scripted_gui.txt": scripted_gui,
}.items():
    unquoted_cmm_links = re.findall(r'(?<!")\b(?:global_)?variable_map\(cmm\|flag:', text)
    expect(not unquoted_cmm_links, f"{path} must not use unquoted CMM variable-map value links")

cmm_mutation_bans = [
    r"\bmodeu5_(?:add|remove|transfer|decay)_stock\b",
    r"\bmodeu5_validate_stock_consistency\b",
    r"\bmodeu5_rebuild_market_stock_from_country_stocks\b",
    r"\b(?:add_to|remove_from)_global_variable_map\b",
    r"\b(?:add_to|remove_from)_variable_map\b",
    r"\bset_global_variable\s*=\s*modeu5_[A-Za-z0-9_]*(?:stock|capacity|production_penalty|demand|consumption|surplus)[A-Za-z0-9_]*\b",
    r"\bset_global_variable\s*=\s*\{[^}]*name\s*=\s*modeu5_[A-Za-z0-9_]*(?:stock|capacity|production_penalty|demand|consumption|surplus)[A-Za-z0-9_]*\b",
]
for path, text in {
    "in_game/common/on_action/nve__cmm_on_actions.txt": on_actions,
    "in_game/common/on_action/nve_cmm_runtime_on_action.txt": runtime_on_actions,
    "in_game/common/scripted_effects/nve__cmm_effects.txt": cmm_effects,
    "in_game/common/scripted_guis/nve__cmm_scripted_gui.txt": scripted_gui,
}.items():
    for pattern in cmm_mutation_bans:
        expect(re.search(pattern, text, re.S) is None, f"CMM callback/UI file must not mutate gameplay state directly: {path}")

# Runtime overlay may mutate the CMM settings map for silent fallback resets, but
# it must not call gameplay stock/capacity/demand effects directly.
for pattern in cmm_mutation_bans[:3] + cmm_mutation_bans[5:]:
    expect(re.search(pattern, runtime_effects, re.S) is None,
           "CMM runtime overlay must not mutate gameplay state directly")

init_block = top_level_block(config_effects, "modeu5_initialize_configuration_state_effect")
expect(re.search(r"variable_map\(cmm\|flag:no_void_economy__nve_debug_messages\)\"\s*=\s*3.*modeu5_enter_debug_runtime_mode\s*=\s*yes.*name\s*=\s*modeu5_debug_level\s+value\s*=\s*2", init_block, re.S) is not None,
       "Detailed debug CMM value must derive debug level 2")
expect(re.search(r"variable_map\(cmm\|flag:no_void_economy__nve_debug_messages\)\"\s*=\s*2.*modeu5_enter_debug_runtime_mode\s*=\s*yes.*name\s*=\s*modeu5_debug_level\s+value\s*=\s*1", init_block, re.S) is not None,
       "Basic debug CMM value must derive debug level 1")
expect(re.search(r"modeu5_enter_normal_runtime_mode\s*=\s*yes.*name\s*=\s*modeu5_debug_level\s+value\s*=\s*0", init_block, re.S) is not None,
       "Unset/default debug CMM value must derive normal runtime and debug level 0")
expect(re.search(r"variable_map\(cmm\|flag:no_void_economy__nve_monthly_stock_check\)\"\s*=\s*2.*modeu5_enter_test_audit_runtime_mode\s*=\s*yes.*modeu5_enter_audit_runtime_mode\s*=\s*yes", init_block, re.S) is not None,
       "Monthly stock check CMM value must enable audit mode and preserve debug+audit when debug is active")
expect(re.search(r"variable_map\(cmm\|flag:no_void_economy__nve_save_mode\)\"\s*=\s*3.*modeu5_enter_strict_accounting_persistence\s*=\s*yes", init_block, re.S) is not None,
       "Complete save CMM value must derive strict persistence")
expect(re.search(r"variable_map\(cmm\|flag:no_void_economy__nve_save_mode\)\"\s*=\s*2.*modeu5_enter_human_relevant_accounting_persistence\s*=\s*yes", init_block, re.S) is not None,
       "Balanced save CMM value must derive human-relevant persistence")
expect("modeu5_enter_minimal_accounting_persistence = yes" in init_block,
       "Default save mode must derive minimal persistence")

full_ledger_block = top_level_block(config_triggers, "modeu5_us00_full_ledger_persistence_allowed_trigger")
for required_gate in (
    "modeu5_accounting_strict_persistence_trigger",
    "modeu5_human_relevant_full_ledger_market_trigger",
    "modeu5_debug_enabled_trigger",
    "modeu5_audit_enabled_trigger",
):
    expect(required_gate in full_ledger_block, f"Full US-00 ledger persistence gate must include {required_gate}")

full_validation_block = top_level_block(config_triggers, "modeu5_full_validation_allowed_trigger")
expect("modeu5_audit_enabled_trigger" in full_validation_block, "Full validation must be gated by audit mode")

human_relevant_block = top_level_block(performance_effects, "modeu5_prepare_human_relevant_full_ledger_markets")
expect("modeu5_accounting_human_relevant_persistence_trigger" in human_relevant_block,
       "Human-relevant market rebuild must be gated by human-relevant persistence")
expect("modeu5_human_relevant_full_ledger_stamp" in human_relevant_block and "current_year" in human_relevant_block and "current_month" in human_relevant_block,
       "Human-relevant market rebuild must stamp the current year/month")
expect("modeu5_rebuild_human_relevant_markets = yes" in human_relevant_block,
       "Human-relevant persistence must rebuild the relevant market list when stale")

loc_keys = localization_keys(loc)
all_settings = {**expected_dropdowns, **expected_bools}
for setting in all_settings:
    expect(f"no_void_economy__{setting}_name" in loc_keys, f"Missing localization name for {setting}")
    expect(f"no_void_economy__{setting}_desc" in loc_keys, f"Missing localization description for {setting}")
for setting, (_, _, _, option_count) in expected_dropdowns.items():
    for index in range(1, int(option_count) + 1):
        expect(f"no_void_economy__{setting}_option_{index}_name" in loc_keys,
               f"Missing localization option {index} name for {setting}")

expect("Warning" in localization_value(loc, "no_void_economy__nve_monthly_stock_check_option_2_desc"),
       "Monthly stock check slow option must include a warning")
expect(
    "Slow" in localization_value(loc, "no_void_economy__nve_save_mode_option_3_name")
    or "Warning" in localization_value(loc, "no_void_economy__nve_save_mode_option_3_desc"),
    "Complete save option must be visibly marked as slow/warning",
)

expect(not (ROOT / "main_menu/common/game_rules/modeu5_game_rules.txt").exists(),
       "Legacy ModeU5 main-menu game-rule configuration must stay removed; CMM is the only configuration surface")
for path, text in {
    "in_game/common/scripted_effects/modeu5_configuration_effects.txt": config_effects,
    "in_game/common/scripted_triggers/modeu5_configuration_triggers.txt": config_triggers,
}.items():
    expect("has_game_rule = modeu5_" not in text,
           f"{path} must not read ModeU5 game rules; use CMM-derived settings instead")

for path in ("in_game", "main_menu"):
    if (ROOT / path).exists():
        combined = "\n".join(
            p.read_text(encoding="utf-8-sig", errors="ignore")
            for p in (ROOT / path).rglob("*")
            if p.is_file() and p.suffix in {".txt", ".yml"}
        )
        expect("modeu5_debug_configuration" not in combined and "modeu5_audit_configuration" not in combined,
               f"Legacy debug/audit game-rule identifiers must not remain under {path}")

if failures:
    print("ModeU5 CMM configuration validation failed:", file=sys.stderr)
    for item in failures:
        print(f"- {item}", file=sys.stderr)
    sys.exit(1)

print("ModeU5 CMM configuration validation passed")

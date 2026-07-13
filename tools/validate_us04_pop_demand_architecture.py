#!/usr/bin/env python3
"""Static contracts for US-04 lifecycle, archived probes, and fail-closed reconciliation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []

CANDIDATES = [
    ("01", "plain_child", "wheat", "docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_01_plain_child.txt", "INJECT:pop_demand = {", "wheat = {", "modeu5_us04_live_pop_demand_multiplier_wheat"),
    ("02", "inner_inject", "beer", "docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_02_inner_inject.txt", "INJECT:pop_demand = {", "INJECT:beer = {", "modeu5_us04_live_pop_demand_multiplier_beer"),
    ("03", "inner_try_inject", "cloth", "docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_03_inner_try_inject.txt", "INJECT:pop_demand = {", "TRY_INJECT:cloth = {", "modeu5_us04_live_pop_demand_multiplier_cloth"),
    ("04", "inner_inject_or_create", "tools", "docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_04_inner_inject_or_create.txt", "INJECT:pop_demand = {", "INJECT_OR_CREATE:tools = {", "modeu5_us04_live_pop_demand_multiplier_tools"),
    ("05", "outer_try_inject", "fish", "docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_05_outer_try_inject.txt", "TRY_INJECT:pop_demand = {", "INJECT:fish = {", "modeu5_us04_live_pop_demand_multiplier_fish"),
    ("06", "outer_inject_or_create", "wine", "docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_06_outer_inject_or_create.txt", "INJECT_OR_CREATE:pop_demand = {", "INJECT:wine = {", "modeu5_us04_live_pop_demand_multiplier_wine"),
    ("07", "direct_global", "books", "docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_07_direct_global.txt", "INJECT:pop_demand = {", "INJECT:books = {", "global_var:modeu5_us04_matrix_global_books"),
    ("08", "direct_global_value_block", "furniture", "docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_08_direct_global_value_block.txt", "INJECT:pop_demand = {", "INJECT:furniture = {", "global_var:modeu5_us04_matrix_global_furniture"),
]


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        failures.append(f"Missing US-04 file: {path}")
        return ""
    return target.read_text(encoding="utf-8-sig", errors="ignore")


def executable_lines(text: str) -> list[str]:
    return [line.split("#", 1)[0] for line in text.splitlines()]


def has_executable_every_location(text: str) -> bool:
    return any(re.search(r"^\s*every_location\s*=\s*\{", line) for line in executable_lines(text))


def expect(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def block(text: str, name: str) -> str:
    marker = f"{name} = {{"
    start = text.find(marker)
    if start < 0:
        failures.append(f"Missing US-04 block: {name}")
        return ""
    open_brace = text.find("{", start)
    depth = 0
    in_quote = False
    escaped = False
    index = open_brace
    while index < len(text):
        char = text[index]
        if in_quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quote = False
        else:
            if char == '"':
                in_quote = True
            elif char == "#":
                newline = text.find("\n", index)
                index = len(text) if newline < 0 else newline
                continue
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
        index += 1
    failures.append(f"Unclosed US-04 block: {name}")
    return ""


def main() -> int:
    template = read("tools/templates/modeu5_us04_pop_demand_good.template.txt")
    helper_generator = read("tools/generate_us04_pop_demand_helpers.sh")
    pop_demand_effects = read("in_game/common/scripted_effects/modeu5_us04_pop_demand_effects.txt")
    demand_resolver = read("in_game/common/scripted_effects/modeu5_stock_demand_resolver_effects.txt")
    integration = read("in_game/common/scripted_effects/modeu5_us04_pop_demand_live_integration_effects.txt")
    observed_target = read("in_game/common/scripted_effects/modeu5_us04_observed_current_target_effects.txt")
    on_actions = read("in_game/common/on_action/modeu5_stock_on_actions.txt")
    probe_values = read("packages/modeu5_core_tests/in_game/common/script_values/modeu5_us04_pop_demand_injection_values.txt")
    endpoint_adapter = read("packages/modeu5_core_tests/in_game/common/script_values/modeu5_us04_pop_demand_endpoint_probe_values.txt")
    endpoint_test = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_pop_demand_endpoint_test_effects.txt")
    debug_test = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_test_effects.txt")
    matrix_test = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_injection_matrix_test_effects.txt")
    q7_q8_test = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_q7_q8_and_target_architecture_test_effects.txt")
    q9_candidate = read("docs/audits/pr69/archives/goods_demand_invalid_syntax/zz_modeu5_us04_probe_09_replace_pop_demand_books.txt")
    q9_test = read("packages/modeu5_core_tests_q9/in_game/common/scripted_effects/modeu5_us04_q9_replace_pop_demand_test_effects.txt")
    q9_debug_events = read("packages/modeu5_core_tests_q9/in_game/events/modeu5_us04_q9_debug_events.txt")
    debug_events = read("packages/modeu5_core_tests/in_game/events/modeu5_us04_debug_events.txt")
    localization = read("packages/modeu5_core_tests/in_game/localization/modeu5_us04_endpoint_probe_l_english.yml")
    summarizer = read("tools/summarize_modeu5_test_logs.sh")
    generate_all = read("tools/generate_all.sh")
    gitignore = read(".gitignore")

    initializer = block(template, "modeu5_initialize_pop_demand_multiplier_good___GOOD__")
    getter = block(template, "modeu5_get_pop_demand_multiplier_good___GOOD__")
    annual = block(template, "modeu5_annual_adjust_location_pop_demand_good___GOOD__")
    reconciliation_getter = block(template, "modeu5_get_us04_reconciliation_coefficient_good___GOOD__")
    reconciliation_initializer = block(template, "modeu5_initialize_us04_reconciliation_coefficient_good___GOOD__")
    monthly_reconciliation = block(template, "modeu5_monthly_reconcile_location_pop_demand_good___GOOD__")
    market_monthly_reconciliation = block(template, "modeu5_monthly_reconcile_country_market_pop_demand_good___GOOD__")
    monthly_country_runtime = block(pop_demand_effects, "modeu5_run_monthly_us04_estate_accounting_for_current_country")
    monthly_country_legacy_runtime = block(pop_demand_effects, "modeu5_run_monthly_us04_reconciliation_for_current_country")
    init_root = block(integration, "modeu5_run_pop_demand_multiplier_initialization_v1")
    init_country = block(integration, "modeu5_run_pop_demand_multiplier_initialization_for_current_country_v1")
    init_once = block(integration, "modeu5_initialize_pop_demand_multipliers_once")
    init_country_once = block(integration, "modeu5_initialize_pop_demand_multipliers_for_current_country_once")
    live_wheat = block(probe_values, "modeu5_us04_live_pop_demand_multiplier_wheat")
    endpoint_probe = block(endpoint_adapter, "modeu5_us04_probe_live_pop_demand_multiplier_wheat")

    expect('value = "modeu5_pop_demand_base_consumption_multiplier"' in initializer, "US-04 initializer must explicitly seed the 1.20 baseline")
    expect('value = "modeu5_pop_demand_base_consumption_multiplier"' in reconciliation_initializer, "US-04 reconciliation coefficient initializer must seed the 1.20 baseline")
    expect("NOT =" in initializer and "is_key_in_variable_map" in initializer, "US-04 initializer must not overwrite an existing location × good coefficient")
    expect("NOT =" in reconciliation_initializer and "is_key_in_variable_map" in reconciliation_initializer, "US-04 reconciliation initializer must not overwrite an existing location × good coefficient")
    expect("name = modeu5_us04_old_multiplier value = 1" in getter, "US-04 missing multiplier read must fall back to 1")
    expect("modeu5_pop_demand_base_consumption_multiplier" not in getter, "US-04 getter must not synthesize 1.20 fallback")
    expect("name = modeu5_us04_reconciliation_coefficient_value value = 1" in reconciliation_getter, "US-04 missing reconciliation coefficient must fall back to 1")
    expect("modeu5_pop_demand_base_consumption_multiplier" not in reconciliation_getter, "US-04 reconciliation getter must not synthesize 1.20 fallback")
    expect("scope:modeu5_us04_multiplier_present > 0" in annual, "US-04 annual adaptation must require an initialized record")
    expect("scope:modeu5_us04_reconciliation_coefficient_present > 0" in annual, "US-04 annual adaptation must require an initialized reconciliation coefficient")
    expect("scope:modeu5_us04_adjustment_applied > 0" in annual, "US-04 annual write must occur only after an adjustment")
    expect("modeu5_write_us04_reconciliation_coefficient_good___GOOD__" in annual, "US-04 annual adaptation must update the active reconciliation coefficient")
    expect("modeu5_read_us04_monthly_location_proxy_estate_quantities_good___GOOD__" in monthly_reconciliation, "US-04 monthly reconciliation must read ModeU5-owned location Estate proxy inputs")
    expect("modeu5_us04_proxy_estate_source_present" in monthly_reconciliation, "US-04 monthly reconciliation must distinguish active proxy input from legacy diagnostics")
    expect("scope:modeu5_us04_proxy_estate_source_present > 0" in monthly_reconciliation, "US-04 stock/estate mutation must require an active proxy source")
    expect("modeu5_us04_proxy_estate_size_total" in monthly_reconciliation, "US-04 monthly reconciliation must compute the local proxy Estate-size total")
    expect("modeu5_remove_stock" in monthly_reconciliation, "US-04 monthly reconciliation must remove satisfied proxy demand through the central stock operator")
    expect("modeu5_us04_positive_reconciliation_delta_ratio" in monthly_reconciliation, "US-04 must split positive consumption deltas from below-baseline restoration deltas")
    expect("modeu5_us04_restore_reconciliation_delta_ratio" in monthly_reconciliation, "US-04 must restore below-baseline consumption deltas when the coefficient falls below 1")
    expect("name = modeu5_us04_goods_supply_removed_quantity value = scope:modeu5_us04_actual_reconciled_quantity" in monthly_reconciliation, "US-04 goods-supply reconciliation must use actual extra quantity removed, not requested total consumption")
    expect("name = modeu5_us04_goods_supply_delta value = { value = scope:modeu5_us04_goods_supply_removed_quantity multiply = -1 }" in monthly_reconciliation, "US-04 goods-supply reconciliation must apply a negative delta equal to actual extra consumption")
    expect("modeu5_add_stock" in monthly_reconciliation, "US-04 monthly reconciliation must restore stock for coefficients below 1")
    expect("name = modeu5_us04_goods_supply_added_quantity value = scope:modeu5_us04_actual_restored_quantity" in monthly_reconciliation, "US-04 goods-supply restoration must use actual stock restored")
    expect("modeu5_us04_reconciliation_estate_refund_value" in monthly_reconciliation, "US-04 below-baseline restoration must compute an estate refund")
    expect("add_gold_to_estate = { estate_type = estate_type:peasants_estate value = scope:modeu5_us04_reconciliation_estate_refund_peasants_estate }" in monthly_reconciliation, "US-04 below-baseline restoration must refund Estates through positive add_gold_to_estate")
    expect("add_goods_supply" in monthly_reconciliation, "US-04 monthly reconciliation must mirror satisfied extra consumption into vanilla market supply")
    expect("add_gold_to_estate" in monthly_reconciliation, "US-04 monthly reconciliation must charge known Estates through the confirmed country-scope effect")
    expect("reason=location_estate_demand_exposure_not_confirmed" not in monthly_reconciliation, "US-04 proxy reconciliation must not stay blocked on direct location Estate demand exposure")
    expect("Legacy location x good records" not in monthly_reconciliation, "US-04 monthly reconciliation must not use a legacy no-estate fallback")
    expect("modeu5_read_country_stock_record" in monthly_reconciliation, "US-04 monthly reconciliation must prove country and market stock deltas after central removal")
    expect("modeu5_read_us04_monthly_location_estate_requested_quantities_good___GOOD__" in template, "US-04 must expose location-level estate requested-demand reads")
    expect("modeu5_read_us04_monthly_pop_requested_estate_quantities_good___GOOD__" in template, "US-04 must retain legacy estate requested-demand read alias")
    for estate in ["peasants_estate", "burghers_estate", "nobles_estate", "clergy_estate"]:
        expect(f"modeu5_us04_proxy_estate_size_{estate}" in template, f"US-04 template must read {estate} proxy size")
        expect(f"modeu5_record_us04_location_estate_proxy_{estate}" in demand_resolver, f"US-04 resolver must expose {estate} proxy writer")
    expect("demands_goods_by_pops = goods:__GOOD__" in market_monthly_reconciliation, "US-04 market monthly dispatcher must gate each good with documented market Pop-demand presence")
    expect("every_owned_location = {" in market_monthly_reconciliation and "limit = { market = scope:modeu5_us04_reconciliation_market }" in market_monthly_reconciliation, "US-04 market monthly dispatcher must scan only owned locations in the target market after the good gate")
    expect("modeu5_monthly_reconcile_location_pop_demand_good___GOOD__ = yes" in market_monthly_reconciliation, "US-04 market monthly dispatcher must delegate to the location-level blocked reconciliation helper")
    expect("modeu5_monthly_assess_country_market_estate_consumption_good___GOOD__" in template, "US-04 must expose an Estate-level country-market assessment alias")
    expect("modeu5_monthly_assess_location_estate_consumption_good___GOOD__" in template, "US-04 must expose an Estate-level location assessment alias")
    expect("modeu5_pop_demand_requested_quantity_peasants_estate" in template, "US-04 must support peasants estate requested-demand records")
    expect("modeu5_pop_demand_requested_quantity_burghers_estate" in template, "US-04 must support burghers estate requested-demand records")
    expect("modeu5_pop_demand_requested_quantity_nobles_estate" in template, "US-04 must support nobles estate requested-demand records")
    expect("modeu5_pop_demand_requested_quantity_clergy_estate" in template, "US-04 must support clergy estate requested-demand records")
    for estate in ["peasants_estate", "burghers_estate", "nobles_estate", "clergy_estate"]:
        expect(f"modeu5_us04_reconciliation_estate_charge_{estate}" in template, f"US-04 monthly reconciliation must record {estate} charge diagnostics")
        expect(f"modeu5_us04_reconciliation_estate_refund_{estate}" in template, f"US-04 monthly reconciliation must record {estate} refund diagnostics")
    expect("modeu5_us04_monthly_requested_quantity_estate_total" in template, "US-04 must keep estate requested total diagnostics available")
    expect("modeu5_us04_reconciliation_estate_charge" in monthly_reconciliation, "US-04 monthly reconciliation must record the estate charge amount")
    expect("modeu5_us04_reconciliation_estate_refund" in monthly_reconciliation, "US-04 monthly reconciliation must record the estate refund amount")

    expect("modeu5_initialize_pop_demand_multiplier_all_goods" in helper_generator, "US-04 helper generator must still emit the all-good initializer")
    expect("modeu5_initialize_us04_reconciliation_coefficient_all_goods" in helper_generator, "US-04 helper generator must emit the active reconciliation initializer")
    expect("modeu5_monthly_reconcile_country_market_pop_demand_all_goods" in helper_generator, "US-04 helper generator must emit country-market monthly reconciliation dispatch")
    expect("modeu5_monthly_assess_country_market_estate_consumption_all_goods" in helper_generator, "US-04 helper generator must emit Estate-level country-market assessment dispatch")
    expect("modeu5_monthly_reconcile_location_pop_demand_all_goods" in helper_generator, "US-04 helper generator must retain location-level monthly reconciliation dispatch for deterministic fixtures")
    expect("modeu5_monthly_assess_location_estate_consumption_all_goods" in helper_generator, "US-04 helper generator must emit Estate-level location assessment dispatch")
    expect(not has_executable_every_location(integration), "US-04 must not use invalid executable every_location effect")
    expect("set_global_variable" in init_root and "modeu5_us04_multiplier_initialization_version" in init_root, "US-04 root initializer must only mark global version")
    expect("every_owned_location = {" in init_country and "modeu5_initialize_pop_demand_multiplier_all_goods = yes" in init_country, "US-04 country initializer must traverse owned locations and seed all goods")
    expect("modeu5_us04_country_multiplier_initialization_version" in init_country, "US-04 country initializer must stamp country version")
    expect("NOT = { has_global_variable = modeu5_us04_multiplier_initialization_version }" in init_once, "US-04 root initializer must have missing-version gate")
    expect("global_var:modeu5_us04_multiplier_initialization_version < 1" in init_once, "US-04 root initializer must support version upgrades")
    expect("NOT = { has_variable = modeu5_us04_country_multiplier_initialization_version }" in init_country_once, "US-04 country initializer must have missing country-version gate")
    expect("modeu5_initialize_pop_demand_multipliers_once = yes" in on_actions, "US-04 root marker must run from delayed new-campaign pulse")
    expect(on_actions.count("modeu5_initialize_pop_demand_multipliers_for_current_country_once = yes") >= 2, "US-04 country initialization must run from monthly and yearly country pulses")
    expect("modeu5_run_monthly_us04_reconciliation_for_current_country = yes" in on_actions, "US-04 monthly reconciliation compatibility wrapper must be wired after monthly stock cycle")
    expect("modeu5_run_monthly_us04_estate_accounting_for_current_country = yes" in monthly_country_legacy_runtime, "US-04 legacy monthly reconciliation wrapper must delegate to Estate-level accounting")
    expect("every_market_present_in_country = {" in monthly_country_runtime, "US-04 current-country monthly runtime must iterate country markets before goods and locations")
    expect("modeu5_monthly_assess_country_market_estate_consumption_all_goods = yes" in monthly_country_runtime, "US-04 current-country monthly runtime must call the Estate-level market/good-first dispatcher")
    expect("modeu5_monthly_reconcile_location_pop_demand_all_goods = yes" not in monthly_country_runtime, "US-04 current-country monthly runtime must not scan every owned location before the market/good gate")
    expect("active_proxy" in debug_test, "US-04 debug test must classify Estate-level accounting as active proxy reconciliation")
    expect("scenario=us04_estate_level_accounting" in debug_test, "US-04 debug test must include the PR #167 Estate-level accounting probe")
    estate_spec = read("docs/specifications/US04_ESTATE_LEVEL_ACCOUNTING.md")
    expect("modeu5_us04_reconciliation_coefficient(location, good)" in estate_spec, "US-04 Estate spec must document the ModeU5 coefficient-based local consumption proxy")
    expect("proxy_estate_size_at_location" in estate_spec, "US-04 Estate spec must document the Estate size term for the local proxy")
    expect("reconciliation_removed_stock_with_proxy" in debug_test, "US-04 debug test must assert that active proxy reconciliation removes stock")
    expect("reconciliation_goods_supply_removed_with_proxy" in debug_test, "US-04 debug test must assert that active proxy reconciliation removes the same extra quantity from goods supply")
    expect("coefficient_below_one_goods_supply_added" in debug_test, "US-04 debug test must assert below-baseline coefficients restore vanilla goods supply")
    expect("coefficient_below_one_stock_restoration" in debug_test, "US-04 debug test must assert below-baseline coefficients restore country and market stock")
    expect("coefficient_below_one_estate_refund" in debug_test, "US-04 debug test must assert below-baseline coefficients refund estates")
    expect("reconciliation_estate_charge_with_proxy" in debug_test, "US-04 debug test must assert that active proxy reconciliation charges estates")
    expect("ModeU5 TEST PASS scenario=us04_estate_level_accounting" in debug_test, "US-04 Estate-level accounting probe must now pass when proxy inputs are present")

    combined_candidates = ""
    for candidate_id, syntax_name, good, path, outer, inner, value_ref in CANDIDATES:
        candidate = read(path)
        combined_candidates += candidate
        expect(outer in candidate, f"US-04 candidate {candidate_id} missing outer syntax")
        expect(inner in candidate, f"US-04 candidate {candidate_id} missing inner syntax")
        expect(value_ref in candidate, f"US-04 candidate {candidate_id} missing value reference")
        if candidate_id not in {"07", "08"}:
            expect(value_ref in probe_values, f"US-04 archived probe values missing {value_ref}")
        if candidate_id in {"01", "02", "03", "04", "05", "06"}:
            expect(f"id={candidate_id} syntax={syntax_name}" in matrix_test, f"US-04 matrix test missing candidate {candidate_id}")
        else:
            expect(f"id={candidate_id} syntax={syntax_name} good={good}" in q7_q8_test, f"US-04 focused Q7/Q8 test missing candidate {candidate_id}")
            expect(f"goods_demand_in_market(goods:{good})" in q7_q8_test, f"US-04 focused Q7/Q8 test must read {good} demand")

    expect("REPLACE:" not in combined_candidates and "TRY_REPLACE:" not in combined_candidates, "US-04 probes 01-08 must remain additive/non-destructive")
    expect("generate_us04_injection_matrix_test.py" not in generate_all, "US-04 injection matrix must not be generated")
    expect(not (ROOT / "tools/generate_us04_injection_matrix_test.py").exists(), "US-04 injection matrix generator must remain deleted")
    expect(not (ROOT / "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_pop_demand_injection_probe.txt").exists(), "Obsolete aggregate probe must remain deleted")

    expect("modeu5_pop_demand_base_consumption_multiplier" not in probe_values, "Archived injection values must never use 1.20 as fallback")
    expect("value = 1" in live_wheat, "Archived injection values must start from multiplier 1")
    expect("has_global_variable = modeu5_us04_multiplier_initialization_version" in probe_values, "Archived injection values must require completed initialization")
    expect('value = "modeu5_us04_live_pop_demand_multiplier_wheat"' in endpoint_probe, "Endpoint probe must delegate to the shared test wheat value")

    expect("modeu5_us04_current_pop_consumption_target_books_by_market" in observed_target, "Observed-current architecture must persist books target by market")
    expect("goods_demand_in_market(goods:books)" in observed_target, "Observed-current architecture must observe current books demand")
    expect("multiply = $baseline_multiplier$" in observed_target, "Observed-current architecture must initialize observed demand by baseline multiplier")
    expect("multiply = $factor$" in observed_target, "Observed-current architecture must transition current target by yearly factor")
    expect("modeu5_resolve_stock_consumption" in observed_target and "requested_quantity = scope:modeu5_us04_current_consumption_target" in observed_target, "Observed-current target must feed ModeU5 stock consumption")

    expect("scenario=us04_q7_q8_positive_globals" in q7_q8_test, "Focused Q7/Q8 scenario marker missing")
    expect("scenario=us04_observed_current_target_architecture" in q7_q8_test, "Observed-current architecture scenario marker missing")
    expect("modeu5_us04_q7_q8_finalize = yes" in debug_events, "Debug event must retain direct-console focused Q7/Q8 probe")
    expect("modeu5_debug_run_us04_estate_level_accounting_probe = yes" in debug_events, "Visible US-04 debug option C must run the Estate-level accounting probe")
    expect("modeu5_us04_debug.1.c" in debug_events and "Estate-level location accounting" in localization, "Estate-level accounting option must be present and localized")

    expect("TEST PACKAGE ONLY / DESTRUCTIVE PROBE" in q9_candidate, "Q9 destructive candidate must be clearly marked test-only")
    expect("REPLACE:pop_demand = {" in q9_candidate, "Q9 must use REPLACE:pop_demand")
    expect("books = {" in q9_candidate and "global_var:modeu5_us04_q9_replace_global_books" in q9_candidate, "Q9 must replace books demand with a dynamic global source")
    expect("scenario=us04_q9_replace_pop_demand" in q9_test, "Q9 scenario marker missing")
    expect("goods_demand_in_market(goods:books)" in q9_test, "Q9 must read books demand")
    expect("goods_demand_in_market(goods:wool)" in q9_test, "Q9 must keep a wool control")
    expect("modeu5_us04_q9_replace_global_books value = 4.0" in q9_test, "Q9 must raise replacement source to 4.0")
    expect("reason=no_target_response" in q9_test, "Q9 must classify no-response failures")
    expect("namespace = modeu5_us04_q9_debug" in q9_debug_events, "Q9 must use an isolated debug namespace")
    expect("modeu5_us04_q9_debug.1" in q9_debug_events and "modeu5_us04_q9_debug.3" in q9_debug_events, "Q9 isolated console event chain must be present")
    expect("id = modeu5_us04_q9_debug.3 days = 35" in q9_debug_events, "Q9 must wait across a monthly tick before final capture")
    expect("modeu5_us04_q9_replace" not in debug_events, "Normal core test launcher must not reference isolated Q9 effects")

    expect("INJECTION (CONTROL|CANDIDATE|RESULT|MATRIX" in summarizer, "Summarizer must include US-04 injection control/candidate/result lines")
    expect("VANILLA DEMAND" in summarizer, "Summarizer must include US-04 vanilla-demand probe lines")
    expect('expected_mode" != "none"' in summarizer and 'Expected scenario checking disabled.' in summarizer, "Summarizer must support --expected none")

    expect("generate_us04_pop_demand_override.py" not in generate_all, "US-04 generation pipeline must not regenerate vanilla pop_demand")
    expect("packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt" not in gitignore, "Obsolete exact-path vanilla pop_demands.txt must not remain ignored")
    expect(not (ROOT / "tools/generate_us04_pop_demand_override.py").exists(), "Obsolete vanilla Pop-demand override generator must remain deleted")
    expect(not (ROOT / "packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt").exists(), "No exact-path vanilla pop_demands.txt override may be present")
    expect(not any((ROOT / "packages/modeu5_economy_rebalance/in_game/common/goods_demand").glob("zz_modeu5_us04_probe_*.txt")), "Archived US-04 pop_demand probes must not live in the campaign economy package")
    expect(not any((ROOT / "packages/modeu5_core_tests_q9/in_game/common/goods_demand").glob("zz_modeu5_us04_probe_*.txt")), "Archived invalid-syntax US-04 pop_demand probes must not live in a loadable test package")
    expect(not (ROOT / "packages/modeu5_economy_rebalance/in_game/common/script_values/modeu5_us04_pop_demand_injection_values.txt").exists(), "Archived US-04 injection script values must not live in the campaign economy package")
    expect(not (ROOT / "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_09_replace_pop_demand_books.txt").exists(), "Q9 destructive replacement probe must never live in the production economy package")
    expect(not (ROOT / "packages/modeu5_core_tests/in_game/common/goods_demand/zz_modeu5_us04_probe_09_replace_pop_demand_books.txt").exists(), "Q9 destructive replacement probe must never live in the normal core test package")

    for marker in ["reason=missing_map_not_vanilla", "reason=missing_initialization_gate_not_vanilla", "reason=disabled_gate_not_vanilla"]:
        expect(marker in endpoint_test, f"Endpoint test must assert {marker}")

    if failures:
        print("ModeU5 US-04 Pop-demand architecture validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("ModeU5 US-04 archived probes and proxy reconciliation validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Static contracts for the US-04 multiplier lifecycle and explicit probe matrix."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []

CANDIDATES = [
    ("01", "plain_child", "wheat", "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_01_plain_child.txt", "INJECT:pop_demand = {", "wheat = {", "modeu5_us04_live_pop_demand_multiplier_wheat"),
    ("02", "inner_inject", "beer", "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_02_inner_inject.txt", "INJECT:pop_demand = {", "INJECT:beer = {", "modeu5_us04_live_pop_demand_multiplier_beer"),
    ("03", "inner_try_inject", "cloth", "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_03_inner_try_inject.txt", "INJECT:pop_demand = {", "TRY_INJECT:cloth = {", "modeu5_us04_live_pop_demand_multiplier_cloth"),
    ("04", "inner_inject_or_create", "tools", "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_04_inner_inject_or_create.txt", "INJECT:pop_demand = {", "INJECT_OR_CREATE:tools = {", "modeu5_us04_live_pop_demand_multiplier_tools"),
    ("05", "outer_try_inject", "fish", "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_05_outer_try_inject.txt", "TRY_INJECT:pop_demand = {", "INJECT:fish = {", "modeu5_us04_live_pop_demand_multiplier_fish"),
    ("06", "outer_inject_or_create", "wine", "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_06_outer_inject_or_create.txt", "INJECT_OR_CREATE:pop_demand = {", "INJECT:wine = {", "modeu5_us04_live_pop_demand_multiplier_wine"),
    ("07", "direct_global", "tea", "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_07_direct_global.txt", "INJECT:pop_demand = {", "INJECT:tea = {", "global_var:modeu5_us04_matrix_global_tea"),
    ("08", "direct_global_value_block", "coffee", "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_probe_08_direct_global_value_block.txt", "INJECT:pop_demand = {", "INJECT:coffee = {", "global_var:modeu5_us04_matrix_global_coffee"),
]


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        failures.append(f"Missing US-04 architecture file: {path}")
        return ""
    return target.read_text(encoding="utf-8-sig", errors="ignore")


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
    integration = read("in_game/common/scripted_effects/modeu5_us04_pop_demand_live_integration_effects.txt")
    on_actions = read("in_game/common/on_action/modeu5_stock_on_actions.txt")
    production_values = read("packages/modeu5_economy_rebalance/in_game/common/script_values/modeu5_us04_pop_demand_injection_values.txt")
    probe_adapter = read("packages/modeu5_core_tests/in_game/common/script_values/modeu5_us04_pop_demand_endpoint_probe_values.txt")
    endpoint_test = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_pop_demand_endpoint_test_effects.txt")
    matrix_test = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_injection_matrix_test_effects.txt")
    debug_events = read("packages/modeu5_core_tests/in_game/events/modeu5_us04_debug_events.txt")
    generate_all = read("tools/generate_all.sh")
    gitignore = read(".gitignore")

    initializer = block(template, "modeu5_initialize_pop_demand_multiplier_good___GOOD__")
    getter = block(template, "modeu5_get_pop_demand_multiplier_good___GOOD__")
    annual = block(template, "modeu5_annual_adjust_location_pop_demand_good___GOOD__")
    init_world = block(integration, "modeu5_run_pop_demand_multiplier_initialization_v1")
    init_once = block(integration, "modeu5_initialize_pop_demand_multipliers_once")
    live_wheat = block(production_values, "modeu5_us04_live_pop_demand_multiplier_wheat")
    probe = block(probe_adapter, "modeu5_us04_probe_live_pop_demand_multiplier_wheat")

    expect('value = "modeu5_pop_demand_base_consumption_multiplier"' in initializer, "US-04 initializer must explicitly seed the 1.20 baseline")
    expect("NOT =" in initializer and "is_key_in_variable_map" in initializer, "US-04 initializer must not overwrite an existing location × good coefficient")
    expect("name = modeu5_us04_old_multiplier value = 1" in getter, "US-04 missing multiplier read must fall back to 1 (vanilla)")
    expect("modeu5_pop_demand_base_consumption_multiplier" not in getter, "US-04 getter must never synthesize the 1.20 baseline")
    expect("scope:modeu5_us04_multiplier_present > 0" in annual, "US-04 yearly adaptation must require an existing initialized record")
    expect("scope:modeu5_us04_adjustment_applied > 0" in annual, "US-04 yearly write must occur only after a 0.99 or 1.01 adjustment")
    expect("OR =" not in annual[annual.find("modeu5_us04_adjustment_applied") :], "US-04 yearly write must not recreate missing records")

    expect("modeu5_initialize_pop_demand_multiplier_all_goods" in helper_generator, "US-04 generator may only generate internal all-good initializer helpers")
    expect("every_location = {" in init_world, "US-04 initialization v1 must traverse every location")
    expect("modeu5_initialize_pop_demand_multiplier_all_goods = yes" in init_world, "US-04 initialization v1 must seed every supported good per location")
    expect(init_world.find("every_location = {") < init_world.find("name = modeu5_us04_multiplier_initialization_version"), "US-04 initialization version gate must be written after the world pass")
    expect("NOT = { has_global_variable = modeu5_us04_multiplier_initialization_version }" in init_once, "US-04 initialization must have a missing-version gate")
    expect("global_var:modeu5_us04_multiplier_initialization_version < 1" in init_once, "US-04 initialization must support explicit version upgrades")
    expect("modeu5_initialize_pop_demand_multipliers_once = yes" in on_actions, "US-04 initialization must run from the delayed new-campaign pulse")

    combined_candidates = ""
    for candidate_id, syntax_name, good, path, outer_syntax, inner_syntax, value_ref in CANDIDATES:
        candidate = read(path)
        combined_candidates += candidate
        expect(outer_syntax in candidate, f"US-04 candidate {candidate_id} missing outer syntax")
        expect(inner_syntax in candidate, f"US-04 candidate {candidate_id} missing inner syntax")
        expect(value_ref in candidate, f"US-04 candidate {candidate_id} missing value reference")
        expect("value =" not in candidate or candidate_id == "08", f"US-04 candidate {candidate_id} must not copy vanilla formulas")
        if candidate_id not in {"07", "08"}:
            expect(value_ref in production_values, f"US-04 production values missing {value_ref}")
        expect(f"id={candidate_id} syntax={syntax_name} good={good}" in matrix_test or f"id={candidate_id} syntax={syntax_name}" in matrix_test, f"US-04 static matrix missing result label for candidate {candidate_id}")
        expect(f"goods_demand_in_market(goods:{good})" in matrix_test, f"US-04 static matrix does not read candidate {candidate_id} demand")

    expect("REPLACE:" not in combined_candidates and "TRY_REPLACE:" not in combined_candidates, "US-04 syntax matrix must remain additive-only")
    expect(not (ROOT / "packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_pop_demand_injection_probe.txt").exists(), "The obsolete aggregate/generator-style injection probe must remain deleted")
    expect(not (ROOT / "tools/generate_us04_injection_matrix_test.py").exists(), "US-04 injection matrix generator must remain deleted")
    expect("generate_us04_injection_matrix_test.py" not in generate_all, "generate_all.sh must not generate the US-04 injection matrix")

    expect("modeu5_pop_demand_base_consumption_multiplier" not in production_values, "US-04 production live values must never use 1.20 as a fallback")
    expect("value = 1" in live_wheat, "US-04 production live values must start from multiplier 1")
    expect("has_global_variable = modeu5_us04_multiplier_initialization_version" in production_values, "US-04 production live values must require completed initialization")
    expect("variable_map(modeu5_pop_demand_multiplier|goods:wheat)" in production_values, "US-04 production wheat value must read the location × wheat coefficient")
    expect('value = "modeu5_us04_live_pop_demand_multiplier_wheat"' in probe, "US-04 endpoint probe must delegate to the production wheat value")

    expect("goods_demand_in_market(goods:wool)" in matrix_test, "US-04 matrix must include an uninjected wool control")
    expect("ModeU5 US-04 INJECTION MATRIX SUMMARY" in matrix_test, "US-04 matrix must emit a consolidated summary")
    expect("scenario=us04_pop_demand_injection_matrix" in matrix_test, "US-04 matrix must emit a dedicated scenario marker")
    expect("modeu5_us04_matrix_restore_state = yes" in matrix_test, "US-04 matrix must restore state")
    expect("modeu5_us04_matrix_begin = yes" in debug_events and "modeu5_us04_matrix_capture_low_and_raise = yes" in debug_events and "modeu5_us04_matrix_finalize = yes" in debug_events, "US-04 debug event must run the complete static matrix chain")

    expect("generate_us04_pop_demand_override.py" not in generate_all, "US-04 generation pipeline must not regenerate vanilla pop_demand")
    expect("packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt" not in gitignore, "The obsolete exact-path vanilla pop_demands.txt must not remain ignored")
    expect(not (ROOT / "tools/generate_us04_pop_demand_override.py").exists(), "The obsolete vanilla Pop-demand override generator must remain deleted")
    expect(not (ROOT / "packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt").exists(), "No exact-path vanilla pop_demands.txt override may be present")

    for marker in ["reason=missing_map_not_vanilla", "reason=missing_initialization_gate_not_vanilla", "reason=disabled_gate_not_vanilla"]:
        expect(marker in endpoint_test, f"US-04 endpoint test must assert {marker}")
    expect("modeu5_us04_endpoint_missing_result < 0.999" in endpoint_test, "US-04 endpoint missing-key test must expect multiplier 1")
    expect("modeu5_us04_endpoint_uninitialized_result < 0.999" in endpoint_test, "US-04 endpoint uninitialized test must expect multiplier 1")

    if failures:
        print("ModeU5 US-04 Pop-demand architecture validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("ModeU5 US-04 explicit additive syntax matrix validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Static contracts for the US-04 Pop-demand multiplier lifecycle and injection probe."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []


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
    injection = read("packages/modeu5_economy_rebalance/in_game/common/goods_demand/zz_modeu5_us04_pop_demand_injection_probe.txt")
    production_value = read("packages/modeu5_economy_rebalance/in_game/common/script_values/modeu5_us04_pop_demand_injection_values.txt")
    probe_adapter = read("packages/modeu5_core_tests/in_game/common/script_values/modeu5_us04_pop_demand_endpoint_probe_values.txt")
    endpoint_test = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_pop_demand_endpoint_test_effects.txt")
    generate_all = read("tools/generate_all.sh")
    gitignore = read(".gitignore")

    initializer = block(template, "modeu5_initialize_pop_demand_multiplier_good___GOOD__")
    getter = block(template, "modeu5_get_pop_demand_multiplier_good___GOOD__")
    annual = block(template, "modeu5_annual_adjust_location_pop_demand_good___GOOD__")
    init_world = block(integration, "modeu5_run_pop_demand_multiplier_initialization_v1")
    init_once = block(integration, "modeu5_initialize_pop_demand_multipliers_once")
    live_value = block(production_value, "modeu5_us04_live_pop_demand_multiplier_wheat")
    probe = block(probe_adapter, "modeu5_us04_probe_live_pop_demand_multiplier_wheat")

    expect('value = "modeu5_pop_demand_base_consumption_multiplier"' in initializer,
           "US-04 initializer must explicitly seed the 1.20 baseline")
    expect("NOT =" in initializer and "is_key_in_variable_map" in initializer,
           "US-04 initializer must not overwrite an existing location × good coefficient")

    expect("name = modeu5_us04_old_multiplier value = 1" in getter,
           "US-04 missing multiplier read must fall back to 1 (vanilla)")
    expect("modeu5_pop_demand_base_consumption_multiplier" not in getter,
           "US-04 getter must never synthesize the 1.20 baseline")

    expect("scope:modeu5_us04_multiplier_present > 0" in annual,
           "US-04 yearly adaptation must require an existing initialized record")
    expect("scope:modeu5_us04_adjustment_applied > 0" in annual,
           "US-04 yearly write must occur only after a 0.99 or 1.01 adjustment")
    expect("OR =" not in annual[annual.find("modeu5_us04_adjustment_applied"):],
           "US-04 yearly write must not use the former adjustment-or-present recreation condition")

    expect("modeu5_initialize_pop_demand_multiplier_all_goods" in helper_generator,
           "US-04 generator must emit the all-good campaign initializer")
    expect("every_location = {" in init_world,
           "US-04 initialization v1 must traverse every location")
    expect("modeu5_initialize_pop_demand_multiplier_all_goods = yes" in init_world,
           "US-04 initialization v1 must seed every supported good per location")
    expect(init_world.find("every_location = {") < init_world.find("name = modeu5_us04_multiplier_initialization_version"),
           "US-04 initialization version gate must be written after the world pass")
    expect("NOT = { has_global_variable = modeu5_us04_multiplier_initialization_version }" in init_once,
           "US-04 initialization must have a missing-version gate")
    expect("global_var:modeu5_us04_multiplier_initialization_version < 1" in init_once,
           "US-04 initialization must support explicit version upgrades")
    expect("modeu5_initialize_pop_demand_multipliers_once = yes" in on_actions,
           "US-04 initialization must run from the delayed new-campaign pulse")

    expect("INJECT:pop_demand = {" in injection,
           "US-04 live probe must inject into the existing pop_demand object")
    expect(injection.count("wheat = {") == 1,
           "US-04 injection probe must contain exactly one wheat entry")
    expect('multiply = "modeu5_us04_live_pop_demand_multiplier_wheat"' in injection,
           "US-04 wheat injection must reference the production multiplier value")
    expect("value =" not in injection,
           "US-04 injection probe must not copy or replace the vanilla wheat value formula")
    expect("beer =" not in injection and "cloth =" not in injection,
           "US-04 live injection must remain wheat-only before runtime acceptance")

    expect("value = 1" in live_value,
           "US-04 production live value must start from vanilla multiplier 1")
    expect("modeu5_pop_demand_base_consumption_multiplier" not in live_value,
           "US-04 production live value must never use 1.20 as a fallback")
    expect("has_global_variable = modeu5_us04_multiplier_initialization_version" in live_value,
           "US-04 production live value must require completed initialization")
    expect("location = {" in live_value and "variable_map(modeu5_pop_demand_multiplier|goods:wheat)" in live_value,
           "US-04 production live value must read the Pop location × wheat coefficient")

    expect('value = "modeu5_us04_live_pop_demand_multiplier_wheat"' in probe,
           "US-04 endpoint probe must delegate to the exact production injection value")

    expect("generate_us04_pop_demand_override.py" not in generate_all,
           "US-04 generation pipeline must not regenerate the vanilla pop_demand file")
    expect("MODEU5_ENABLE_US04_POP_DEMAND_OVERRIDE" not in generate_all,
           "US-04 generation pipeline must not retain the former override switch")
    expect("validate_us04_pop_demand_architecture.py" in generate_all,
           "US-04 static architecture validator must remain in generate_all.sh")
    expect("packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt" not in gitignore,
           "The obsolete exact-path vanilla pop_demands.txt output must not remain ignored")

    expect(not (ROOT / "tools/generate_us04_pop_demand_override.py").exists(),
           "The obsolete vanilla Pop-demand override generator must remain deleted")
    expect(not (ROOT / "packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt").exists(),
           "No exact-path vanilla pop_demands.txt override may be present")

    for marker in [
        "reason=missing_map_not_vanilla",
        "reason=missing_initialization_gate_not_vanilla",
        "reason=disabled_gate_not_vanilla",
    ]:
        expect(marker in endpoint_test, f"US-04 endpoint test must assert {marker}")
    expect("modeu5_us04_endpoint_missing_result < 0.999" in endpoint_test,
           "US-04 endpoint missing-key test must expect multiplier 1")
    expect("modeu5_us04_endpoint_uninitialized_result < 0.999" in endpoint_test,
           "US-04 endpoint uninitialized test must expect multiplier 1")

    if failures:
        print("ModeU5 US-04 Pop-demand architecture validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("ModeU5 US-04 Pop-demand injection architecture validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

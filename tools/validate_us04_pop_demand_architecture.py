#!/usr/bin/env python3
"""Static contracts for the US-04 Pop-demand multiplier lifecycle."""

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
    override_generator = read("tools/generate_us04_pop_demand_override.py")
    integration = read("in_game/common/scripted_effects/modeu5_us04_pop_demand_live_integration_effects.txt")
    on_actions = read("in_game/common/on_action/modeu5_stock_on_actions.txt")
    probe_value = read("packages/modeu5_core_tests/in_game/common/script_values/modeu5_us04_pop_demand_endpoint_probe_values.txt")
    endpoint_test = read("packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_pop_demand_endpoint_test_effects.txt")

    initializer = block(template, "modeu5_initialize_pop_demand_multiplier_good___GOOD__")
    getter = block(template, "modeu5_get_pop_demand_multiplier_good___GOOD__")
    annual = block(template, "modeu5_annual_adjust_location_pop_demand_good___GOOD__")
    init_world = block(integration, "modeu5_run_pop_demand_multiplier_initialization_v1")
    init_once = block(integration, "modeu5_initialize_pop_demand_multipliers_once")
    probe = block(probe_value, "modeu5_us04_probe_live_pop_demand_multiplier_wheat")

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

    expect('default=["wheat"]' in override_generator,
           "US-04 live pop_demand integration must remain a wheat-only probe before runtime acceptance")
    expect("selected_goods" in override_generator,
           "US-04 override generator must wrap only explicitly selected probe goods")
    expect("modeu5_pop_demand_base_consumption_multiplier" not in override_generator,
           "US-04 live Pop-scope reader generator must not use 1.20 as a fallback")
    expect("has_global_variable = modeu5_us04_multiplier_initialization_version" in override_generator,
           "US-04 generated live reader must require completed initialization")

    expect("value = 1" in probe,
           "US-04 endpoint probe must begin from vanilla multiplier 1")
    expect("modeu5_pop_demand_base_consumption_multiplier" not in probe,
           "US-04 endpoint probe must not use baseline 1.20 as a fallback")
    expect("has_global_variable = modeu5_us04_multiplier_initialization_version" in probe,
           "US-04 endpoint probe must test the initialization gate")

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

    print("ModeU5 US-04 Pop-demand architecture validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

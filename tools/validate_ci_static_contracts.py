#!/usr/bin/env python3
"""Static CI contracts for the US-17/US-20 direct named-value implementation.

The complete pre-existing validator remains in
``validate_ci_static_contracts_legacy.py``. This entry point replaces only the
US-17/US-20 contracts whose business rules changed, then delegates to the
legacy main so all unrelated checks remain active.
"""

from __future__ import annotations

import re

import validate_ci_static_contracts_legacy as legacy

CUSTOM_DEFINE_NAMES = (
    "CBP_ROUTE_LOSS_COEFFICIENT_MAX",
    "CBP_ROUTE_LOSS_COEFFICIENT_CURVE",
    "CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT",
    "CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE",
    "CBP_ROUTE_LOSS_MAX",
    "CBP_ROUTE_LOSS_CURVE",
    "CBP_TRADE_MAINTENANCE_VANILLA_WEIGHT",
    "CBP_TRADE_MAINTENANCE_DIRECTIONAL_WEIGHT",
    "CBP_TRADE_EFFICIENCY_COMPENSATION_MAX",
    "CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE",
    "CBD_TRADE_MAINTENANCE_MAX_IMPACT",
)


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
    expect = legacy.expect
    block = legacy.block
    runtime_constants = legacy.read(
        "in_game/common/script_values/cbp_us17_us20_runtime_constants.txt"
    )
    trade_defines = legacy.read("loading_screen/common/defines/cbp_trade_defines.txt")

    expected_runtime_values = {
        "cbp_us17_us20_route_loss_coefficient_max": "0.05",
        "cbp_us17_us20_route_loss_coefficient_curve": "10",
        "cbp_us17_maintenance_component_weight": "0.5",
        "cbp_us17_maintenance_efficiency_scale": "10",
    }
    for name, value in expected_runtime_values.items():
        value_block = block(runtime_constants, name)
        expect(
            f"value = {value}" in value_block,
            f"Named script value {name} must equal {value}",
        )

    for name in CUSTOM_DEFINE_NAMES:
        expect(
            re.search(rf"(?m)^\s*{re.escape(name)}\s*=", trade_defines) is None,
            f"Arbitrary custom Define must be absent: {name}",
        )

    expect(
        "define:NCountry|CBP_" not in owner_modifier_effects
        and "define:NCountry|CBD_" not in owner_modifier_effects,
        "US17/US20 production must not read arbitrary custom engine Defines",
    )
    expect(
        "REPLACE:cbp_compute_us20_route_loss_coefficient_from_selling_baseline"
        not in owner_modifier_effects
        and "REPLACE:cbp_compute_us17_native_corrections_from_baselines"
        not in owner_modifier_effects,
        "US17/US20 calculations must be authoritative direct effects",
    )

    coefficient_formula = block(
        owner_modifier_effects,
        "cbp_compute_us20_route_loss_coefficient_from_selling_baseline",
    )
    correction_formula = block(
        owner_modifier_effects,
        "cbp_compute_us17_native_corrections_from_baselines",
    )
    reconstruction = block(
        owner_modifier_effects,
        "cbp_reconstruct_us17_native_baselines_from_effective_values",
    )
    refresh = block(
        owner_modifier_effects,
        "cbp_refresh_us17_native_profit_modifiers_for_current_country",
    )
    clear = block(
        owner_modifier_effects,
        "cbp_clear_us17_native_profit_modifiers_for_current_country",
    )
    money_wrapper = block(
        owner_modifier_effects,
        "cbp_run_us17_operation_aware_route_profit_reconciliation",
    )
    us20_route = block(
        owner_modifier_effects,
        "cbp_compute_us20_route_loss_from_selling_efficiency",
    )
    goods_wrapper = block(
        owner_modifier_effects,
        "cbp_run_us20_route_loss_reconciliation",
    )

    for token in [
        "cbp_us17_native_baseline_selling_efficiency",
        "cbp_us17_us20_route_loss_coefficient_max",
        "cbp_us17_us20_route_loss_coefficient_curve",
        "cbp_us20_route_loss_denominator",
        "cbp_us20_route_loss_coefficient_result",
        "divide = scope:cbp_us20_route_loss_denominator",
        "min = 0.01",
    ]:
        expect(token in coefficient_formula, f"Shared Selling coefficient must contain {token}")
    expect(
        coefficient_formula.count("divide = scope:") == 1,
        "Shared Selling coefficient helper must contain exactly one reciprocal curve",
    )
    expect(
        "set_variable" not in coefficient_formula,
        "Pure Selling coefficient helper must return a temporary result",
    )

    for token in [
        "cbp_us17_native_selling_correction_result",
        "cbp_us17_native_baseline_selling_efficiency",
        "var:cbp_us20_route_loss_coefficient",
    ]:
        expect(token in correction_formula, f"Selling correction must contain {token}")
    expect(
        "scope:cbp_us20_route_loss_coefficient_result" not in correction_formula,
        "Selling correction must consume the persisted country coefficient",
    )
    expect(
        "cbp_us17_us20_route_loss_coefficient_max" not in correction_formula
        and "cbp_us17_us20_route_loss_coefficient_curve" not in correction_formula,
        "Selling correction must not recalculate the shared coefficient",
    )

    for token in [
        "cbp_us17_native_import_correction_result",
        "cbp_us17_native_baseline_import_efficiency",
        "cbp_us17_native_export_correction_result",
        "cbp_us17_native_baseline_export_efficiency",
    ]:
        expect(token in correction_formula, f"Directional cancellation must contain {token}")
    for forbidden in [
        "CBP_TRADE_EFFICIENCY_COMPENSATION_MAX",
        "CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE",
        "cbp_us17_import_residual_impact",
        "cbp_us17_export_residual_impact",
    ]:
        expect(forbidden not in correction_formula, f"Directional residual curve must be absent: {forbidden}")

    for token in [
        "cbp_us17_maintenance_vanilla_term",
        "cbp_us17_maintenance_directional_term",
        "cbp_us17_maintenance_curve_denominator",
        "cbp_us17_maintenance_curve_reciprocal",
        "cbp_us17_native_effective_maintenance_result",
        "cbp_us17_native_maintenance_correction_result",
        "cbp_us17_maintenance_component_weight",
        "cbp_us17_maintenance_efficiency_scale",
        "divide = scope:cbp_us17_maintenance_curve_denominator",
    ]:
        expect(token in correction_formula, f"Mixed-denominator maintenance formula must contain {token}")
    expect(
        correction_formula.count("divide = scope:") == 1,
        "US17 correction helper must contain exactly one maintenance reciprocal",
    )
    expect(
        correction_formula.count("cbp_us17_maintenance_component_weight") == 2,
        "Component weight must apply once to M and once to the directional scale",
    )
    expect(
        "cbp_us17_directional_maintenance_efficiency" not in correction_formula,
        "Rejected separately averaged directional efficiency must be absent",
    )

    for semantic_name in ["selling", "import", "export", "maintenance"]:
        expect(
            f"cbp_us17_native_previous_{semantic_name}_correction" in reconstruction,
            f"Baseline reconstruction must remove previous {semantic_name} correction",
        )
        expect(
            f"cbp_us17_native_{semantic_name}_baseline" in refresh,
            f"Refresh must persist reconstructed {semantic_name} baseline",
        )
        expect(
            f"cbp_us17_native_{semantic_name}_correction" in refresh,
            f"Refresh must persist {semantic_name} correction",
        )

    coefficient_call = "cbp_compute_us20_route_loss_coefficient_from_selling_baseline = yes"
    persist_coefficient = (
        "set_variable = { name = cbp_us20_route_loss_coefficient "
        "value = scope:cbp_us20_route_loss_coefficient_result }"
    )
    correction_call = "cbp_compute_us17_native_corrections_from_baselines = yes"
    for token, message in [
        (coefficient_call, "Country refresh must calculate the shared Selling coefficient"),
        (persist_coefficient, "Country refresh must persist the shared Selling coefficient"),
        (correction_call, "Country refresh must calculate US17 corrections"),
    ]:
        expect(token in refresh, message)
    expect(
        refresh.index(coefficient_call)
        < refresh.index(persist_coefficient)
        < refresh.index(correction_call),
        "Country refresh order must remain calculate -> persist -> consume",
    )
    expect(
        refresh.count(persist_coefficient) == 1,
        "Country refresh must persist cbp_us20_route_loss_coefficient exactly once",
    )
    expect(
        "cbp_us17_native_modifier_state_version value = 7" in refresh,
        "Mixed-denominator state must use version 7",
    )
    expect(
        "cbp_us17_runtime_constant_source_version value = 1" in refresh,
        "Refresh must persist the named-value source version directly",
    )
    expect(
        "remove_variable = cbp_us20_route_loss_coefficient" in clear,
        "Disabling trade rework must remove the shared coefficient",
    )
    expect(
        "cbp_us17_runtime_constant_source_version value = 1" in clear,
        "Clear must persist the named-value source version directly",
    )

    expect("add_gold" not in money_wrapper, "US17 compatibility hook must not mutate treasury")
    expect(
        "gui_cbp_trade_efficiency_route_money_delta value = 0" in money_wrapper,
        "US17 compatibility hook must expose a zero money delta",
    )

    for token in [
        "has_variable = cbp_us20_route_loss_coefficient",
        "value = var:cbp_us20_route_loss_coefficient",
        "cbp_us20_route_loss_coefficient_input",
        "gui_cbp_us20_goods_received_loss",
        "gui_cbp_us20_target_goods_amount_received",
        "gui_cbp_us20_goods_reconciliation_delta",
    ]:
        expect(token in us20_route, f"US20 route calculation must contain {token}")
    for forbidden in [
        "cbp_us17_us20_route_loss_coefficient_max",
        "cbp_us17_us20_route_loss_coefficient_curve",
        "divide =",
        "modifier:selling_efficiency",
        "var:cbp_us17_native_selling_baseline",
    ]:
        expect(forbidden not in us20_route, f"US20 must not recalculate coefficient ({forbidden})")
    expect(
        "value = scope:gui_cbp_us20_goods_amount_sent" in us20_route
        and "multiply = scope:cbp_us20_route_loss_coefficient_input" in us20_route,
        "US20 goods loss must equal trade volume multiplied by persisted coefficient",
    )
    expect(
        "cbp_compute_us20_route_loss_from_selling_efficiency = yes" in goods_wrapper,
        "US20 live wrapper must call the compatibility-named read-only helper",
    )
    expect(
        "cbp_apply_us20_goods_delta_to_target_market_good = yes" in goods_wrapper,
        "US20 live wrapper must preserve centralized goods reconciliation",
    )
    expect("add_gold" not in goods_wrapper, "US20 goods wrapper must never mutate money")

    expected_auto_modifiers = [
        ("cbp_us17_selling_efficiency_cancellation", "cbp_us17_native_selling_correction", "selling_efficiency"),
        ("cbp_us17_import_efficiency_cancellation", "cbp_us17_native_import_correction", "import_efficiency"),
        ("cbp_us17_export_efficiency_cancellation", "cbp_us17_native_export_correction", "export_efficiency"),
        (
            "cbp_us17_merchant_maintenance_reconciliation",
            "cbp_us17_native_maintenance_correction",
            "merchant_maintenance_efficiency",
        ),
    ]
    for modifier_name, variable_name, modifier_type in expected_auto_modifiers:
        modifier_block = block(native_auto_modifiers, modifier_name)
        expect(
            re.search(
                rf"scales_with\s*=\s*\{{[^{{}}]*value\s*=\s*var:{variable_name}[^{{}}]*\}}",
                modifier_block,
                re.DOTALL,
            )
            is not None,
            f"{modifier_name} must scale from its persisted correction",
        )
        expect(f"{modifier_type} = 1" in modifier_block, f"{modifier_name} must write {modifier_type}")
        expect(
            "cbp_trade_rework_enabled_trigger = yes" in modifier_block,
            f"{modifier_name} must remain gated",
        )
        expect(
            f"AUTO_MODIFIER_NAME_{modifier_name}" in native_localization,
            f"Missing localization for {modifier_name}",
        )
    expect(
        native_auto_modifiers.count("requires_real = no") == 4,
        "US17 must expose exactly four auto-modifiers",
    )

    policy_hook = block(country_governance_on_actions, "on_policy_changed")
    reform_hook = block(country_governance_on_actions, "on_reform_change")
    shared_dispatcher = block(country_governance_on_actions, "cbp_country_governance_changed")
    expect(
        re.findall(r"\bcbp_[a-z0-9_]+\b", policy_hook) == ["cbp_country_governance_changed"],
        "on_policy_changed must use only shared dispatcher",
    )
    expect(
        re.findall(r"\bcbp_[a-z0-9_]+\b", reform_hook) == ["cbp_country_governance_changed"],
        "on_reform_change must use only shared dispatcher",
    )
    expect(
        len(re.findall(r"(?m)^on_policy_changed\s*=", all_cbp_on_actions)) == 1,
        "CBP must register on_policy_changed exactly once",
    )
    expect(
        len(re.findall(r"(?m)^on_reform_change\s*=", all_cbp_on_actions)) == 1,
        "CBP must register on_reform_change exactly once",
    )
    expect(
        shared_dispatcher.count("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes") == 1,
        "Shared governance dispatcher must refresh US17 state exactly once",
    )

    for token in [
        "namespace = cbp_us17_owner_modifiers",
        "cbp_us17_owner_modifiers.1",
        "cbp_us17_owner_modifiers.11",
        "cbp_debug_run_us17_owner_modifier_probe = yes",
        "cbp_debug_finish_us17_owner_modifier_probe = yes",
    ]:
        expect(token in owner_modifier_probe_events, f"US17 focused event surface must contain {token}")

    for assertion in [
        "shared_coefficient_calculated_upstream",
        "selling_correction_uses_shared_coefficient",
        "import_price_effect_cancelled",
        "export_price_effect_cancelled",
        "maintenance_vanilla_half_term",
        "maintenance_directional_five_term",
        "mixed_denominator_formula",
        "mixed_denominator_maintenance_target",
        "mixed_denominator_maintenance_correction",
        "selling_effective_shared_residual",
        "effective_import_zero",
        "effective_export_zero",
        "us20_trade_volume_times_persisted_coefficient",
        "idempotent_selling_baseline",
        "idempotent_import_baseline",
        "idempotent_export_baseline",
        "idempotent_maintenance_baseline",
        "mixed_denominator_formula=verified",
    ]:
        expect(assertion in owner_modifier_probe_effects, f"Focused probe must assert {assertion}")

    expect(
        "value = scope:cbp_trade_owner_goods_quantity" in trade_values,
        "Trade route quantity script value must remain available",
    )
    expect(
        "define:NCountry|MERCHANT_MAINTENANCE_COST" in trade_values,
        "Loaded base maintenance engine Define must remain available",
    )


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
    expect = legacy.expect
    block = legacy.block
    country_cycle = block(country_trade_owner_effects, "cbp_run_monthly_country_trade_owner_cycle")
    live_hook_call = "cbp_run_us20_route_loss_reconciliation = yes"
    us17_compatibility_hook = "cbp_run_us17_operation_aware_route_profit_reconciliation = yes"
    legacy_hook_call = "cbp_run_us17_us20_route_reconciliation = yes"
    e2e_probe_call = "cbp_debug_run_us20_case12_market_loss_probe = yes"

    expect(
        country_cycle.count(live_hook_call) == 1,
        "Country trade-owner cycle must call US20 route loss exactly once per enabled trade",
    )
    expect(
        country_cycle.count(us17_compatibility_hook) == 1,
        "Country cycle may retain exactly one zero-delta US17 compatibility hook",
    )
    expect(legacy_hook_call not in country_cycle, "Live country cycle must not call historical seeded wrapper")
    expect(
        country_cycle.count("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes") == 1,
        "Country cycle must refresh shared country state once when trade rework is enabled",
    )
    expect(
        country_cycle.index("cbp_trade_rework_enabled_trigger = yes")
        < country_cycle.index("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes")
        < country_cycle.index("every_trade = {")
        < country_cycle.index(us17_compatibility_hook)
        < country_cycle.index(live_hook_call),
        "Trade rework order must remain gate -> refresh -> every_trade -> US17 -> US20",
    )
    expect(
        country_cycle.count("cbp_trade_rework_enabled_trigger = yes") == 1,
        "Country trade-owner cycle must use one authoritative trade-rework gate",
    )
    expect(
        "cbp_clear_us17_native_profit_modifiers_for_current_country = yes" in country_cycle,
        "Disabled trade-rework branch must clear persisted US17/US20 country state",
    )
    expect("every_trade = {" in country_cycle, "Country cycle must use native every_trade iterator")

    compatibility_money = block(
        owner_modifier_effects,
        "cbp_run_us17_operation_aware_route_profit_reconciliation",
    )
    expect("add_gold" not in compatibility_money, "US17 compatibility hook must contain no treasury mutation")
    expect(
        "gui_cbp_trade_efficiency_route_money_delta value = 0" in compatibility_money,
        "US17 compatibility hook must return zero",
    )
    expect(
        "cbp_compute_us20_route_loss_coefficient_from_selling_baseline" in owner_modifier_effects,
        "Production must expose upstream shared Selling coefficient helper",
    )
    expect(
        "cbp_compute_us20_route_loss_from_selling_efficiency" in owner_modifier_effects,
        "Production must retain compatibility-named US20 reader",
    )

    expect(live_hook_call not in q8_7_global_owner_effects, "US20 live hook must not be in market-local body")
    expect(live_hook_call not in stock_on_actions, "US20 live hook must not be directly in monthly on_actions")
    expect(us17_compatibility_hook not in q8_7_global_owner_effects, "US17 hook must not be in market-local body")
    expect(us17_compatibility_hook not in stock_on_actions, "US17 hook must not be directly in monthly on_actions")
    expect(
        "every_market_center_in_country = {"
        not in country_trade_owner_effects
        + q8_7_global_owner_effects
        + trade_reconciliation_effects
        + owner_modifier_effects,
        "Trade rework must not reintroduce a second market-center every_trade scaffold",
    )

    unsafe_global_counter = re.compile(
        r"set_global_variable\s*=\s*\{[^{}]*name\s*=\s*cbp_(?:trade_efficiency|us20)[^{}]*value\s*=\s*\{\s*value\s*=\s*global_var:",
        re.DOTALL,
    )
    expect(
        unsafe_global_counter.search(trade_reconciliation_effects + owner_modifier_effects) is None,
        "US17/US20 counters must use change_global_variable after initialization",
    )
    expect(
        "change_global_variable = { name = cbp_trade_efficiency_routes_seen add = 1 }"
        in trade_reconciliation_effects,
        "Route-seen counter must retain safe increment semantics",
    )
    expect(
        "change_global_variable = { name = cbp_us20_market_goods_supply_loss_routes add = 1 }"
        in trade_reconciliation_effects,
        "US20 market-loss counter must retain safe increment semantics",
    )

    for token, message in [
        (
            "save_temporary_scope_as = cbp_vanilla_market_goods_supply_good",
            "US20 must pass saved route good to central market helper",
        ),
        (
            "name = cbp_vanilla_market_goods_supply_delta value = scope:gui_cbp_us20_market_goods_supply_delta",
            "US20 must pass negative market delta to central helper",
        ),
        (
            "cbp_apply_vanilla_market_goods_supply_delta_from_saved_good = yes",
            "US20 must apply market loss through central helper",
        ),
        (
            "cbp_select_us20_goods_receiver_country_for_promoted_market = yes",
            "Promoted destinations must select receiver before country-stock loss",
        ),
    ]:
        expect(token in trade_reconciliation_effects, message)

    expect(e2e_probe_call not in revalidate_events, "Experimental US20 E2E probe must remain outside stable revalidation")
    expect("Step 13/13" in revalidate_events, "Stable revalidation must retain final US17/US20 scenario")
    expect(e2e_probe_call in us20_probe_events, "Standalone US20 probe must call E2E effect")
    expect("namespace = cbp_us20_probe" in us20_probe_events, "Standalone US20 probe namespace must remain")

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


legacy.validate_us17_owner_modifier_contract = validate_us17_owner_modifier_contract
legacy.validate_us17_us20_static_contract = validate_us17_us20_static_contract


def main() -> int:
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())

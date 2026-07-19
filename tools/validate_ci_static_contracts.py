#!/usr/bin/env python3
"""Static contracts for the stacked shared-Selling / 50-50 maintenance model."""

from __future__ import annotations

import re

import validate_ci_static_contracts_legacy as legacy


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
    defines = legacy.read("loading_screen/common/defines/cbp_trade_defines.txt")

    for token in [
        "CBP_ROUTE_LOSS_COEFFICIENT_MAX = 0.05",
        "CBP_ROUTE_LOSS_COEFFICIENT_CURVE = 10",
        "CBP_TRADE_MAINTENANCE_VANILLA_WEIGHT = 0.5",
        "CBP_TRADE_MAINTENANCE_DIRECTIONAL_WEIGHT = 0.5",
        "CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE = 10",
    ]:
        expect(token in defines, f"US17/US20 defines must contain {token}")

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
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_MAX",
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_CURVE",
        "cbp_us20_route_loss_coefficient_result",
        "divide = scope:cbp_us20_route_loss_denominator",
    ]:
        expect(token in coefficient_formula, f"Shared Selling coefficient must contain {token}")
    expect(
        coefficient_formula.count("divide = scope:") == 1,
        "Shared Selling coefficient must contain exactly one reciprocal",
    )
    expect("set_variable" not in coefficient_formula, "Coefficient helper must remain pure")

    for token in [
        "cbp_us17_native_selling_correction_result",
        "var:cbp_us20_route_loss_coefficient",
        "cbp_us17_native_import_correction_result",
        "cbp_us17_native_export_correction_result",
        "cbp_us17_directional_maintenance_denominator",
        "define:NCountry|CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE",
        "define:NCountry|CBP_TRADE_MAINTENANCE_VANILLA_WEIGHT",
        "define:NCountry|CBP_TRADE_MAINTENANCE_DIRECTIONAL_WEIGHT",
        "cbp_us17_native_effective_maintenance_result",
        "cbp_us17_native_maintenance_correction_result",
    ]:
        expect(token in correction_formula, f"US17 50/50 formula must contain {token}")

    expect(
        "CBP_ROUTE_LOSS_COEFFICIENT_MAX" not in correction_formula
        and "CBP_ROUTE_LOSS_COEFFICIENT_CURVE" not in correction_formula,
        "US17 Selling must consume the persisted coefficient without recalculating it",
    )
    expect(
        "CBP_TRADE_EFFICIENCY_COMPENSATION_MAX" not in correction_formula
        and "CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE" not in correction_formula,
        "Import and Export must be cancelled, not replaced by residual price curves",
    )
    expect(
        correction_formula.count("divide = scope:") == 1,
        "Only the directional maintenance half may contain a reciprocal",
    )
    expect(
        "value = scope:cbp_us17_native_baseline_import_efficiency\n\t\t\tmultiply = -1"
        in correction_formula,
        "Import correction must cancel the full baseline",
    )
    expect(
        "value = scope:cbp_us17_native_baseline_export_efficiency\n\t\t\tmultiply = -1"
        in correction_formula,
        "Export correction must cancel the full baseline",
    )

    for semantic_name in ["selling", "import", "export", "maintenance"]:
        expect(
            f"cbp_us17_native_previous_{semantic_name}_correction" in reconstruction,
            f"Baseline reconstruction must remove previous {semantic_name} correction",
        )
        expect(
            f"cbp_us17_native_{semantic_name}_baseline" in refresh,
            f"Refresh must persist {semantic_name} baseline",
        )

    coefficient_call = "cbp_compute_us20_route_loss_coefficient_from_selling_baseline = yes"
    persist_coefficient = (
        "set_variable = { name = cbp_us20_route_loss_coefficient "
        "value = scope:cbp_us20_route_loss_coefficient_result }"
    )
    correction_call = "cbp_compute_us17_native_corrections_from_baselines = yes"
    for token, message in [
        (coefficient_call, "Refresh must calculate shared coefficient"),
        (persist_coefficient, "Refresh must persist shared coefficient"),
        (correction_call, "Refresh must calculate US17 corrections"),
    ]:
        expect(token in refresh, message)
    expect(
        refresh.index(coefficient_call)
        < refresh.index(persist_coefficient)
        < refresh.index(correction_call),
        "Refresh order must remain calculate -> persist -> Selling consume",
    )
    expect(
        "cbp_us17_native_modifier_state_version value = 7" in refresh,
        "Shared-Selling / 50-50 maintenance state must use version 7",
    )
    expect(
        "remove_variable = cbp_us20_route_loss_coefficient" in clear,
        "Disabling trade rework must remove shared coefficient",
    )

    expected_auto_modifiers = [
        ("cbp_us17_selling_efficiency_cancellation", "cbp_us17_native_selling_correction", "selling_efficiency"),
        ("cbp_us17_import_efficiency_cancellation", "cbp_us17_native_import_correction", "import_efficiency"),
        ("cbp_us17_export_efficiency_cancellation", "cbp_us17_native_export_correction", "export_efficiency"),
        ("cbp_us17_merchant_maintenance_reconciliation", "cbp_us17_native_maintenance_correction", "merchant_maintenance_efficiency"),
    ]
    for modifier_name, variable_name, modifier_type in expected_auto_modifiers:
        modifier_block = block(native_auto_modifiers, modifier_name)
        expect(f"value = var:{variable_name}" in modifier_block, f"{modifier_name} must scale from {variable_name}")
        expect(f"{modifier_type} = 1" in modifier_block, f"{modifier_name} must write {modifier_type}")
        expect("cbp_trade_rework_enabled_trigger = yes" in modifier_block, f"{modifier_name} must remain gated")
        expect(f"AUTO_MODIFIER_NAME_{modifier_name}" in native_localization, f"Missing localization for {modifier_name}")
    expect(
        native_auto_modifiers.count("requires_real = no") == 4,
        "US17 must expose exactly four auto-modifiers",
    )

    expect("add_gold" not in money_wrapper, "US17 compatibility hook must not mutate treasury")
    expect(
        "gui_cbp_trade_efficiency_route_money_delta value = 0" in money_wrapper,
        "US17 compatibility hook must expose zero money delta",
    )

    for token in [
        "has_variable = cbp_us20_route_loss_coefficient",
        "value = var:cbp_us20_route_loss_coefficient",
        "cbp_us20_route_loss_coefficient_input",
        "gui_cbp_us20_goods_received_loss",
        "gui_cbp_us20_target_goods_amount_received",
    ]:
        expect(token in us20_route, f"US20 route calculation must contain {token}")
    for forbidden in [
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_MAX",
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_CURVE",
        "divide =",
        "modifier:selling_efficiency",
        "var:cbp_us17_native_selling_baseline",
    ]:
        expect(forbidden not in us20_route, f"US20 must not recalculate coefficient ({forbidden})")
    expect(
        "multiply = scope:cbp_us20_route_loss_coefficient_input" in us20_route,
        "US20 goods loss must multiply trade volume by shared coefficient",
    )
    expect("add_gold" not in goods_wrapper, "US20 goods wrapper must never mutate money")

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
        "Shared governance dispatcher must refresh US17 exactly once",
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
        "directional_maintenance_denominator",
        "maintenance_cost_split_50_50",
        "maintenance_correction_50_50",
        "selling_effective_shared_residual",
        "effective_import_zero",
        "effective_export_zero",
        "idempotent_selling_baseline",
        "idempotent_import_baseline",
        "idempotent_export_baseline",
        "idempotent_maintenance_baseline",
        "selling_shared_coefficient=verified",
        "maintenance_cost_split=50_50",
        "proportional_goods_loss=verified",
    ]:
        expect(assertion in owner_modifier_probe_effects, f"50/50 probe must assert {assertion}")

    expect(
        "value = scope:cbp_trade_owner_goods_quantity" in trade_values,
        "Trade route quantity script value must remain available",
    )
    expect(
        "define:NCountry|MERCHANT_MAINTENANCE_COST" in trade_values,
        "Loaded base maintenance define script value must remain available",
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
    us17_hook = "cbp_run_us17_operation_aware_route_profit_reconciliation = yes"

    expect(country_cycle.count(live_hook_call) == 1, "Country cycle must call US20 once per trade")
    expect(country_cycle.count(us17_hook) == 1, "Country cycle must retain one zero-delta US17 hook")
    expect(
        country_cycle.count("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes") == 1,
        "Country cycle must refresh shared country state once",
    )
    expect(
        country_cycle.index("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes")
        < country_cycle.index("every_trade = {"),
        "Country refresh must precede every_trade",
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
    expect(live_hook_call not in q8_7_global_owner_effects, "US20 live hook must not be in market-local body")
    expect(live_hook_call not in stock_on_actions, "US20 live hook must not be directly in monthly on_actions")

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
    expect(
        "cbp_apply_vanilla_market_goods_supply_delta_from_saved_good = yes"
        in trade_reconciliation_effects,
        "US20 must preserve central market-supply helper",
    )
    expect(
        "cbp_select_us20_goods_receiver_country_for_promoted_market = yes"
        in trade_reconciliation_effects,
        "Promoted destinations must select receiver",
    )

    expect("namespace = cbp_us20_probe" in us20_probe_events, "Standalone US20 probe namespace must remain")
    for assertion in [
        "case1_classification_expected=1",
        "case2_classification_expected=1",
        "case3_classification_expected=2",
        "case4_classification_expected=1",
        "market_goods_supply_loss_routes_expected=5",
        "promoted_destination_country_loss_routes_expected=3",
        "receivers=explicit_plus_trade_owner_plus_allocator",
    ]:
        expect(assertion in us20_probe_effects, f"US20 E2E probe must assert {assertion}")


legacy.validate_us17_owner_modifier_contract = validate_us17_owner_modifier_contract
legacy.validate_us17_us20_static_contract = validate_us17_us20_static_contract


def main() -> int:
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())

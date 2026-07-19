#!/usr/bin/env python3
"""Static CI contracts for reciprocal US-17 maintenance and separated US-20 loss.

The complete pre-existing validator remains in
``validate_ci_static_contracts_legacy.py``. This entry point replaces only the
US-17/US-20 contracts whose business rules changed, then delegates to legacy.
"""

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
        "CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT = 0.5",
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

    # US-20 retains one independently persisted Selling-driven goods-loss curve.
    for token in [
        "cbp_us17_native_baseline_selling_efficiency",
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_MAX",
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_CURVE",
        "cbp_us20_route_loss_denominator",
        "cbp_us20_route_loss_coefficient_result",
        "divide = scope:cbp_us20_route_loss_denominator",
        "min = 0.01",
    ]:
        expect(token in coefficient_formula, f"US20 coefficient formula must contain {token}")
    expect(
        coefficient_formula.count("divide = scope:") == 1,
        "US20 coefficient helper must contain exactly one reciprocal curve",
    )
    expect(
        "set_variable" not in coefficient_formula,
        "US20 coefficient helper must be pure; country refresh owns persistence",
    )

    # US-17 must cancel directional price effects and move them into maintenance.
    for token in [
        "cbp_us17_native_import_correction_result",
        "cbp_us17_native_export_correction_result",
        "cbp_us17_native_baseline_import_efficiency",
        "cbp_us17_native_baseline_export_efficiency",
        "cbp_us17_native_baseline_maintenance_efficiency",
        "cbp_us17_directional_maintenance_term",
        "define:NCountry|CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT",
        "define:NCountry|CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE",
        "cbp_us17_maintenance_curve_denominator",
        "cbp_us17_maintenance_curve_reciprocal",
        "cbp_us17_native_effective_maintenance_result",
        "cbp_us17_native_maintenance_correction_result",
        "divide = scope:cbp_us17_maintenance_curve_denominator",
        "min = 0.01",
    ]:
        expect(token in correction_formula, f"US17 reciprocal formula must contain {token}")

    expect(
        correction_formula.count("multiply = -1") >= 4,
        "US17 must cancel Import/Export and form reciprocal/correction differences",
    )
    expect(
        correction_formula.count("divide = scope:") == 1,
        "US17 reciprocal maintenance formula must contain exactly one division",
    )
    for forbidden in [
        "cbp_us17_native_selling_correction_result",
        "var:cbp_us20_route_loss_coefficient",
        "CBP_ROUTE_LOSS_COEFFICIENT_MAX",
        "CBP_ROUTE_LOSS_COEFFICIENT_CURVE",
        "CBP_TRADE_EFFICIENCY_COMPENSATION_MAX",
    ]:
        expect(
            forbidden not in correction_formula,
            f"US17 reciprocal maintenance must be independent of {forbidden}",
        )

    # Selling remains native; I, Ex and M reconstruct idempotently.
    expect(
        "value = scope:cbp_us17_native_effective_selling_efficiency" in reconstruction,
        "Selling baseline must equal the untouched native effective Selling Efficiency",
    )
    expect(
        "cbp_us17_native_previous_selling_correction" not in reconstruction,
        "Selling reconstruction must not subtract a CBP correction",
    )
    for semantic_name in ["import", "export", "maintenance"]:
        expect(
            f"cbp_us17_native_previous_{semantic_name}_correction" in reconstruction,
            f"US17 reconstruction must remove previous {semantic_name} correction",
        )
        expect(
            f"cbp_us17_native_{semantic_name}_baseline" in refresh,
            f"US17 refresh must persist reconstructed {semantic_name} baseline",
        )

    coefficient_call = "cbp_compute_us20_route_loss_coefficient_from_selling_baseline = yes"
    persist_coefficient = (
        "set_variable = { name = cbp_us20_route_loss_coefficient "
        "value = scope:cbp_us20_route_loss_coefficient_result }"
    )
    correction_call = "cbp_compute_us17_native_corrections_from_baselines = yes"
    for token, message in [
        (coefficient_call, "Country refresh must calculate US20 coefficient"),
        (persist_coefficient, "Country refresh must persist US20 coefficient"),
        (correction_call, "Country refresh must calculate US17 reciprocal corrections"),
        (
            "set_variable = { name = cbp_us17_native_maintenance_correction value = scope:cbp_us17_native_maintenance_correction_result }",
            "Country refresh must persist maintenance correction",
        ),
        (
            "set_variable = { name = cbp_us17_native_modifier_state_version value = 7 }",
            "Reciprocal-maintenance state must use version 7",
        ),
        (
            "remove_variable = cbp_us17_native_selling_correction",
            "Migration must remove stale Selling correction",
        ),
    ]:
        expect(token in refresh, message)

    expect(
        refresh.index(coefficient_call)
        < refresh.index(persist_coefficient)
        < refresh.index(correction_call),
        "Country refresh must persist US20 state before the route pass and then compute US17",
    )
    expect(
        "remove_variable = cbp_us20_route_loss_coefficient" in clear,
        "Disabling trade rework must remove the US20 coefficient",
    )
    expect(
        "cbp_us17_native_modifier_state_version value = 7" in clear,
        "Clear path must migrate to state version 7",
    )

    expect("add_gold" not in money_wrapper, "US17 compatibility hook must not mutate treasury")
    expect(
        "gui_cbp_trade_efficiency_route_money_delta value = 0" in money_wrapper,
        "US17 compatibility hook must expose a zero money delta",
    )

    # US-20 reads the persisted coefficient and multiplies it by route volume only.
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
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_MAX",
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_CURVE",
        "divide =",
        "modifier:selling_efficiency",
    ]:
        expect(forbidden not in us20_route, f"US20 route must not recalculate coefficient ({forbidden})")
    expect(
        "value = scope:gui_cbp_us20_goods_amount_sent" in us20_route
        and "multiply = scope:cbp_us20_route_loss_coefficient_input" in us20_route,
        "US20 goods loss must equal trade volume multiplied by persisted coefficient",
    )
    expect(
        "cbp_compute_us20_route_loss_from_selling_efficiency = yes" in goods_wrapper,
        "US20 live wrapper must call its read-only coefficient consumer",
    )
    expect("add_gold" not in goods_wrapper, "US20 goods wrapper must never mutate money")

    expected_auto_modifiers = [
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
        expect("cbp_trade_rework_enabled_trigger = yes" in modifier_block, f"{modifier_name} must remain gated")
        expect(f"AUTO_MODIFIER_NAME_{modifier_name}" in native_localization, f"Missing localization for {modifier_name}")
    expect(
        "cbp_us17_selling_efficiency_cancellation" not in native_auto_modifiers,
        "US17 must not alter Selling Efficiency",
    )
    expect(
        native_auto_modifiers.count("requires_real = no") == 3,
        "US17 must expose exactly Import, Export and Merchant Maintenance modifiers",
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
        "Shared governance dispatcher must refresh US17/US20 country state exactly once",
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
        "reciprocal_denominator_formula",
        "reciprocal_maintenance_target",
        "reciprocal_maintenance_correction",
        "selling_untouched",
        "effective_import_zero",
        "effective_export_zero",
        "idempotent_maintenance_baseline",
        "live_selling_untouched",
        "live_import_cancelled",
        "live_export_cancelled",
        "live_reciprocal_maintenance_applied",
        "us20_coefficient_persisted_separately",
        "us20_trade_volume_times_persisted_coefficient",
        "reciprocal_maintenance_formula=verified",
        "import_export_price_effect=zero",
        "us20_coefficient=separate",
    ]:
        expect(assertion in owner_modifier_probe_effects, f"Reciprocal-maintenance probe must assert {assertion}")

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
    us17_compatibility_hook = "cbp_run_us17_operation_aware_route_profit_reconciliation = yes"
    legacy_hook_call = "cbp_run_us17_us20_route_reconciliation = yes"

    expect(country_cycle.count(live_hook_call) == 1, "Country cycle must call US20 once per trade")
    expect(
        country_cycle.count(us17_compatibility_hook) == 1,
        "Country cycle may retain exactly one zero-delta US17 compatibility hook",
    )
    expect(legacy_hook_call not in country_cycle, "Live country cycle must not call historical seeded wrapper")
    expect(
        country_cycle.count("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes") == 1,
        "Country cycle must refresh US17/US20 country state once before every_trade",
    )
    expect(
        country_cycle.index("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes")
        < country_cycle.index("every_trade = {"),
        "Country refresh must precede every_trade",
    )
    expect(
        country_cycle.index(us17_compatibility_hook) < country_cycle.index(live_hook_call),
        "Zero-delta US17 hook must precede US20 goods reconciliation",
    )

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
        "Production must expose the separated US20 coefficient helper",
    )
    expect(
        "cbp_compute_us20_route_loss_from_selling_efficiency" in owner_modifier_effects,
        "Production must retain the US20 coefficient consumer",
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

    expect(
        "cbp_apply_vanilla_market_goods_supply_delta_from_saved_good = yes" in trade_reconciliation_effects,
        "US20 must preserve centralized market-goods reconciliation",
    )
    expect(
        "cbp_select_us20_goods_receiver_country_for_promoted_market = yes" in trade_reconciliation_effects,
        "Promoted destinations must select receiver before country-stock loss",
    )
    expect(
        "namespace = cbp_us20_probe" in us20_probe_events,
        "Standalone US20 probe namespace must remain",
    )
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
    expect("Step 13/13" in revalidate_events, "Stable revalidation must retain final US17/US20 scenario")


legacy.validate_us17_owner_modifier_contract = validate_us17_owner_modifier_contract
legacy.validate_us17_us20_static_contract = validate_us17_us20_static_contract


def main() -> int:
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())

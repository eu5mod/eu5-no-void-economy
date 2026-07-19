#!/usr/bin/env python3
"""Static CI contracts for the stacked US-17/US-20 shared-coefficient model.

The complete pre-existing validator remains in
``validate_ci_static_contracts_legacy.py``. This entry point replaces only the
two contracts whose business rules changed, then delegates to the legacy main so
all unrelated checks remain active.
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
        "CBP_TRADE_EFFICIENCY_COMPENSATION_MAX = 0.05",
        "CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE = 10",
    ]:
        expect(token in defines, f"US17/US20 defines must contain {token}")

    expect(
        "CBP_ROUTE_LOSS_MAX = 0.05" in defines
        and "CBP_ROUTE_LOSS_CURVE = 10" in defines,
        "Previous route-loss define names must remain as temporary aliases",
    )
    expect(
        "CBD_TRADE_MAINTENANCE_MAX_IMPACT = 0.05" in defines,
        "Historical deterministic fixture alias must remain available",
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

    # One pure calculation creates the country coefficient candidate.
    for token in [
        "cbp_us17_native_baseline_selling_efficiency",
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_MAX",
        "define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_CURVE",
        "cbp_us20_route_loss_denominator",
        "cbp_us20_route_loss_coefficient_result",
        "divide = scope:cbp_us20_route_loss_denominator",
        "min = 0.01",
    ]:
        expect(token in coefficient_formula, f"Shared coefficient formula must contain {token}")
    expect(
        coefficient_formula.count("divide = scope:") == 1,
        "Shared coefficient helper must contain exactly one reciprocal curve",
    )
    expect(
        "set_variable" not in coefficient_formula,
        "Pure coefficient helper must return a temporary result; refresh owns persistence",
    )

    # US-17 Selling consumes the persisted country variable. It must not calculate
    # the reciprocal Selling curve again.
    for token in [
        "cbp_us17_native_baseline_selling_efficiency",
        "var:cbp_us20_route_loss_coefficient",
        "cbp_us17_native_selling_correction_result",
        "cbp_us17_native_baseline_import_efficiency",
        "define:NCountry|CBP_TRADE_EFFICIENCY_COMPENSATION_MAX",
        "define:NCountry|CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE",
        "cbp_us17_native_import_correction_result",
        "cbp_us17_native_baseline_export_efficiency",
        "cbp_us17_native_export_correction_result",
    ]:
        expect(token in correction_formula, f"US17 correction formula must contain {token}")

    expect(
        "CBP_ROUTE_LOSS_COEFFICIENT_MAX" not in correction_formula
        and "CBP_ROUTE_LOSS_COEFFICIENT_CURVE" not in correction_formula,
        "US17 Selling correction must not recalculate the shared curve",
    )
    expect(
        "scope:cbp_us20_route_loss_coefficient_result" not in correction_formula,
        "US17 Selling must read the persisted country variable, not the temporary result",
    )
    expect(
        correction_formula.count("divide = scope:") == 2,
        "Only Import and Export may evaluate reciprocal curves inside US17 corrections",
    )
    expect(
        correction_formula.count("min = 0.01") == 2,
        "Only the two directional curves require denominator safety floors here",
    )
    expect(
        "cbp_us17_native_maintenance_correction_result" not in correction_formula,
        "US17 must not calculate a Merchant Maintenance correction",
    )
    expect(
        "merchant_maintenance_efficiency" not in native_auto_modifiers,
        "US17 must not write the native Merchant Maintenance surface",
    )
    expect(
        "cbp_us17_merchant_maintenance_reconciliation" not in native_auto_modifiers,
        "Previous fourth auto-modifier must be removed",
    )

    for semantic_name in ["selling", "import", "export"]:
        expect(
            f"cbp_us17_native_previous_{semantic_name}_correction" in reconstruction,
            f"US17 refresh must remove its previous {semantic_name} correction",
        )
        expect(
            f"cbp_us17_native_{semantic_name}_baseline" in refresh,
            f"US17 refresh must persist its reconstructed {semantic_name} baseline",
        )

    expect(
        "cbp_us17_native_previous_maintenance_correction" not in reconstruction,
        "Baseline reconstruction must not subtract stale maintenance correction",
    )
    expect(
        "value = scope:cbp_us17_native_effective_maintenance_efficiency" in reconstruction,
        "Diagnostic maintenance baseline must equal native effective value",
    )

    coefficient_call = "cbp_compute_us20_route_loss_coefficient_from_selling_baseline = yes"
    persist_coefficient = (
        "set_variable = { name = cbp_us20_route_loss_coefficient "
        "value = scope:cbp_us20_route_loss_coefficient_result }"
    )
    correction_call = "cbp_compute_us17_native_corrections_from_baselines = yes"

    for token, message in [
        (coefficient_call, "Country refresh must calculate the shared coefficient"),
        (persist_coefficient, "Country refresh must persist the shared coefficient"),
        (correction_call, "Country refresh must calculate US17 corrections"),
    ]:
        expect(token in refresh, message)

    expect(
        refresh.index(coefficient_call)
        < refresh.index(persist_coefficient)
        < refresh.index(correction_call),
        "Country refresh order must be calculate -> persist -> US17 consume",
    )
    expect(
        refresh.count(persist_coefficient) == 1,
        "Country refresh must persist cbp_us20_route_loss_coefficient exactly once",
    )
    expect(
        "cbp_us17_native_modifier_state_version value = 6" in refresh,
        "Shared-coefficient state must use version 6",
    )
    expect(
        "remove_variable = cbp_us20_route_loss_coefficient" in clear,
        "Disabling trade rework must remove the shared coefficient",
    )
    expect(
        "remove_variable = cbp_us17_native_maintenance_correction" in refresh + clear,
        "Migration must remove stale maintenance correction state",
    )
    expect(
        "remove_variable = cbp_us17_native_maintenance_baseline" in refresh + clear,
        "Migration must remove stale maintenance baseline state",
    )

    expect("add_gold" not in money_wrapper, "US17 compatibility hook must not mutate treasury")
    expect(
        "gui_cbp_trade_efficiency_route_money_delta value = 0" in money_wrapper,
        "US17 compatibility hook must expose a zero money delta",
    )

    # US-20 may only read the persisted coefficient and multiply it by route volume.
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
        "var:cbp_us17_native_selling_baseline",
    ]:
        expect(
            forbidden not in us20_route,
            f"US20 must not recalculate shared coefficient ({forbidden})",
        )

    expect(
        "value = scope:gui_cbp_us20_goods_amount_sent" in us20_route
        and "multiply = scope:cbp_us20_route_loss_coefficient_input" in us20_route,
        "US20 goods loss must equal trade volume multiplied by persisted coefficient",
    )
    expect(
        "value = scope:cbp_us20_route_loss_coefficient_input" in us20_route,
        "Historical loss-factor diagnostic must carry the shared coefficient",
    )
    expect(
        "cbp_compute_us20_route_loss_from_selling_efficiency = yes" in goods_wrapper,
        "US20 live wrapper must call compatibility-named read-only helper",
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
        native_auto_modifiers.count("requires_real = no") == 3,
        "US17 must expose exactly three curve auto-modifiers",
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
        "Shared governance dispatcher must refresh shared coefficient exactly once",
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
        "import_curve_correction_formula",
        "export_curve_correction_formula",
        "merchant_maintenance_baseline_unchanged",
        "route_money_delta_zero",
        "shared_coefficient_persisted_upstream",
        "us20_reads_persisted_shared_coefficient",
        "selling_uses_shared_coefficient",
        "us20_trade_volume_times_persisted_coefficient",
        "us20_proportional_loss_subtracted",
        "idempotent_selling_baseline",
        "idempotent_import_baseline",
        "idempotent_export_baseline",
        "live_merchant_maintenance_untouched",
        "coefficient_calculated_upstream=verified",
        "selling_us20_coefficient=shared",
        "us20_recalculation=absent",
        "proportional_goods_loss=verified",
    ]:
        expect(assertion in owner_modifier_probe_effects, f"Shared-coefficient probe must assert {assertion}")

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
    e2e_probe_call = "cbp_debug_run_us20_case12_market_loss_probe = yes"

    expect(
        country_cycle.count(live_hook_call) == 1,
        "Country trade-owner cycle must call US20 route loss exactly once per trade",
    )
    expect(
        country_cycle.count(us17_compatibility_hook) == 1,
        "Country cycle may retain exactly one zero-delta US17 compatibility hook",
    )
    expect(legacy_hook_call not in country_cycle, "Live country cycle must not call historical seeded wrapper")
    expect(
        country_cycle.count("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes") == 1,
        "Country cycle must refresh shared country state once before every_trade",
    )
    expect(
        country_cycle.index("cbp_refresh_us17_native_profit_modifiers_for_current_country = yes")
        < country_cycle.index("every_trade = {"),
        "Shared coefficient refresh must precede every_trade",
    )
    expect(
        country_cycle.index(us17_compatibility_hook) < country_cycle.index(live_hook_call),
        "Zero-delta US17 hook must precede US20 goods reconciliation",
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
        "Production must expose upstream shared-coefficient helper",
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

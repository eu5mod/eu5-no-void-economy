#!/usr/bin/env python3
"""Validate that hot-path observability counters are debug/audit-only.

This validator deliberately checks named scripted-effect contracts rather than
trying to interpret every Paradox script expression. It protects two properties:

1. every selected counter family is owned by an effect containing the shared
   ``cbp_observability_enabled_trigger`` gate;
2. the business iterators, work lists, ordering, and mutation calls remain in
   their owning effects independently of observability.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = "cbp_observability_enabled_trigger = yes"


class ContractError(RuntimeError):
    """Raised when a static observability contract is violated."""


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def named_block(text: str, name: str) -> str:
    marker = f"{name} = {{"
    start = text.find(marker)
    if start < 0:
        raise ContractError(f"Missing scripted block: {name}")

    brace_start = text.find("{", start)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace_start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ContractError(f"Unclosed scripted block: {name}")


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def expect_gated(text: str, names: tuple[str, ...]) -> None:
    for name in names:
        block = named_block(text, name)
        expect(GATE in block, f"Observability effect must use shared gate: {name}")


def validate_trigger_contract() -> None:
    text = read("in_game/common/scripted_triggers/cbp_configuration_triggers.txt")
    gate = named_block(text, "cbp_observability_enabled_trigger")
    expect(
        "cbp_debug_capture_enabled_trigger = yes" in gate,
        "Observability gate must include debug capture",
    )
    expect(
        "cbp_audit_enabled_trigger = yes" in gate,
        "Observability gate must include audit mode",
    )
    pr71 = named_block(text, "cbp_pr71_metrics_enabled_trigger")
    expect(
        "cbp_observability_enabled_trigger = yes" in pr71,
        "PR7.1 metrics trigger must delegate to the shared observability gate",
    )


def validate_q87() -> None:
    text = read("in_game/common/scripted_effects/cbp_q8_7_global_owner_effects.txt")
    expect_gated(
        text,
        (
            "cbp_reset_q8_7_live_global_owner_metrics",
            "cbp_note_q8_7_live_global_owner_run",
            "cbp_note_q8_7_live_global_owner_skip_run",
            "cbp_note_q8_7_live_global_owner_market_seen",
            "cbp_note_q8_7_live_global_owner_detailed_market",
            "cbp_note_q8_7_live_global_owner_fallback_market",
            "cbp_note_q8_7_live_global_owner_blocked_market",
        ),
    )
    owner = named_block(text, "cbp_run_monthly_q8_7_global_market_local_cycle_once")
    for token in (
        "cbp_q8_7_live_global_owner_month_stamp",
        "every_market_in_world",
        "cbp_q8_7_run_global_market_local_owner_market",
    ):
        expect(token in owner, f"Q8.7 business owner lost token: {token}")
    cycle = named_block(text, "cbp_run_monthly_stock_cycle_q8_7_owner_switch")
    for token in (
        "cbp_run_monthly_capacity_refresh_for_current_country",
        "cbp_run_monthly_country_trade_owner_cycle",
        "cbp_run_monthly_us04_reconciliation_for_current_country",
    ):
        expect(token in cycle, f"Monthly economic order lost token: {token}")


def validate_market_country_cache() -> None:
    text = read("in_game/common/scripted_effects/cbp_market_country_cache_effects.txt")
    expect_gated(
        text,
        (
            "cbp_clear_countries_present_in_market_work_cache",
            "cbp_increment_market_country_cache_location_scan",
            "cbp_increment_market_country_cache_location_with_owner",
            "cbp_increment_market_country_cache_country_added",
            "cbp_rebuild_countries_present_in_market",
            "cbp_repair_dirty_market_country_caches",
        ),
    )
    clear = named_block(text, "cbp_clear_countries_present_in_market_work_cache")
    expect(
        "clear_global_variable_list = cbp_countries_present_in_market" in clear,
        "Countries-present work list must still clear in every runtime mode",
    )
    add = named_block(text, "cbp_add_country_to_current_market_country_cache")
    expect(
        add.count("add_to_global_variable_list") == 2,
        "Countries-present work list must retain both first-add and deduplicated-add paths",
    )
    rebuild = named_block(text, "cbp_rebuild_countries_present_in_market")
    expect("every_location_in_market" in rebuild, "Market-country cache must retain native location traversal")


def validate_trade_owner() -> None:
    text = read("in_game/common/scripted_effects/cbp_country_trade_owner_effects.txt")
    expect_gated(
        text,
        (
            "cbp_reset_country_trade_owner_pass_metrics",
            "cbp_note_country_trade_owner_pass_run",
            "cbp_note_country_trade_owner_trade_seen",
            "cbp_note_country_trade_owner_inter_market_trade",
            "cbp_note_country_trade_owner_owner_mismatch",
            "cbp_note_country_trade_owner_quantity_confirmed_trade",
            "cbp_note_country_trade_owner_quantity_blocked_trade",
            "cbp_note_country_trade_owner_explicit_request",
            "cbp_note_country_trade_owner_inter_market_transfer",
            "cbp_note_country_trade_owner_outcome_quantities",
        ),
    )
    capture = named_block(text, "cbp_capture_country_trade_owner_trade_quantity")
    for token in ("trade_volume", "cbp_trade_owner_goods_quantity", "cbp_trade_owner_quantity_matched"):
        expect(token in capture, f"Trade quantity capture lost business token: {token}")
    cycle = named_block(text, "cbp_run_monthly_country_trade_owner_cycle")
    for token in (
        "every_trade",
        "cbp_refresh_us17_native_profit_modifiers_for_current_country",
        "cbp_run_us17_operation_aware_route_profit_reconciliation",
        "cbp_run_us20_route_loss_reconciliation",
    ):
        expect(token in cycle, f"Trade-owner cycle lost business token: {token}")


def validate_promoted_market() -> None:
    text = read("in_game/common/scripted_effects/cbp_promoted_market_cycle_effects.txt")
    expect_gated(
        text,
        (
            "cbp_clear_promoted_market_cycle_work_list",
            "cbp_note_promoted_market_cycle_candidate",
            "cbp_note_promoted_market_cycle_rejected",
            "cbp_add_current_market_to_promoted_market_cycle_work_list",
            "cbp_run_monthly_promoted_market_cycle",
            "cbp_reset_promoted_market_local_branch_metrics",
            "cbp_note_promoted_market_local_branch_country_cache_rebuild",
            "cbp_note_promoted_market_local_branch_capacity_country",
            "cbp_note_promoted_market_local_branch_us00",
            "cbp_note_promoted_market_local_branch_us10",
            "cbp_note_promoted_market_local_branch_validation",
            "cbp_run_promoted_market_local_branch_market_good",
            "cbp_reset_promoted_market_live_dispatcher_metrics",
            "cbp_prepare_monthly_promoted_market_live_dispatcher_metrics",
            "cbp_note_promoted_market_live_dispatcher_run",
            "cbp_note_promoted_market_live_detailed_market",
            "cbp_note_promoted_market_live_fallback_market",
            "cbp_note_promoted_market_live_blocked_market",
            "cbp_note_promoted_market_live_country_cache_rebuild",
            "cbp_note_promoted_market_live_capacity_country",
            "cbp_note_promoted_market_live_us00_country_pass",
            "cbp_note_promoted_market_live_us10_country_pass",
            "cbp_note_promoted_market_live_local_market_processed",
            "cbp_note_promoted_market_live_trade_owner_pass",
        ),
    )
    work_list = named_block(text, "cbp_add_current_market_to_promoted_market_cycle_work_list")
    expect(
        work_list.count("add_to_global_variable_list") == 2,
        "Promoted-market work-list additions must remain business-active",
    )
    live = named_block(text, "cbp_run_promoted_market_live_local_branch_market_all_goods")
    us00 = live.find("cbp_pr71_process_us00_monthly_market_active_goods")
    us10 = live.find("cbp_pr71_process_us10_monthly_market_pending_goods")
    expect(us00 >= 0 and us10 > us00, "US-00 must remain before US-10 in the live market branch")
    expect(
        live.count("every_in_global_list") == 2,
        "Live detailed market must retain the two present-country passes",
    )


def validate_performance_helpers() -> None:
    text = read("in_game/common/scripted_effects/cbp_performance_effects.txt")
    expect_gated(
        text,
        (
            "cbp_clear_performance_relevant_markets",
            "cbp_prepare_performance_relevant_market_counters",
            "cbp_mark_performance_relevant_market",
            "cbp_add_country_present_markets_to_performance_relevant_list",
            "cbp_rebuild_human_relevant_markets",
            "cbp_prepare_vanilla_fallback_counters",
            "cbp_note_us00_vanilla_fallback_market",
            "cbp_note_us10_vanilla_fallback_market",
            "cbp_note_runtime_blocked_market",
        ),
    )
    mark = named_block(text, "cbp_mark_performance_relevant_market")
    expect(
        mark.count("add_to_global_variable_list") == 2,
        "Relevant-market work list must retain both add paths",
    )
    promotion = named_block(text, "cbp_promote_market_to_detailed_accounting")
    for token in (
        "cbp_refresh_market_promotion_country_capacities",
        "cbp_promote_market_to_detailed_accounting_all_goods",
        "cbp_mark_market_detailed_accounting_promoted",
        "cbp_perf14_promotion_failure_detected",
    ):
        expect(token in promotion, f"Promotion business contract lost token: {token}")


def main() -> int:
    validate_trigger_contract()
    validate_q87()
    validate_market_country_cache()
    validate_trade_owner()
    validate_promoted_market()
    validate_performance_helpers()
    print("CBP observability gate contracts validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

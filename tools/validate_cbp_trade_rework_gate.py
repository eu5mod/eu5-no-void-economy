#!/usr/bin/env python3
"""Validate that the CMM trade-rework option owns both US-17 and US-20.

The monthly native-trade pass must do no trade iteration when the option is off.
Persisted US-17/US-20 country state must still be cleared through the disabled
branch, while explicit ModeU5-owned transfer requests remain independent.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRADE_GATE = "cbp_trade_rework_enabled_trigger = yes"


class ContractError(RuntimeError):
    """Raised when the static trade-rework contract is violated."""


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def block_from(text: str, start: int) -> tuple[str, int]:
    brace_start = text.find("{", start)
    if brace_start < 0:
        raise ContractError("Missing opening brace")

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
                return text[start : index + 1], index + 1
    raise ContractError("Unclosed scripted block")


def named_block(text: str, name: str) -> str:
    marker = f"{name} = {{"
    start = text.find(marker)
    if start < 0:
        raise ContractError(f"Missing scripted block: {name}")
    block, _ = block_from(text, start)
    return block


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def validate_monthly_cycle() -> None:
    text = read("in_game/common/scripted_effects/cbp_country_trade_owner_effects.txt")
    cycle = named_block(text, "cbp_run_monthly_country_trade_owner_cycle")

    expect(cycle.count(TRADE_GATE) == 1, "Monthly trade cycle must have one authoritative trade-rework gate")
    gate_index = cycle.index(TRADE_GATE)
    gate_start = cycle.rfind("if = {", 0, gate_index)
    expect(gate_start >= 0, "Trade-rework gate must be inside an if block")
    enabled, enabled_end = block_from(cycle, gate_start)

    ordered_tokens = (
        "cbp_refresh_us17_native_profit_modifiers_for_current_country = yes",
        "every_trade = {",
        "cbp_run_us17_operation_aware_route_profit_reconciliation = yes",
        "cbp_run_us20_route_loss_reconciliation = yes",
    )
    positions = [enabled.find(token) for token in ordered_tokens]
    for token, position in zip(ordered_tokens, positions, strict=True):
        expect(position >= 0, f"Enabled trade-rework branch lost token: {token}")
    expect(positions == sorted(positions), "Enabled trade order must remain refresh -> every_trade -> US-17 -> US-20")

    expect(enabled.count("every_trade = {") == 1, "Enabled branch must contain exactly one country-scoped every_trade")
    expect(enabled.count("cbp_run_us17_operation_aware_route_profit_reconciliation = yes") == 1, "US-17 route hook must run exactly once per trade")
    expect(enabled.count("cbp_run_us20_route_loss_reconciliation = yes") == 1, "US-20 route reconciliation must run exactly once per trade")
    expect(TRADE_GATE not in enabled[enabled.index(TRADE_GATE) + len(TRADE_GATE) :], "US-20 must not retain a second nested trade-rework gate")

    outside_enabled = cycle[:gate_start] + cycle[enabled_end:]
    expect("every_trade = {" not in outside_enabled, "Native every_trade must not execute outside the trade-rework gate")
    expect("cbp_run_us17_operation_aware_route_profit_reconciliation = yes" not in outside_enabled, "US-17 route hook must not execute outside the trade-rework gate")
    expect("cbp_run_us20_route_loss_reconciliation = yes" not in outside_enabled, "US-20 must not execute outside the trade-rework gate")
    expect("cbp_clear_us17_native_profit_modifiers_for_current_country = yes" in outside_enabled, "Disabled branch must clear persisted US-17/US-20 country state")

    explicit_request = named_block(text, "cbp_process_country_trade_owner_explicit_request")
    expect(TRADE_GATE not in explicit_request, "Explicit ModeU5 transfer requests must remain independent of native trade rework")
    expect("cbp_handoff_scoped_inter_market_transfer" in explicit_request, "Explicit transfer handler lost central transfer handoff")


def validate_country_state_dispatcher() -> None:
    text = read("in_game/common/scripted_effects/cbp_trade_owner_modifier_reconciliation_effects.txt")
    refresh = named_block(text, "cbp_refresh_us17_native_profit_modifiers_for_current_country")
    expect(TRADE_GATE in refresh, "US-17 country-state refresh must retain its defensive trade-rework gate")
    expect("cbp_clear_us17_native_profit_modifiers_for_current_country = yes" in refresh, "US-17 country-state refresh must clear state when disabled")


def main() -> int:
    validate_monthly_cycle()
    validate_country_state_dispatcher()
    print("CBP trade-rework gate contracts validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

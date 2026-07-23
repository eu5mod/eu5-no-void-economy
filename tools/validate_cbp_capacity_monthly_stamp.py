#!/usr/bin/env python3
"""Static contracts for the monthly country-market capacity stamp."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPACITY = ROOT / "in_game/common/scripted_effects/cbp_capacity_effects.txt"
PROMOTED = ROOT / "in_game/common/scripted_effects/cbp_promoted_market_cycle_effects.txt"
STAMP_MAP = "cbp_capacity_monthly_stamp_by_market"


class ContractError(RuntimeError):
    pass


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def block(text: str, name: str) -> str:
    marker = f"{name} = {{"
    start = text.find(marker)
    if start < 0:
        raise ContractError(f"Missing block: {name}")
    opening = text.find("{", start)
    depth = 0
    in_string = False
    escaped = False
    for index in range(opening, len(text)):
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
    raise ContractError(f"Unclosed block: {name}")


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def main() -> int:
    capacity = read(CAPACITY)
    promoted = read(PROMOTED)

    stamp_formula = block(capacity, "cbp_prepare_country_market_capacity_current_month_stamp")
    for token in ("value = current_year", "multiply = 12", "add = current_month"):
        expect(token in stamp_formula, f"Monthly stamp formula lost token: {token}")

    load = block(capacity, "cbp_load_country_market_capacity_monthly_stamp")
    expect("scope:cbp_country = {" in load, "Stamp map must always be read from saved country scope")
    expect(f"has_variable_map = {STAMP_MAP}" in load, "Stamp loader must test the stamp map")
    expect(f"name = {STAMP_MAP}" in load, "Stamp loader must read the stamp map")
    expect("cbp_capacity_stored_month_stamp value = -1" in load, "Missing stamp must use a stale sentinel")

    store_stamp = block(capacity, "cbp_store_country_market_capacity_current_month_stamp")
    expect("scope:cbp_country = {" in store_stamp, "Stamp writer must use saved country scope")
    expect(f"add_to_variable_map = {{\n\t\t\tname = {STAMP_MAP}" in store_stamp, "Stamp writer must persist by market")
    expect("key = scope:cbp_market" in store_stamp, "Stamp map key must be the current market")

    raw = block(capacity, "cbp_recalculate_country_market_capacity_from_prepared_pool_raw_shared")
    for token in (
        "cbp_apply_country_storage_capacity_pool_to_current_market = yes",
        "cbp_store_capacity_record = yes",
        "cbp_store_country_market_capacity_current_month_stamp = yes",
        "cbp_finalize_country_market_capacity = yes",
    ):
        expect(token in raw, f"Raw prepared-pool writer lost token: {token}")

    gated = block(capacity, "cbp_recalculate_country_market_capacity_from_prepared_pool_shared")
    for token in (
        "cbp_prepare_country_market_capacity_current_month_stamp = yes",
        "cbp_load_country_market_capacity_monthly_stamp = yes",
        "scope:cbp_capacity_stored_month_stamp != scope:cbp_capacity_current_month_stamp",
        "cbp_recalculate_country_market_capacity_from_prepared_pool_raw_shared = yes",
    ):
        expect(token in gated, f"Idempotent country-market gate lost token: {token}")
    expect("cbp_store_capacity_record = yes" not in gated, "Public idempotent gate must delegate rather than write directly")

    monthly_all = block(capacity, "cbp_ensure_saved_country_storage_capacities_current_month")
    expect("every_market_present_in_country = {" in monthly_all, "Monthly preparation must retain all present markets")
    expect("cbp_recalculate_country_market_capacity_from_prepared_pool_shared = yes" in monthly_all, "Monthly preparation must use the idempotent entry point")
    expect("_raw_shared" not in monthly_all, "Monthly preparation must not bypass the stamp")

    forced_all = block(capacity, "cbp_recalculate_saved_country_storage_capacities")
    expect("cbp_recalculate_country_market_capacity_from_prepared_pool_raw_shared = yes" in forced_all, "Forced refresh must bypass the monthly gate")
    expect("cbp_recalculate_country_market_capacity_from_prepared_pool_shared = yes" not in forced_all, "Forced refresh must not be suppressed by an existing stamp")

    monthly_entry = block(capacity, "cbp_run_monthly_capacity_refresh_for_current_country")
    expect("cbp_ensure_saved_country_storage_capacities_current_month = yes" in monthly_entry, "Monthly country pulse must use the ensure path")

    full_writer = block(capacity, "cbp_recalculate_country_market_capacity_shared")
    expect("cbp_store_country_market_capacity_current_month_stamp = yes" in full_writer, "Full capacity recalculation must restamp the market")

    topology = block(capacity, "cbp_rebuild_and_refresh_country_storage_capacities")
    expect("cbp_recalculate_saved_country_storage_capacities = yes" in topology, "Topology refresh must retain the forced all-market path")

    promoted_entry = block(promoted, "cbp_prepare_promoted_country_market_capacity")
    expect("cbp_recalculate_country_market_capacity_from_prepared_pool_shared = yes" in promoted_entry, "Promoted-market pass must share the idempotent entry point")
    expect("_raw_shared" not in promoted_entry, "Promoted-market pass must not bypass the stamp")

    print("CBP monthly country-market capacity stamp contracts validated.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)

#!/usr/bin/env python3
"""Validate the sparse US-04 work-index contract.

This is a static topology and ownership contract. It does not claim runtime timing
or prove economic equivalence in place of an in-game comparison.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

RUNTIME = ROOT / "in_game/common/scripted_effects/cbp_us04_pop_demand_effects.txt"
GENERATOR = ROOT / "tools/generate_us04_pop_demand_helpers.sh"
GENERATED = ROOT / "in_game/common/scripted_effects/cbp_us04_pop_demand_generated.txt"
TEMPLATE = ROOT / "tools/templates/cbp_us04_pop_demand_good.template.txt"
STOCK_ON_ACTIONS = ROOT / "in_game/common/on_action/cbp_stock_on_actions.txt"
CORE03_ON_ACTIONS = ROOT / "in_game/common/on_action/cbp_core03_exposure_on_actions.txt"
STATE_DOC = ROOT / "docs/technical/PERSISTENT_STATE_AUDIT.md"
RUNTIME_FLOW = ROOT / "docs/architecture/RUNTIME_FLOW.md"
IMPLEMENTATION_DOC = ROOT / "docs/performance/US04_SPARSE_WORK_INDEX_IMPLEMENTATION.md"
AUDIT = ROOT / "tools/audit_cbp_persistent_state.sh"
GOODS = ROOT / "tools/cbp_goods.sh"


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"Missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def effect_body(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\{{", text)
    if not match:
        raise AssertionError(f"Missing effect: {name}")
    start = match.end() - 1
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
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
                return text[start + 1 : index]
    raise AssertionError(f"Unbalanced effect: {name}")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f"{label}: missing `{token}`")


def forbid(text: str, token: str, label: str) -> None:
    if token in text:
        raise AssertionError(f"{label}: forbidden `{token}`")


def parse_goods(text: str) -> list[str]:
    match = re.search(r"cbp_goods=\(\s*(.*?)\s*\)", text, re.S)
    if not match:
        raise AssertionError("Could not parse tools/cbp_goods.sh")
    body = re.sub(r"#.*", "", match.group(1))
    goods = body.split()
    if not goods:
        raise AssertionError("Goods registry is empty")
    return goods


def main() -> int:
    runtime = read(RUNTIME)
    generator = read(GENERATOR)
    generated = read(GENERATED)
    template = read(TEMPLATE)
    stock_on_actions = read(STOCK_ON_ACTIONS)
    core03_on_actions = read(CORE03_ON_ACTIONS)
    state_doc = read(STATE_DOC)
    runtime_flow = read(RUNTIME_FLOW)
    implementation_doc = read(IMPLEMENTATION_DOC)
    audit = read(AUDIT)
    goods = parse_goods(read(GOODS))

    monthly = effect_body(runtime, "cbp_run_monthly_us04_estate_accounting_for_current_country")
    require(monthly, "cbp_prepare_us04_sparse_index_for_current_country", "monthly owner")
    require(monthly, "cbp_monthly_process_us04_sparse_index_all_goods", "monthly owner")
    forbid(monthly, "every_market_present_in_country", "monthly owner")
    forbid(monthly, "every_owned_location", "monthly owner")

    rebuild = effect_body(runtime, "cbp_rebuild_us04_sparse_index_for_current_country")
    require(rebuild, "cbp_us04_clear_sparse_index_for_current_country", "load repair")
    require(rebuild, "every_owned_location", "load repair")
    require(rebuild, "cbp_us04_refresh_location_sparse_index_all_goods", "load repair")
    require(rebuild, "cbp_us04_sparse_index_load_generation", "load repair")

    yearly = effect_body(runtime, "cbp_run_yearly_pop_demand_adaptation_for_current_country")
    require(yearly, "every_owned_location", "yearly verifier")
    require(yearly, "cbp_annual_adjust_location_pop_demand_all_goods", "yearly verifier")
    require(yearly, "cbp_us04_clear_sparse_index_for_current_country", "yearly verifier")

    owner_repair = effect_body(runtime, "cbp_us04_handle_location_changed_owner")
    for token in ("scope:loser", "scope:winner", "cbp_us04_remove_location_from_country_sparse_index_all_goods", "cbp_us04_refresh_location_sparse_index_all_goods"):
        require(owner_repair, token, "ownership repair")

    start = effect_body(stock_on_actions, "cbp_start_game_stock_initialization_pulse")
    load = effect_body(stock_on_actions, "cbp_load_game_stock_initialization_pulse")
    require(start, "cbp_advance_us04_sparse_index_load_generation", "game start")
    require(load, "cbp_advance_us04_sparse_index_load_generation", "game load")

    location_hook = effect_body(core03_on_actions, "cbp_core03_probe_location_changed_owner")
    require(location_hook, "cbp_core03_handle_location_changed_owner", "location-owner hook")
    require(location_hook, "cbp_us04_handle_location_changed_owner", "location-owner hook")

    for token in (
        'list_name = f"cbp_{good}_us04_active_locations"',
        "cbp_us04_sparse_coefficient_active",
        "cbp_us04_sparse_proxy_present",
        "cbp_us04_sparse_prior_record_present",
        "cbp_us04_process_sparse_country_good_",
        "cbp_monthly_process_us04_sparse_index_all_goods",
        "cbp_us04_refresh_location_sparse_index_all_goods",
        "remove_list_variable",
        "every_in_list",
    ):
        require(generator, token, "generator")

    for token in (
        "cbp_us04_reconciliation_coefficient",
        "cbp_us04_proxy_estate_size_peasants_estate",
        "cbp_us04_reconciliation_requested_quantity",
    ):
        require(generator, token, "activity membership")

    # The generated output must contain one country-owned sparse list surface and
    # one sparse processor for every canonical supported good.
    for good in goods:
        for token in (
            f"cbp_{good}_us04_active_locations",
            f"cbp_us04_prepare_sparse_state_good_{good}",
            f"cbp_us04_refresh_location_sparse_index_good_{good}",
            f"cbp_us04_process_sparse_country_good_{good}",
        ):
            require(generated, token, f"generated {good}")

    for token in (
        "demands_goods_by_pops",
        "cbp_monthly_reconcile_location_pop_demand_good_wheat",
        "cbp_us04_clear_monthly_reconciliation_record_good_wheat",
        "cbp_us04_refresh_location_sparse_index_good_wheat",
    ):
        require(generated, token, "generated sparse dispatcher")

    # Work selection may change; economic effects and central mutation boundaries
    # stay in the existing per-good template.
    for token in (
        "cbp_remove_stock",
        "cbp_add_stock",
        "add_gold_to_estate",
        "scope:cbp_us04_reconciliation_delta_ratio",
        "cbp_us04_store_monthly_reconciliation_record_good___GOOD__",
    ):
        require(template, token, "economic template")

    for token in (
        "cbp_<good>_us04_active_locations",
        "scheduling index",
        "never economic source",
        "cbp_us04_sparse_index_load_generation",
    ):
        require(state_doc, token, "persistent-state classification")

    require(audit, "cbp_<good>_us04_active_locations", "executable state audit")
    require(audit, "tools/generate_us04_pop_demand_helpers.sh", "executable state audit")

    for token in (
        "sparse",
        "cbp_<good>_us04_active_locations",
        "ownership",
        "prior monthly record",
    ):
        require(implementation_doc, token, "implementation documentation")

    for token in (
        "country-owned per-good active-location lists",
        "ownership-change repair",
        "prior record",
    ):
        require(runtime_flow, token, "normative runtime flow")

    print(f"Validated sparse US-04 indexes for {len(goods)} goods.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"US-04 sparse-index validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

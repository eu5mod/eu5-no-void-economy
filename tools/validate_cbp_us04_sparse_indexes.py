#!/usr/bin/env python3
"""Validate the sparse US-04 runtime work-selection contract."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

RUNTIME = ROOT / "in_game/common/scripted_effects/cbp_us04_pop_demand_effects.txt"
GENERATOR = ROOT / "tools/generate_us04_pop_demand_helpers.sh"
GENERATED = ROOT / "in_game/common/scripted_effects/cbp_us04_pop_demand_generated.txt"
TEMPLATE = ROOT / "tools/templates/cbp_us04_pop_demand_good.template.txt"
DEMAND_RESOLVER = ROOT / "in_game/common/scripted_effects/cbp_stock_demand_resolver_effects.txt"
STOCK_ON_ACTIONS = ROOT / "in_game/common/on_action/cbp_stock_on_actions.txt"
CORE03_ON_ACTIONS = ROOT / "in_game/common/on_action/cbp_core03_exposure_on_actions.txt"
IMPLEMENTATION_DOC = ROOT / "docs/performance/US04_SPARSE_WORK_INDEX_IMPLEMENTATION.md"
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
    demand_resolver = read(DEMAND_RESOLVER)
    stock_on_actions = read(STOCK_ON_ACTIONS)
    core03_on_actions = read(CORE03_ON_ACTIONS)
    implementation_doc = read(IMPLEMENTATION_DOC)
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

    yearly = effect_body(runtime, "cbp_run_yearly_pop_demand_adaptation_for_current_country")
    require(yearly, "every_owned_location", "yearly verifier")
    require(yearly, "cbp_us04_clear_sparse_index_for_current_country", "yearly verifier")

    owner_repair = effect_body(runtime, "cbp_us04_handle_location_changed_owner")
    for token in (
        "scope:loser",
        "scope:winner",
        "cbp_us04_remove_location_from_country_sparse_index_all_goods",
        "cbp_us04_refresh_location_sparse_index_all_goods",
    ):
        require(owner_repair, token, "ownership repair")

    require(
        effect_body(stock_on_actions, "cbp_start_game_stock_initialization_pulse"),
        "cbp_advance_us04_sparse_index_load_generation",
        "game start",
    )
    require(
        effect_body(stock_on_actions, "cbp_load_game_stock_initialization_pulse"),
        "cbp_advance_us04_sparse_index_load_generation",
        "game load",
    )
    require(
        effect_body(core03_on_actions, "cbp_core03_probe_location_changed_owner"),
        "cbp_us04_handle_location_changed_owner",
        "location-owner hook",
    )

    for token in (
        'list_name = f"cbp_{good}_us04_active_locations"',
        "cbp_us04_sparse_coefficient_active",
        "cbp_us04_sparse_proxy_present",
        "cbp_us04_sparse_prior_record_present",
        "cbp_monthly_process_us04_sparse_index_all_goods",
        "remove_list_variable",
        "every_in_list",
    ):
        require(generator, token, "generator")

    for good in goods:
        for token in (
            f"cbp_{good}_us04_active_locations",
            f"cbp_us04_prepare_sparse_state_good_{good}",
            f"cbp_us04_refresh_location_sparse_index_good_{good}",
            f"cbp_us04_process_sparse_country_good_{good}",
        ):
            require(generated, token, f"generated {good}")

    for writer in (
        "cbp_reset_us04_location_estate_proxy",
        "cbp_record_us04_location_estate_proxy_peasants_estate",
        "cbp_record_us04_location_estate_proxy_burghers_estate",
        "cbp_record_us04_location_estate_proxy_nobles_estate",
        "cbp_record_us04_location_estate_proxy_clergy_estate",
        "cbp_reset_pop_demand_outcome",
    ):
        require(
            effect_body(demand_resolver, writer),
            "cbp_us04_refresh_location_sparse_index_good_$good$ = yes",
            f"proxy writer {writer}",
        )

    for token in (
        "cbp_remove_stock",
        "cbp_add_stock",
        "add_gold_to_estate",
        "cbp_us04_store_monthly_reconciliation_record_good___GOOD__",
    ):
        require(template, token, "economic template")

    for token in (
        "cbp_<good>_us04_active_locations",
        "coefficient **and** proxy activity",
        "prior monthly record",
        "Ownership-change repair",
    ):
        require(implementation_doc, token, "implementation documentation")

    print(f"Validated sparse US-04 runtime indexes for {len(goods)} goods.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"US-04 sparse-index validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

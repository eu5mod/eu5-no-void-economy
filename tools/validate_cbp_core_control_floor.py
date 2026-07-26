#!/usr/bin/env python3
"""Validate the permanent owner-core Control floor static contract."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FLOOR_FILE = ROOT / "in_game/common/scripted_effects/cbp_core_control_floor_effects.txt"
CORE04_FILE = ROOT / "in_game/common/scripted_effects/cbp_core04_market_entry_effects.txt"
MONTHLY_MEMORY_FILE = ROOT / "in_game/common/scripted_effects/cbp_core04_monthly_memory_effects.txt"
CORE03_ON_ACTION = ROOT / "in_game/common/on_action/cbp_core03_exposure_on_actions.txt"
STOCK_ON_ACTION = ROOT / "in_game/common/on_action/cbp_stock_on_actions.txt"
STOCK_EFFECTS_FILE = ROOT / "in_game/common/scripted_effects/cbp_stock_effects.txt"
DOC_FILE = ROOT / "docs/technical/PERMANENT_CORE_CONTROL_FLOOR.md"

EFFECT = "cbp_enforce_owner_core_control_floor"
COMBINED_REFRESH = "cbp_core04_refresh_current_country_location_market_memory"
MONTHLY_REFRESH = "cbp_core04_refresh_current_country_location_market_memory_monthly"


def fail(message: str) -> None:
    print(f"[FAIL] {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8-sig")


def extract_block(text: str, key: str) -> str:
    marker = f"{key} = {{"
    start = text.find(marker)
    require(start >= 0, f"missing block: {key}")
    brace_start = text.find("{", start)
    depth = 0
    for index in range(brace_start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    fail(f"unbalanced block: {key}")
    return ""  # unreachable


def main() -> None:
    floor = read(FLOOR_FILE)
    core04 = read(CORE04_FILE)
    monthly_memory = read(MONTHLY_MEMORY_FILE)
    owner_on_action = read(CORE03_ON_ACTION)
    stock_on_action = read(STOCK_ON_ACTION)
    stock_effects = read(STOCK_EFFECTS_FILE)
    documentation = read(DOC_FILE)

    require(floor.count(f"{EFFECT} = {{") == 1, "floor effect must have one definition")
    require("every_owned_location" not in floor, "floor effect must not own a location loop")
    require(floor.count("change_control = scope:cbp_core_control_floor_delta") == 3,
            "each rank family must use the shared positive delta")
    require(floor.count("is_core_of = scope:cbp_core_control_floor_owner") == 3,
            "every rank branch must recheck owner-core eligibility")
    require(floor.count("min = 0") == 3, "every Control delta must be clamped at zero")

    rank_contracts = {
        "location_rank:rural_settlement": ("local_control < 0.25", "value = 0.25"),
        "location_rank:town": ("local_control < 0.30", "value = 0.30"),
        "location_rank:city": ("local_control < 0.35", "value = 0.35"),
        "location_rank:megalopolis": ("local_control < 0.35", "value = 0.35"),
    }
    for rank, expected_fragments in rank_contracts.items():
        require(rank in floor, f"missing rank contract: {rank}")
        for fragment in expected_fragments:
            require(fragment in floor, f"missing {fragment!r} for {rank}")

    require("change_control = -" not in floor, "floor must never lower Control")
    require("subtract = 0." not in floor, "floor must subtract current Control, not a fixed value")
    require(floor.count("subtract = local_control") == 3,
            "each floor delta must subtract current local_control")

    combined = extract_block(core04, COMBINED_REFRESH)
    require(combined.count("every_owned_location = {") == 1,
            "combined CORE-04 refresh must retain one owned-location loop")
    iterator_pos = combined.find("every_owned_location = {")
    floor_pos = combined.find(f"{EFFECT} = yes", iterator_pos)
    require(floor_pos > iterator_pos,
            "combined CORE-04 refresh must enforce the floor inside its location loop")
    require(combined.find("cbp_core04_last_known_market", floor_pos) > floor_pos,
            "combined CORE-04 refresh must retain location-memory writes")

    monthly = extract_block(monthly_memory, MONTHLY_REFRESH)
    require(monthly.count("every_owned_location = {") == 1,
            "monthly CORE-04 memory refresh must retain one owned-location loop")
    require(EFFECT not in monthly,
            "monthly CORE-04 memory refresh must not evaluate the Control floor")
    require("cbp_core04_last_known_market" in monthly,
            "monthly CORE-04 memory refresh must retain market-memory writes")

    global_refresh = extract_block(core04, "cbp_core04_refresh_all_location_market_memory")
    global_ready_pos = global_refresh.find("cbp_stock_runtime_ready_trigger = yes")
    global_country_pos = global_refresh.find("every_country = {")
    require(global_ready_pos >= 0 and global_country_pos > global_ready_pos,
            "global start/load refresh must run only after stock runtime readiness")
    require(global_country_pos >= 0,
            "start/load refresh must retain its existing country traversal")
    require(f"{COMBINED_REFRESH} = yes" in global_refresh,
            "start/load refresh must reuse the combined location loop")

    start_registration = extract_block(stock_on_action, "on_game_start")
    require("cbp_start_game_stock_initialization_pulse" in start_registration,
            "on_game_start must register the stock initialization pulse")
    start_pulse = extract_block(stock_on_action, "cbp_start_game_stock_initialization_pulse")
    start_dispatcher_pos = start_pulse.find("cbp_start_game_stock_initialization_dispatcher = yes")
    start_refresh_pos = start_pulse.find("cbp_core04_refresh_all_location_market_memory = yes")
    require(start_dispatcher_pos >= 0 and start_refresh_pos > start_dispatcher_pos,
            "game-start pulse must refresh all Control floors after stock initialization")

    load_registration = extract_block(stock_on_action, "on_game_load")
    require("cbp_load_game_stock_initialization_pulse" in load_registration,
            "on_game_load must register the stock lifecycle-repair pulse")
    load_pulse = extract_block(stock_on_action, "cbp_load_game_stock_initialization_pulse")
    require("cbp_repair_stock_lifecycle_on_game_load = yes" in load_pulse,
            "game-load pulse must invoke stock lifecycle repair")
    load_repair = extract_block(stock_effects, "cbp_repair_stock_lifecycle_on_game_load")
    load_dispatcher_pos = load_repair.find("cbp_start_game_stock_initialization_dispatcher = yes")
    load_refresh_pos = load_repair.find("cbp_core04_refresh_all_location_market_memory = yes")
    require(load_dispatcher_pos >= 0 and load_refresh_pos > load_dispatcher_pos,
            "game-load repair must refresh all Control floors after readiness repair")

    owner_change = extract_block(owner_on_action, "cbp_core03_probe_location_changed_owner")
    succession_pos = owner_change.find("cbp_core03_handle_location_changed_owner = yes")
    owner_floor_pos = owner_change.find(f"{EFFECT} = yes")
    require(succession_pos >= 0 and owner_floor_pos > succession_pos,
            "owner-change hook must enforce the floor after CORE-03 succession")

    require("on_location_changed_rank = {" in stock_on_action,
            "rank-change hardcoded on-action must remain registered")
    rank_change = extract_block(stock_on_action, "cbp_capacity_location_rank_changed_pulse")
    capacity_pos = rank_change.find("cbp_handle_location_capacity_changed = yes")
    rank_floor_pos = rank_change.find(f"{EFFECT} = yes")
    require(capacity_pos >= 0 and rank_floor_pos > capacity_pos,
            "rank-change pulse must enforce the floor after capacity refresh")

    monthly_pulse = extract_block(stock_on_action, "cbp_monthly_stock_cycle_pulse")
    require(f"{MONTHLY_REFRESH} = yes" in monthly_pulse,
            "monthly pulse must use the memory-only CORE-04 refresh")
    require(f"{COMBINED_REFRESH} = yes" not in monthly_pulse,
            "monthly pulse must not call the combined Control-floor refresh")

    yearly_pulse = extract_block(stock_on_action, "cbp_yearly_pop_demand_adaptation_pulse")
    yearly_adaptation_pos = yearly_pulse.find("cbp_run_yearly_pop_demand_adaptation_for_current_country = yes")
    yearly_floor_pos = yearly_pulse.find(f"{COMBINED_REFRESH} = yes")
    require(yearly_adaptation_pos >= 0 and yearly_floor_pos > yearly_adaptation_pos,
            "yearly pulse must run the combined Control-floor refresh after adaptation")

    runtime_occurrences: list[str] = []
    for path in (ROOT / "in_game/common").rglob("*.txt"):
        text = path.read_text(encoding="utf-8-sig")
        if EFFECT in text:
            runtime_occurrences.append(str(path.relative_to(ROOT)))
    require(sorted(runtime_occurrences) == sorted([
        "in_game/common/on_action/cbp_core03_exposure_on_actions.txt",
        "in_game/common/on_action/cbp_stock_on_actions.txt",
        "in_game/common/scripted_effects/cbp_core04_market_entry_effects.txt",
        "in_game/common/scripted_effects/cbp_core_control_floor_effects.txt",
    ]), f"unexpected runtime floor integration surfaces: {runtime_occurrences}")

    require("No monthly Control-floor evaluation" in documentation,
            "documentation must record the monthly exclusion contract")
    require("yearly country pulse" in documentation,
            "documentation must record the yearly fallback cadence")
    require("No confirmed integration-status on-action" in documentation,
            "documentation must record the unresolved integration-status exposure")

    print("[PASS] permanent owner-core Control floor static contract")


if __name__ == "__main__":
    main()

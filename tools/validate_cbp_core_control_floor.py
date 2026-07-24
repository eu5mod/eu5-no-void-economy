#!/usr/bin/env python3
"""Validate the permanent owner-core Control floor static contract."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FLOOR_FILE = ROOT / "in_game/common/scripted_effects/cbp_core_control_floor_effects.txt"
CORE04_FILE = ROOT / "in_game/common/scripted_effects/cbp_core04_market_entry_effects.txt"
CORE03_ON_ACTION = ROOT / "in_game/common/on_action/cbp_core03_exposure_on_actions.txt"
STOCK_ON_ACTION = ROOT / "in_game/common/on_action/cbp_stock_on_actions.txt"
DOC_FILE = ROOT / "docs/technical/PERMANENT_CORE_CONTROL_FLOOR.md"

EFFECT = "cbp_enforce_owner_core_control_floor"


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
    owner_on_action = read(CORE03_ON_ACTION)
    stock_on_action = read(STOCK_ON_ACTION)
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

    monthly = extract_block(core04, "cbp_core04_refresh_current_country_location_market_memory")
    require(monthly.count("every_owned_location = {") == 1,
            "CORE-04 monthly memory effect must retain one owned-location loop")
    iterator_pos = monthly.find("every_owned_location = {")
    floor_pos = monthly.find(f"{EFFECT} = yes", iterator_pos)
    require(floor_pos > iterator_pos,
            "monthly floor call must be inside the existing CORE-04 location loop")
    require(monthly.find("cbp_core04_last_known_market", floor_pos) > floor_pos,
            "floor call must share the location-memory loop before memory writes")

    global_refresh = extract_block(core04, "cbp_core04_refresh_all_location_market_memory")
    require("every_country = {" in global_refresh,
            "start/load refresh must retain its existing country traversal")
    require("cbp_core04_refresh_current_country_location_market_memory = yes" in global_refresh,
            "start/load refresh must reuse the same country location loop")

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

    require("No separate monthly `every_owned_location` traversal" in documentation,
            "documentation must record the no-duplicate-loop contract")
    require("No confirmed integration-status on-action" in documentation,
            "documentation must record the unresolved integration-status exposure")

    print("[PASS] permanent owner-core Control floor static contract")


if __name__ == "__main__":
    main()

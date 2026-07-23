#!/usr/bin/env python3
"""Validate that monthly market-local accounting has one global owner path."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EFFECTS_PATH = ROOT / "in_game/common/scripted_effects/cbp_q8_7_global_owner_effects.txt"
TRIGGERS_PATH = ROOT / "in_game/common/scripted_triggers/cbp_q8_7_global_owner_triggers.txt"
RUNTIME_FLOW_PATH = ROOT / "docs/architecture/RUNTIME_FLOW.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def block(text: str, name: str) -> str:
    marker = f"{name} = {{"
    start = text.find(marker)
    require(start >= 0, f"Missing scripted block: {name}")

    opening = text.find("{", start)
    depth = 0
    for index in range(opening, len(text)):
        character = text[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError(f"Unclosed scripted block: {name}")


def uncommented_script(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def mermaid_block(markdown: str) -> str:
    marker = "```mermaid"
    start = markdown.find(marker)
    require(start >= 0, "Normative runtime document must contain a Mermaid diagram")
    body_start = start + len(marker)
    end = markdown.find("```", body_start)
    require(end >= 0, "Normative Mermaid diagram must be closed")
    return markdown[body_start:end]


def main() -> int:
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    live_effects = uncommented_script(effects)
    runtime_flow = RUNTIME_FLOW_PATH.read_text(encoding="utf-8")
    runtime_mermaid = mermaid_block(runtime_flow)

    require(
        not TRIGGERS_PATH.exists(),
        "Retired Q8.7 owner-selection trigger file must remain absent",
    )

    for forbidden in (
        "cbp_q8_7_live_global_market_owner_disabled",
        "cbp_q8_7_live_global_market_owner_enabled_trigger",
        "cbp_q8_7_live_global_market_owner_disabled_trigger",
        "cbp_enable_q8_7_live_global_market_owner",
        "cbp_disable_q8_7_live_global_market_owner",
        "cbp_run_monthly_promoted_market_local_cycle = yes",
        "every_market_center_in_country",
    ):
        require(forbidden not in live_effects, f"Retired owner path reintroduced: {forbidden}")

    monthly_owner = block(live_effects, "cbp_run_monthly_stock_cycle_q8_7_owner_switch")
    global_cycle = block(live_effects, "cbp_run_monthly_q8_7_global_market_local_cycle_once")
    market_body = block(live_effects, "cbp_q8_7_run_global_market_local_owner_market")

    global_call = "cbp_run_monthly_q8_7_global_market_local_cycle_once = {"
    trade_call = "cbp_run_monthly_country_trade_owner_cycle = yes"
    us04_call = "cbp_run_monthly_us04_reconciliation_for_current_country = yes"

    require(
        monthly_owner.count(global_call) == 1,
        "Monthly owner must call the globally stamped market cycle exactly once",
    )
    require(trade_call in monthly_owner, "Country trade owner must remain after market-local work")
    require(us04_call in monthly_owner, "Monthly US-04 owner must remain after trade")
    require(
        monthly_owner.index(global_call)
        < monthly_owner.index(trade_call)
        < monthly_owner.index(us04_call),
        "Required order is global markets -> country trades -> monthly US-04",
    )

    require(
        global_cycle.count("every_market_in_world = {") == 1,
        "Global cycle must contain exactly one every_market_in_world iterator",
    )
    require(
        "cbp_q8_7_live_global_owner_month_stamp" in global_cycle,
        "Global cycle must retain its once-per-month stamp",
    )

    for required in (
        "cbp_market_runtime_use_detailed_accounting_trigger",
        "cbp_market_runtime_use_vanilla_fallback_trigger",
        "cbp_market_runtime_blocked_trigger",
    ):
        require(required in market_body, f"Per-market accounting mode missing: {required}")

    require(
        "every_market_center_in_country" not in runtime_mermaid,
        "Normative runtime diagram must not expose the retired market-center path",
    )
    require(
        "every_market_in_world" in runtime_mermaid,
        "Normative runtime diagram must expose the sole every-market path",
    )

    print("Global market owner-only contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

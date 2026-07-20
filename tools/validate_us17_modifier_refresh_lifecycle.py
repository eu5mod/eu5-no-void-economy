#!/usr/bin/env python3
"""Validate US-17 lifecycle, runtime constants, and privilege coverage."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EFFECTS = ROOT / "in_game/common/scripted_effects/cbp_us17_modifier_refresh_lifecycle_effects.txt"
ON_ACTIONS = ROOT / "in_game/common/on_action/cbp_us17_modifier_refresh_lifecycle_on_actions.txt"
EVENTS = ROOT / "in_game/events/cbp_us17_modifier_refresh_events.txt"
RUNTIME_CONSTANTS = ROOT / "in_game/common/script_values/cbp_us17_us20_runtime_constants.txt"
RUNTIME_REPLACEMENTS = (
    ROOT / "in_game/common/scripted_effects/zz_cbp_us17_runtime_constant_replacements.txt"
)
PROMOTED_METRIC_GUARDS = (
    ROOT / "in_game/common/scripted_effects/zz_cbp_promoted_market_metric_guards.txt"
)
INJECTION_FILES = (
    ROOT / "in_game/common/estate_privileges/cbp_us17_trade_efficiency_refresh_injections.txt",
    ROOT
    / "packages/cbp_economy_rebalance/in_game/common/estate_privileges/zz_cbp_us17_trade_efficiency_refresh_injections.txt",
)
PRIVILEGE_FILES = (
    ROOT / "packages/cbp_economy_rebalance/in_game/common/estate_privileges/burghers_estate.txt",
    ROOT / "packages/cbp_economy_rebalance/in_game/common/estate_privileges/nobles_estate.txt",
)

RELEVANT_MODIFIER = re.compile(
    r"\b(?:selling_efficiency|import_efficiency|export_efficiency|merchant_maintenance_efficiency)\s*="
)
TOP_LEVEL_ENTRY = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{")
INJECTION_ENTRY = re.compile(r"^TRY_INJECT:([A-Za-z0-9_]+)\s*=\s*\{", re.MULTILINE)


def fail(message: str) -> None:
    print(f"US17 lifecycle validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8-sig")


def strip_comment(line: str) -> str:
    return line.split("#", 1)[0]


def relevant_privileges(path: Path) -> set[str]:
    text = read(path)
    result: set[str] = set()
    current_name: str | None = None
    current_lines: list[str] = []
    depth = 0

    for raw_line in text.splitlines():
        code = strip_comment(raw_line)
        if current_name is None:
            match = TOP_LEVEL_ENTRY.match(code)
            if not match:
                continue
            current_name = match.group(1)
            current_lines = [code]
            depth = code.count("{") - code.count("}")
        else:
            current_lines.append(code)
            depth += code.count("{") - code.count("}")

        if current_name is not None and depth == 0:
            block = "\n".join(current_lines)
            if RELEVANT_MODIFIER.search(block):
                result.add(current_name)
            current_name = None
            current_lines = []

    if current_name is not None:
        fail(f"unbalanced top-level privilege block in {path.relative_to(ROOT)}")
    return result


def injection_blocks(text: str) -> dict[str, str]:
    matches = list(INJECTION_ENTRY.finditer(text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks[match.group(1)] = text[match.start():end]
    return blocks


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        fail(f"{label} is missing `{token}`")


def validate_injections(path: Path, expected: set[str]) -> dict[str, str]:
    blocks = injection_blocks(read(path))
    actual = set(blocks)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    label = str(path.relative_to(ROOT))
    if missing:
        fail(f"{label} is missing privilege lifecycle injections: " + ", ".join(missing))
    if unexpected:
        fail(f"{label} contains stale or unsupported injections: " + ", ".join(unexpected))

    for privilege, block in sorted(blocks.items()):
        require(block, "on_activate = {", f"{label}:{privilege}")
        require(block, "on_deactivate = {", f"{label}:{privilege}")
        if block.count("cbp_schedule_us17_native_profit_modifier_refresh = yes") != 2:
            fail(
                f"{label}:{privilege} must schedule exactly one activation "
                "and one deactivation refresh"
            )
    return blocks


def main() -> int:
    effects = read(EFFECTS)
    on_actions = read(ON_ACTIONS)
    events = read(EVENTS)
    constants = read(RUNTIME_CONSTANTS)
    replacements = read(RUNTIME_REPLACEMENTS)
    metric_guards = read(PROMOTED_METRIC_GUARDS)

    for token in (
        "cbp_migrate_us17_native_profit_modifiers_all_countries",
        "every_country = {",
        "NOT = { has_variable = cbp_us17_native_modifier_state_version }",
        "var:cbp_us17_native_modifier_state_version < 7",
        "NOT = { has_variable = cbp_us17_runtime_constant_source_version }",
        "var:cbp_us17_runtime_constant_source_version < 1",
        "cbp_refresh_us17_native_profit_modifiers_for_current_country = yes",
        "cbp_schedule_us17_native_profit_modifier_refresh",
        "cbp_us17_native_modifier_refresh_scheduled",
        "id = cbp_us17_modifier_refresh.1",
        "days = 1",
    ):
        require(effects, token, str(EFFECTS.relative_to(ROOT)))

    for token in (
        "on_game_start = {",
        "on_game_load = {",
        "cbp_us17_modifier_migration_on_game_start",
        "cbp_us17_modifier_migration_on_game_load",
        "cbp_migrate_us17_native_profit_modifiers_all_countries = yes",
        "delay = { days = 1 }",
    ):
        require(on_actions, token, str(ON_ACTIONS.relative_to(ROOT)))

    for token in (
        "namespace = cbp_us17_modifier_refresh",
        "cbp_us17_modifier_refresh.1 = {",
        "type = country_event",
        "hidden = yes",
        "remove_variable = cbp_us17_native_modifier_refresh_scheduled",
        "cbp_refresh_us17_native_profit_modifiers_for_current_country = yes",
    ):
        require(events, token, str(EVENTS.relative_to(ROOT)))

    for token in (
        "cbp_us17_us20_route_loss_coefficient_max = {",
        "cbp_us17_us20_route_loss_coefficient_curve = {",
        "cbp_us17_maintenance_component_weight = {",
        "cbp_us17_maintenance_efficiency_scale = {",
        "value = 0.05",
        "value = 0.5",
        "value = 10",
    ):
        require(constants, token, str(RUNTIME_CONSTANTS.relative_to(ROOT)))

    for token in (
        "REPLACE:cbp_compute_us20_route_loss_coefficient_from_selling_baseline",
        "REPLACE:cbp_compute_us17_native_corrections_from_baselines",
        "cbp_us17_us20_route_loss_coefficient_max",
        "cbp_us17_us20_route_loss_coefficient_curve",
        "cbp_us17_maintenance_component_weight",
        "cbp_us17_maintenance_efficiency_scale",
        "INJECT:cbp_clear_us17_native_profit_modifiers_for_current_country",
        "INJECT:cbp_refresh_us17_native_profit_modifiers_for_current_country",
        "cbp_us17_runtime_constant_source_version value = 1",
    ):
        require(replacements, token, str(RUNTIME_REPLACEMENTS.relative_to(ROOT)))
    if "define:NCountry|CBP_" in replacements:
        fail("runtime replacements must not read arbitrary CBP_* engine Defines")

    for effect_name in (
        "cbp_note_promoted_market_live_us00_country_pass",
        "cbp_note_promoted_market_live_us10_country_pass",
    ):
        require(
            metric_guards,
            f"REPLACE:{effect_name}",
            str(PROMOTED_METRIC_GUARDS.relative_to(ROOT)),
        )
    for token in (
        "has_global_variable = cbp_promoted_market_live_us00_country_passes",
        "has_global_variable = cbp_promoted_market_live_us10_country_passes",
        "has_global_variable = cbp_promoted_market_live_us00_good_scans",
        "has_global_variable = cbp_promoted_market_live_us10_good_scans",
        "exists = scope:cbp_generated_stock_good_count",
    ):
        require(metric_guards, token, str(PROMOTED_METRIC_GUARDS.relative_to(ROOT)))

    expected: set[str] = set()
    for privilege_file in PRIVILEGE_FILES:
        expected.update(relevant_privileges(privilege_file))

    validated = [validate_injections(path, expected) for path in INJECTION_FILES]
    if set(validated[0]) != set(validated[1]):
        fail("Core and Economy package privilege injection sets differ")

    print(
        "US17 modifier refresh lifecycle validation passed: "
        "named runtime constants and promoted-market guards verified; "
        f"{len(expected)} trade-efficiency privileges covered in Core and Economy package"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

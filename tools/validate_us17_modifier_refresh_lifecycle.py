#!/usr/bin/env python3
"""Validate the direct US-17 runtime implementation and refresh lifecycle."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LIFECYCLE_EFFECTS = ROOT / "in_game/common/scripted_effects/cbp_us17_modifier_refresh_lifecycle_effects.txt"
ON_ACTIONS = ROOT / "in_game/common/on_action/cbp_us17_modifier_refresh_lifecycle_on_actions.txt"
EVENTS = ROOT / "in_game/events/cbp_us17_modifier_refresh_events.txt"
RUNTIME_CONSTANTS = ROOT / "in_game/common/script_values/cbp_us17_us20_runtime_constants.txt"
PRODUCTION_EFFECTS = ROOT / "in_game/common/scripted_effects/cbp_trade_owner_modifier_reconciliation_effects.txt"
HISTORICAL_RECONCILIATION = ROOT / "in_game/common/scripted_effects/zzz_trade_reconciliation_effects.txt"
OBSOLETE_REPLACEMENTS = ROOT / "in_game/common/scripted_effects/zz_cbp_us17_runtime_constant_replacements.txt"
TRADE_DEFINES = ROOT / "loading_screen/common/defines/cbp_trade_defines.txt"
PROMOTED_METRIC_GUARDS = ROOT / "in_game/common/scripted_effects/zz_cbp_promoted_market_metric_guards.txt"
INJECTION_FILE = (
    ROOT / "in_game/common/estate_privileges/cbp_us17_trade_efficiency_refresh_injections.txt"
)
OBSOLETE_PACKAGE_INJECTION = (
    ROOT
    / "packages/cbp_economy_rebalance/in_game/common/estate_privileges/"
    "zz_cbp_us17_trade_efficiency_refresh_injections.txt"
)
PACKAGE_PRIVILEGE_OUTPUTS = (
    ROOT / "packages/cbp_economy_rebalance/in_game/common/estate_privileges/cbp_burghers_estate.txt",
    ROOT / "packages/cbp_economy_rebalance/in_game/common/estate_privileges/cbp_nobles_estate.txt",
)
SUPPORTED_PRIVILEGES = {
    "novgorod_ivans_hundred",
    "kbo_lake_chad_trade_privilege",
    "noble_patronage",
    "polish_merchant_seal",
    "fra_leadership_of_marcel",
    "consolidated_corruption_of_the_burghers",
    "mam_muhtasibs",
    "office_of_the_farima_soura_privilege",
}

CUSTOM_DEFINE_NAMES = (
    "CBP_ROUTE_LOSS_COEFFICIENT_MAX",
    "CBP_ROUTE_LOSS_COEFFICIENT_CURVE",
    "CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT",
    "CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE",
    "CBP_ROUTE_LOSS_MAX",
    "CBP_ROUTE_LOSS_CURVE",
    "CBP_TRADE_MAINTENANCE_VANILLA_WEIGHT",
    "CBP_TRADE_MAINTENANCE_DIRECTIONAL_WEIGHT",
    "CBP_TRADE_EFFICIENCY_COMPENSATION_MAX",
    "CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE",
    "CBD_TRADE_MAINTENANCE_MAX_IMPACT",
)

RELEVANT_MODIFIER = re.compile(
    r"\b(?:selling_efficiency|import_efficiency|export_efficiency|merchant_maintenance_efficiency)\s*="
)
TOP_LEVEL_ENTRY = re.compile(
    r"^\s*(?:REPLACE:)?([A-Za-z0-9_]+)\s*=\s*\{"
)
INJECTION_ENTRY = re.compile(r"^TRY_INJECT:([A-Za-z0-9_]+)\s*=\s*\{", re.MULTILINE)


def fail(message: str) -> None:
    print(f"US17 lifecycle validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8-sig")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        fail(f"{label} is missing `{token}`")


def block(text: str, name: str) -> str:
    marker = f"{name} = {{"
    start = text.find(marker)
    if start < 0:
        fail(f"missing block `{name}`")
    open_brace = text.find("{", start)
    depth = 0
    for index in range(open_brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    fail(f"unclosed block `{name}`")
    return ""


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
            if RELEVANT_MODIFIER.search("\n".join(current_lines)):
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


def validate_injections(path: Path, expected: set[str]) -> dict[str, str]:
    blocks = injection_blocks(read(path))
    actual = set(blocks)
    label = str(path.relative_to(ROOT))

    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        fail(f"{label} is missing privilege lifecycle injections: " + ", ".join(missing))
    if unexpected:
        fail(f"{label} contains stale or unsupported injections: " + ", ".join(unexpected))

    for privilege, privilege_block in sorted(blocks.items()):
        require(privilege_block, "on_activate = {", f"{label}:{privilege}")
        require(privilege_block, "on_deactivate = {", f"{label}:{privilege}")
        if privilege_block.count("cbp_schedule_us17_native_profit_modifier_refresh = yes") != 2:
            fail(
                f"{label}:{privilege} must schedule exactly one activation "
                "and one deactivation refresh"
            )
    return blocks


def main() -> int:
    lifecycle_effects = read(LIFECYCLE_EFFECTS)
    on_actions = read(ON_ACTIONS)
    events = read(EVENTS)
    constants = read(RUNTIME_CONSTANTS)
    production = read(PRODUCTION_EFFECTS)
    historical_reconciliation = read(HISTORICAL_RECONCILIATION)
    trade_defines = read(TRADE_DEFINES)
    metric_guards = read(PROMOTED_METRIC_GUARDS)

    if OBSOLETE_REPLACEMENTS.exists():
        fail(
            "obsolete runtime replacement layer must be removed: "
            f"{OBSOLETE_REPLACEMENTS.relative_to(ROOT)}"
        )

    for name in CUSTOM_DEFINE_NAMES:
        if re.search(rf"(?m)^\s*{re.escape(name)}\s*=", trade_defines):
            fail(f"arbitrary custom Define must be removed: {name}")
    if "define:NCountry|CBP_" in production or "define:NCountry|CBD_" in production:
        fail("production runtime must not read arbitrary custom engine Defines")
    if "CBD_TRADE_MAINTENANCE_MAX_IMPACT" in historical_reconciliation:
        fail("historical reconciliation must not read the retired CBD custom Define")
    require(
        historical_reconciliation,
        "multiply = cbp_us17_us20_route_loss_coefficient_max",
        str(HISTORICAL_RECONCILIATION.relative_to(ROOT)),
    )
    if "REPLACE:cbp_compute_us20_route_loss_coefficient_from_selling_baseline" in production:
        fail("authoritative calculation must be a direct effect, not a late replacement")
    if "REPLACE:cbp_compute_us17_native_corrections_from_baselines" in production:
        fail("authoritative calculation must be a direct effect, not a late replacement")

    expected_values = {
        "cbp_us17_us20_route_loss_coefficient_max": "0.05",
        "cbp_us17_us20_route_loss_coefficient_curve": "10",
        "cbp_us17_maintenance_component_weight": "0.5",
        "cbp_us17_maintenance_efficiency_scale": "10",
    }
    for name, value in expected_values.items():
        value_block = block(constants, name)
        require(value_block, f"value = {value}", str(RUNTIME_CONSTANTS.relative_to(ROOT)))
        require(production, name, str(PRODUCTION_EFFECTS.relative_to(ROOT)))

    coefficient = block(
        production,
        "cbp_compute_us20_route_loss_coefficient_from_selling_baseline",
    )
    corrections = block(
        production,
        "cbp_compute_us17_native_corrections_from_baselines",
    )
    clear = block(
        production,
        "cbp_clear_us17_native_profit_modifiers_for_current_country",
    )
    refresh = block(
        production,
        "cbp_refresh_us17_native_profit_modifiers_for_current_country",
    )

    for token in (
        "cbp_us17_us20_route_loss_coefficient_max",
        "cbp_us17_us20_route_loss_coefficient_curve",
        "divide = scope:cbp_us20_route_loss_denominator",
    ):
        require(coefficient, token, "direct Selling/US20 coefficient helper")
    for token in (
        "cbp_us17_maintenance_component_weight",
        "cbp_us17_maintenance_efficiency_scale",
        "divide = scope:cbp_us17_maintenance_curve_denominator",
    ):
        require(corrections, token, "direct US17 correction helper")
    if corrections.count("cbp_us17_maintenance_component_weight") != 2:
        fail("maintenance component weight must be applied exactly twice")

    source_marker = "cbp_us17_runtime_constant_source_version value = 1"
    require(clear, source_marker, "direct clear effect")
    require(refresh, source_marker, "direct refresh effect")

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
        require(lifecycle_effects, token, str(LIFECYCLE_EFFECTS.relative_to(ROOT)))

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

    expected = set(SUPPORTED_PRIVILEGES)
    common_dir = os.environ.get("EU5_GAME_COMMON_DIR")
    if common_dir:
        vanilla_privileges = (
            Path(common_dir) / "estate_privileges/burghers_estate.txt",
            Path(common_dir) / "estate_privileges/nobles_estate.txt",
        )
        discovered: set[str] = set()
        for privilege_file in vanilla_privileges:
            discovered.update(relevant_privileges(privilege_file))
        if discovered != expected:
            fail(
                "installed Vanilla trade-efficiency privilege set changed: "
                f"expected={sorted(expected)}, discovered={sorted(discovered)}"
            )

    package_relevant: set[str] = set()
    for privilege_file in PACKAGE_PRIVILEGE_OUTPUTS:
        package_relevant.update(relevant_privileges(privilege_file))
    if not package_relevant <= expected:
        fail(
            "generated privilege replacements contain unregistered trade-efficiency "
            f"objects: {sorted(package_relevant - expected)}"
        )

    if OBSOLETE_PACKAGE_INJECTION.exists():
        fail(
            "package-local privilege injections duplicate the Core TRY_INJECT "
            f"registrations: {OBSOLETE_PACKAGE_INJECTION.relative_to(ROOT)}"
        )
    validate_injections(INJECTION_FILE, expected)

    print(
        "US17 modifier refresh lifecycle validation passed: "
        "direct named-value implementation and promoted-market guards verified; "
        f"{len(expected)} trade-efficiency privileges covered by one Core injection set"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

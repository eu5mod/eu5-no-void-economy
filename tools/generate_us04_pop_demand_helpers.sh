#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="${1:-$repo_root/in_game/common/scripted_effects/cbp_us04_pop_demand_generated.txt}"
template="$repo_root/tools/templates/cbp_us04_pop_demand_good.template.txt"
stock_generated="$repo_root/in_game/common/scripted_effects/cbp_stock_goods_generated.txt"

# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_goods_registry
cbp_require_file "$template"

mkdir -p "$(dirname "$output")"

python3 - "$output" "$template" "$stock_generated" "${cbp_goods[@]}" <<'PY'
from collections import Counter
from pathlib import Path
import re
import sys

output = Path(sys.argv[1])
template = Path(sys.argv[2]).read_text(encoding="utf-8")
stock_generated = Path(sys.argv[3])
goods = sys.argv[4:]

PROXY_MAPS = [
    "cbp_us04_proxy_estate_size_peasants_estate",
    "cbp_us04_proxy_estate_size_burghers_estate",
    "cbp_us04_proxy_estate_size_nobles_estate",
    "cbp_us04_proxy_estate_size_clergy_estate",
]

MONTHLY_RECORD_MAPS = [
    "cbp_us04_reconciliation_requested_quantity",
    "cbp_us04_reconciliation_extra_quantity",
    "cbp_us04_reconciliation_removed_quantity",
    "cbp_us04_reconciliation_goods_supply_removed_quantity",
    "cbp_us04_reconciliation_restored_quantity",
    "cbp_us04_reconciliation_goods_supply_added_quantity",
    "cbp_us04_reconciliation_unsatisfied_quantity",
    "cbp_us04_reconciliation_country_stock_delta",
    "cbp_us04_reconciliation_market_stock_delta",
    "cbp_us04_reconciliation_estate_charge",
    "cbp_us04_reconciliation_estate_requested_total",
    "cbp_us04_reconciliation_estate_charge_peasants_estate",
    "cbp_us04_reconciliation_estate_charge_burghers_estate",
    "cbp_us04_reconciliation_estate_charge_nobles_estate",
    "cbp_us04_reconciliation_estate_charge_clergy_estate",
    "cbp_us04_reconciliation_estate_refund",
    "cbp_us04_reconciliation_estate_refund_peasants_estate",
    "cbp_us04_reconciliation_estate_refund_burghers_estate",
    "cbp_us04_reconciliation_estate_refund_nobles_estate",
    "cbp_us04_reconciliation_estate_refund_clergy_estate",
]


def render_good(good: str) -> str:
    rendered = template.replace("__GOOD__", good)
    unresolved = sorted(set(re.findall(r"__[A-Z0-9_]+__", rendered)))
    if unresolved:
        raise SystemExit(
            "Unresolved placeholders in US-04 pop demand template: "
            + ", ".join(unresolved)
        )
    return rendered.rstrip()


def assert_balanced_braces(text: str, label: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        for char in line:
            if not in_string and char == "#":
                break
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
                if depth < 0:
                    raise SystemExit(
                        f"{label} has an unexpected closing brace at line {line_number}"
                    )
    if in_string:
        raise SystemExit(f"{label} has an unclosed quoted string")
    if depth != 0:
        raise SystemExit(f"{label} has {depth} unclosed opening brace(s)")


def top_level_effect_names(text: str) -> list[str]:
    return re.findall(r"^([a-zA-Z0-9_]+)\s*=\s*\{\s*$", text, re.M)


def append_map_presence(lines: list[str], map_name: str, good: str, indent: str) -> None:
    lines.extend(
        [
            f"{indent}AND = {{",
            f"{indent}\thas_variable_map = {map_name}",
            f"{indent}\tis_key_in_variable_map = {{",
            f"{indent}\t\tname = {map_name}",
            f"{indent}\t\ttarget = goods:{good}",
            f"{indent}\t}}",
            f"{indent}}}",
        ]
    )


def append_sparse_good_helpers(lines: list[str], good: str) -> None:
    list_name = f"cbp_{good}_us04_active_locations"

    lines.extend(
        [
            f"cbp_us04_prepare_sparse_state_good_{good} = {{",
            "\tsave_temporary_scope_value_as = { name = cbp_us04_sparse_coefficient_active value = 0 }",
            "\tsave_temporary_scope_value_as = { name = cbp_us04_sparse_proxy_present value = 0 }",
            "\tsave_temporary_scope_value_as = { name = cbp_us04_sparse_prior_record_present value = 0 }",
            "",
            "\tif = {",
            "\t\tlimit = {",
            "\t\t\thas_variable_map = cbp_us04_reconciliation_coefficient",
            "\t\t\tis_key_in_variable_map = {",
            "\t\t\t\tname = cbp_us04_reconciliation_coefficient",
            f"\t\t\t\ttarget = goods:{good}",
            "\t\t\t}",
            f"\t\t\t\"variable_map(cbp_us04_reconciliation_coefficient|goods:{good})\" != 1",
            "\t\t}",
            "\t\tsave_temporary_scope_value_as = { name = cbp_us04_sparse_coefficient_active value = 1 }",
            "\t}",
            "",
            "\tif = {",
            "\t\tlimit = {",
            "\t\t\tOR = {",
        ]
    )
    for map_name in PROXY_MAPS:
        append_map_presence(lines, map_name, good, "\t\t\t\t")
    lines.extend(
        [
            "\t\t\t}",
            "\t\t}",
            "\t\tsave_temporary_scope_value_as = { name = cbp_us04_sparse_proxy_present value = 1 }",
            "\t}",
            "",
            "\tif = {",
            "\t\tlimit = {",
            "\t\t\tOR = {",
        ]
    )
    for map_name in MONTHLY_RECORD_MAPS:
        append_map_presence(lines, map_name, good, "\t\t\t\t")
    lines.extend(
        [
            "\t\t\t}",
            "\t\t}",
            "\t\tsave_temporary_scope_value_as = { name = cbp_us04_sparse_prior_record_present value = 1 }",
            "\t}",
            "}",
            "",
            f"cbp_us04_remove_location_from_country_sparse_index_good_{good} = {{",
            "\tif = {",
            "\t\tlimit = {",
            "\t\t\texists = scope:cbp_us04_sparse_country",
            "\t\t\texists = scope:cbp_us04_sparse_location",
            "\t\t}",
            "\t\tscope:cbp_us04_sparse_country = {",
            "\t\t\tif = {",
            "\t\t\t\tlimit = {",
            f"\t\t\t\t\thas_variable_list = {list_name}",
            "\t\t\t\t\tis_target_in_variable_list = {",
            f"\t\t\t\t\t\tname = {list_name}",
            "\t\t\t\t\t\ttarget = scope:cbp_us04_sparse_location",
            "\t\t\t\t\t}",
            "\t\t\t\t}",
            "\t\t\t\tremove_list_variable = {",
            f"\t\t\t\t\tname = {list_name}",
            "\t\t\t\t\ttarget = scope:cbp_us04_sparse_location",
            "\t\t\t\t}",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "}",
            "",
            f"cbp_us04_refresh_location_sparse_index_good_{good} = {{",
            "\tsave_temporary_scope_as = cbp_us04_sparse_location",
            f"\tcbp_us04_prepare_sparse_state_good_{good} = yes",
            "\towner ?= { save_temporary_scope_as = cbp_us04_sparse_country }",
            "",
            "\tif = {",
            "\t\tlimit = { exists = scope:cbp_us04_sparse_country }",
            "\t\tscope:cbp_us04_sparse_country = {",
            "\t\t\tif = {",
            "\t\t\t\tlimit = {",
            "\t\t\t\t\tOR = {",
            "\t\t\t\t\t\tscope:cbp_us04_sparse_coefficient_active > 0",
            "\t\t\t\t\t\tscope:cbp_us04_sparse_proxy_present > 0",
            "\t\t\t\t\t\tscope:cbp_us04_sparse_prior_record_present > 0",
            "\t\t\t\t\t}",
            "\t\t\t\t}",
            "\t\t\t\tif = {",
            f"\t\t\t\t\tlimit = {{ NOT = {{ has_variable_list = {list_name} }} }}",
            "\t\t\t\t\tadd_to_variable_list = {",
            f"\t\t\t\t\t\tname = {list_name}",
            "\t\t\t\t\t\ttarget = scope:cbp_us04_sparse_location",
            "\t\t\t\t\t}",
            "\t\t\t\t}",
            "\t\t\t\telse_if = {",
            "\t\t\t\t\tlimit = {",
            "\t\t\t\t\t\tNOT = {",
            "\t\t\t\t\t\t\tis_target_in_variable_list = {",
            f"\t\t\t\t\t\t\t\tname = {list_name}",
            "\t\t\t\t\t\t\t\ttarget = scope:cbp_us04_sparse_location",
            "\t\t\t\t\t\t\t}",
            "\t\t\t\t\t\t}",
            "\t\t\t\t\t}",
            "\t\t\t\t\tadd_to_variable_list = {",
            f"\t\t\t\t\t\tname = {list_name}",
            "\t\t\t\t\t\ttarget = scope:cbp_us04_sparse_location",
            "\t\t\t\t\t}",
            "\t\t\t\t}",
            "\t\t\t}",
            "\t\t\telse = {",
            f"\t\t\t\tcbp_us04_remove_location_from_country_sparse_index_good_{good} = yes",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "}",
            "",
            f"cbp_us04_process_sparse_country_good_{good} = {{",
            "\tsave_temporary_scope_as = cbp_us04_sparse_country",
            "\tif = {",
            f"\t\tlimit = {{ has_variable_list = {list_name} }}",
            "\t\tevery_in_list = {",
            f"\t\t\tvariable = {list_name}",
            "\t\t\tsave_temporary_scope_as = cbp_us04_sparse_location",
            "\t\t\towner ?= { save_temporary_scope_as = cbp_us04_sparse_location_owner }",
            "\t\t\tif = {",
            "\t\t\t\tlimit = {",
            "\t\t\t\t\texists = scope:cbp_us04_sparse_location_owner",
            "\t\t\t\t\tscope:cbp_us04_sparse_location_owner = scope:cbp_us04_sparse_country",
            "\t\t\t\t}",
            f"\t\t\t\tcbp_us04_prepare_sparse_state_good_{good} = yes",
            "\t\t\t\tif = {",
            "\t\t\t\t\tlimit = {",
            "\t\t\t\t\t\tOR = {",
            "\t\t\t\t\t\t\tscope:cbp_us04_sparse_coefficient_active > 0",
            "\t\t\t\t\t\t\tscope:cbp_us04_sparse_proxy_present > 0",
            "\t\t\t\t\t\t}",
            "\t\t\t\t\t}",
            "\t\t\t\t\tmarket ?= { save_temporary_scope_as = cbp_us04_sparse_market }",
            "\t\t\t\t\tif = {",
            "\t\t\t\t\t\tlimit = {",
            "\t\t\t\t\t\t\texists = scope:cbp_us04_sparse_market",
            "\t\t\t\t\t\t\tscope:cbp_us04_sparse_market = {",
            f"\t\t\t\t\t\t\t\tdemands_goods_by_pops = goods:{good}",
            "\t\t\t\t\t\t\t}",
            "\t\t\t\t\t\t}",
            f"\t\t\t\t\t\tcbp_monthly_reconcile_location_pop_demand_good_{good} = yes",
            "\t\t\t\t\t}",
            "\t\t\t\t\telse = {",
            f"\t\t\t\t\t\tcbp_us04_clear_monthly_reconciliation_record_good_{good} = yes",
            "\t\t\t\t\t}",
            "\t\t\t\t}",
            "\t\t\t\telse = {",
            f"\t\t\t\t\tcbp_us04_clear_monthly_reconciliation_record_good_{good} = yes",
            "\t\t\t\t}",
            f"\t\t\t\tcbp_us04_refresh_location_sparse_index_good_{good} = yes",
            "\t\t\t}",
            "\t\t\telse = {",
            f"\t\t\t\tcbp_us04_remove_location_from_country_sparse_index_good_{good} = yes",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "}",
            "",
        ]
    )


lines: list[str] = [
    "# Generated by tools/generate_us04_pop_demand_helpers.sh.",
    "# Do not edit manually.",
    "# US-04 local Pop demand adaptation helpers.",
    "# Location scope: maps are keyed by goods scope.",
    "# Sparse runtime indexes: country-owned per-good variable lists target locations.",
    "",
]

for good in goods:
    lines.extend([render_good(good), ""])
    append_sparse_good_helpers(lines, good)

lines.extend(["cbp_initialize_pop_demand_multiplier_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_initialize_pop_demand_multiplier_good_{good} = yes")
for good in goods:
    lines.append(f"\tcbp_initialize_us04_reconciliation_coefficient_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_initialize_us04_reconciliation_coefficient_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_initialize_us04_reconciliation_coefficient_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_us04_clear_sparse_index_for_current_country = {"])
for good in goods:
    list_name = f"cbp_{good}_us04_active_locations"
    lines.extend(
        [
            f"\tif = {{",
            f"\t\tlimit = {{ has_variable_list = {list_name} }}",
            f"\t\tclear_variable_list = {list_name}",
            f"\t}}",
        ]
    )
lines.extend(["}", ""])

lines.extend(["cbp_us04_refresh_location_sparse_index_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_us04_refresh_location_sparse_index_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_us04_remove_location_from_country_sparse_index_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_us04_remove_location_from_country_sparse_index_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_monthly_process_us04_sparse_index_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_us04_process_sparse_country_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_annual_adjust_location_pop_demand_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_annual_adjust_location_pop_demand_good_{good} = yes")
    lines.append(f"\tcbp_us04_refresh_location_sparse_index_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_monthly_reconcile_country_market_pop_demand_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_monthly_reconcile_country_market_pop_demand_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_monthly_assess_country_market_estate_consumption_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_monthly_assess_country_market_estate_consumption_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_monthly_reconcile_location_pop_demand_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_monthly_reconcile_location_pop_demand_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_monthly_assess_location_estate_consumption_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_monthly_assess_location_estate_consumption_good_{good} = yes")
lines.extend(["}", ""])

lines.extend(["cbp_reset_pop_demand_annual_counters_all_goods = {"])
for good in goods:
    lines.append(f"\tcbp_us04_reset_pop_demand_annual_counters_good_{good} = yes")
lines.extend(["}", ""])

generated = "\n".join(lines)
assert_balanced_braces(generated, "Generated US-04 Pop-demand helpers")

names = top_level_effect_names(generated)
duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
if duplicates:
    raise SystemExit(
        "Generated US-04 Pop-demand helpers contain duplicate top-level keys: "
        + ", ".join(duplicates)
    )

if stock_generated.is_file():
    stock_names = set(top_level_effect_names(stock_generated.read_text(encoding="utf-8")))
    collisions = sorted(set(names) & stock_names)
    if collisions:
        raise SystemExit(
            "Generated US-04 Pop-demand helpers collide with stock-generated keys: "
            + ", ".join(collisions)
        )

nested_map_value = re.compile(
    r"add_to_variable_map\s*=\s*\{(?:(?!\n\}).)*?\bvalue\s*=\s*\{",
    re.S,
)
if nested_map_value.search(generated):
    raise SystemExit(
        "Generated US-04 Pop-demand helpers must precompute arithmetic before "
        "add_to_variable_map; nested value blocks are not accepted by EU5 runtime"
    )

output.write_text(generated, encoding="utf-8")
PY

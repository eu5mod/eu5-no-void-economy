#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
template="$repo_root/tools/templates/modeu5_stock_good_adapter.template.txt"
output="${1:-$repo_root/in_game/common/scripted_effects/modeu5_stock_goods_generated.txt}"
modifiers_output="${2:-$repo_root/main_menu/common/static_modifiers/modeu5_us00_modifiers_generated.txt}"
modifiers_localization_output="${3:-$repo_root/main_menu/localization/english/modeu5_us00_static_modifiers_generated_l_english.yml}"

goods=(
	cotton sugar tobacco
	tar porcelain naval_supplies firearms cannons weaponry glass steel cloth
	fine_cloth liquor beer paper books jewelry leather tools masonry
	lacquerware pottery furniture
	horses clay sand coal iron copper goods_gold silver stone tin lead silk
	dyes incense tea cocoa coffee fiber_crops ivory lumber salt medicaments
	gems pearls amber saltpeter alum wine elephants marble mercury saffron
	pepper cloves chili
	wool wild_game fur fish wheat maize rice millet legumes potato livestock
	olives fruit beeswax
	slaves_goods
)

mkdir -p "$(dirname "$output")" "$(dirname "$modifiers_output")" "$(dirname "$modifiers_localization_output")"

postprocess_stock_goods_output() {
	local generated_path="$1"

	python3 - "$generated_path" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text()

# Jomini accepts arithmetic value blocks in save_temporary_scope_value_as, but
# runtime validation shows add_to_variable_map expects a scalar/event-target
# value. Precompute any one-line arithmetic map value before writing the map.
map_add_pattern = re.compile(
    r"^(\t*)add_to_variable_map = \{ name = ([a-zA-Z0-9_]+) key = ([^{}]+?) value = \{ value = scope:([a-zA-Z0-9_]+) add = (scope:[a-zA-Z0-9_]+|-?\d+(?:\.\d+)?) \} \}$",
    re.M,
)

def replace_map_add(match: re.Match[str]) -> str:
    indent, map_name, key_expr, before, delta = match.groups()
    computed_name = f"{map_name}_computed_value"
    return (
        f"{indent}save_temporary_scope_value_as = {{\n"
        f"{indent}\tname = {computed_name}\n"
        f"{indent}\tvalue = {{\n"
        f"{indent}\t\tvalue = scope:{before}\n"
        f"{indent}\t\tadd = {delta}\n"
        f"{indent}\t}}\n"
        f"{indent}}}\n"
        f"{indent}add_to_variable_map = {{ name = {map_name} key = {key_expr.strip()} value = scope:{computed_name} }}"
    )

text = map_add_pattern.sub(replace_map_add, text)

# These generated effects are future US-04/UI integration points. They are kept
# in the generated symbol surface as literal no-op placeholders, but their full
# draft bodies are not emitted yet because the current PR stack has no live
# caller that sets modeu5_demand_location / monthly UI values. The full draft
# implementation remains in tools/templates/modeu5_stock_good_adapter.template.txt.
FUTURE_EFFECT_RE = re.compile(
    r"^(modeu5_(?:record_pop_demand_outcome|reset_pop_demand_outcome|reset_pop_demand_annual_counters|store_us10_ui_monthly_counters)_good_[a-z0-9_]+) = \{\n",
    re.M,
)

def stub_future_effect_blocks(source: str) -> str:
    result: list[str] = []
    position = 0
    while True:
        match = FUTURE_EFFECT_RE.search(source, position)
        if match is None:
            result.append(source[position:])
            break

        effect_name = match.group(1)
        result.append(source[position:match.start()])
        brace_start = source.find("{", match.start(), match.end())
        if brace_start < 0:
            raise SystemExit("ModeU5 generator postprocess could not find effect opening brace")

        depth = 0
        end = None
        for index in range(brace_start, len(source)):
            char = source[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            raise SystemExit("ModeU5 generator postprocess could not find effect closing brace")

        if source.startswith("\n\n", end):
            end += 2
        elif source.startswith("\n", end):
            end += 1

        result.append(
            f"{effect_name} = {{\n"
            "\t# Future US-04/UI adapter placeholder. Do not emit the draft body until live callers are wired.\n"
            "}\n\n"
        )
        position = end

    return "".join(result)

text = stub_future_effect_blocks(text)

bad_lines = [
    line for line in text.splitlines()
    if "add_to_variable_map" in line and "value = {" in line and " add = " in line
]
if bad_lines:
    raise SystemExit(
        "ModeU5 generator emitted nested arithmetic directly inside add_to_variable_map:\n"
        + "\n".join(bad_lines[:20])
    )

for forbidden in (
    "scope:modeu5_demand_location",
    "scope:modeu5_ui_monthly_surplus",
    "scope:modeu5_ui_monthly_consumption",
):
    if forbidden in text:
        raise SystemExit(f"ModeU5 generator emitted unwired target reference: {forbidden}")

path.write_text(text)
PY
}

{
	cat <<'TXT'
# Generated by tools/generate_stock_good_helpers.sh.
# Do not edit manually.
# Literal map access is generated from tools/templates/modeu5_stock_good_adapter.template.txt.

modeu5_mark_active_market_any_good = {
	if = {
		limit = {
			NOT = { has_global_variable_list = modeu5_active_markets_any_good }
		}
		add_to_global_variable_list = {
			name = modeu5_active_markets_any_good
			target = scope:modeu5_active_market
		}
	}
	else_if = {
		limit = {
			NOT = {
				is_target_in_global_variable_list = {
					name = modeu5_active_markets_any_good
					target = scope:modeu5_active_market
				}
			}
		}
		add_to_global_variable_list = {
			name = modeu5_active_markets_any_good
			target = scope:modeu5_active_market
		}
	}
}

modeu5_clear_active_markets_any_good = {
	if = {
		limit = { has_global_variable_list = modeu5_active_markets_any_good }
		clear_global_variable_list = modeu5_active_markets_any_good
	}
}

modeu5_validate_dirty_stock_consistency = {
	modeu5_prepare_reconciliation_controller = yes
	if = {
		limit = { exists = scope:modeu5_reconciliation_controller }
		scope:modeu5_reconciliation_controller = {
			save_temporary_scope_value_as = { name = modeu5_reconciliation_type value = 1 }
			modeu5_reconciliation_prepare = yes
TXT
	for good in "${goods[@]}"; do
		printf '\t\t\tmodeu5_validate_dirty_markets_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
			modeu5_reconciliation_finalize = yes
		}
	}
	else = {
		error_log = "ModeU5 reconciliation skipped because no country controller scope exists."
	}
}

modeu5_validate_active_market_all_goods = {
TXT
	for good in "${goods[@]}"; do
		printf '\tmodeu5_validate_active_market_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
}

modeu5_validate_active_stock_consistency = {
	modeu5_prepare_reconciliation_controller = yes
	if = {
		limit = { exists = scope:modeu5_reconciliation_controller }
		scope:modeu5_reconciliation_controller = {
			save_temporary_scope_value_as = { name = modeu5_reconciliation_type value = 3 }
			modeu5_reconciliation_prepare = yes
			remove_global_variable = modeu5_market_owned_active_markets_processed_count
			remove_global_variable = modeu5_market_owned_country_cache_rebuild_count
			remove_global_variable = modeu5_market_owned_active_goods_processed_count
			set_global_variable = { name = modeu5_market_owned_active_markets_processed_count value = 0 }
			set_global_variable = { name = modeu5_market_owned_country_cache_rebuild_count value = 0 }
			set_global_variable = { name = modeu5_market_owned_active_goods_processed_count value = 0 }
			modeu5_repair_dirty_market_country_caches = yes
			if = {
				limit = { has_global_variable_list = modeu5_active_markets_any_good }
				every_in_global_list = {
					variable = modeu5_active_markets_any_good
					save_temporary_scope_as = modeu5_reconciliation_market
					save_temporary_scope_as = modeu5_market_country_cache_market
					modeu5_rebuild_countries_present_in_market = yes
					set_global_variable = {
						name = modeu5_market_owned_active_markets_processed_count
						value = {
							value = global_var:modeu5_market_owned_active_markets_processed_count
							add = 1
						}
					}
					set_global_variable = {
						name = modeu5_market_owned_country_cache_rebuild_count
						value = {
							value = global_var:modeu5_market_owned_country_cache_rebuild_count
							add = 1
						}
					}
					modeu5_validate_active_market_all_goods = yes
				}
			}
			modeu5_reconciliation_finalize = yes
		}
	}
	else = {
		error_log = "ModeU5 active reconciliation skipped because no country controller scope exists."
	}
}

modeu5_validate_all_stock_consistency = {
	modeu5_prepare_reconciliation_controller = yes
	if = {
		limit = { exists = scope:modeu5_reconciliation_controller }
		scope:modeu5_reconciliation_controller = {
			save_temporary_scope_value_as = { name = modeu5_reconciliation_type value = 2 }
			modeu5_reconciliation_prepare = yes
TXT
	for good in "${goods[@]}"; do
		printf '\t\t\tmodeu5_validate_all_markets_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
			modeu5_reconciliation_finalize = yes
		}
	}
	else = {
		error_log = "ModeU5 reconciliation skipped because no country controller scope exists."
	}
}

modeu5_clear_all_dirty_stock_markets = {
TXT
	for good in "${goods[@]}"; do
		printf '\tmodeu5_clear_dirty_markets_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
}

modeu5_clear_all_active_stock_markets = {
	modeu5_clear_active_markets_any_good = yes
TXT
	for good in "${goods[@]}"; do
		printf '\tmodeu5_clear_active_markets_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
}

modeu5_repair_all_active_stock_markets = {
	save_temporary_scope_as = modeu5_active_repair_controller
	modeu5_clear_all_active_stock_markets = yes
	modeu5_perf13_reset_active_repair_metrics = yes
TXT
	for good in "${goods[@]}"; do
		printf '\tmodeu5_repair_active_markets_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
}

modeu5_initialize_storage_capacities = {
	every_country = {
		save_temporary_scope_as = modeu5_country
		modeu5_rebuild_country_location_capacity_pool = yes
		modeu5_recalculate_saved_country_storage_capacities = yes
		set_global_variable = {
			name = modeu5_initialization_capacity_country_scans
			value = {
				value = global_var:modeu5_initialization_capacity_country_scans
				add = 1
			}
		}
	}
}

modeu5_initialize_opening_stocks = {
TXT
	for good in "${goods[@]}"; do
		printf '\tmodeu5_initialize_opening_stocks_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
}

modeu5_core03_transfer_location_all_goods = {
TXT
	for good in "${goods[@]}"; do
		printf '\tmodeu5_core03_transfer_location_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
}

modeu5_core03_transfer_residual_all_goods = {
TXT
	for good in "${goods[@]}"; do
		printf '\tevery_market_in_world = {\n'
		printf '\t\tsave_temporary_scope_as = modeu5_core03_market\n'
		printf '\t\tmodeu5_core03_transfer_residual_good_%s = yes\n' "$good"
		printf '\t}\n'
	done
	cat <<'TXT'
}

modeu5_process_us00_monthly_market_all_goods = {
TXT
	for good in "${goods[@]}"; do
		printf '\tmodeu5_process_us00_monthly_market_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
}

modeu5_clear_retired_us00_diagnostic_fields_all_goods = {
TXT
	for good in "${goods[@]}"; do
		printf '\tmodeu5_clear_retired_us00_diagnostic_fields_good_%s = yes\n' "$good"
	done
	cat <<'TXT'
}

modeu5_migrate_current_country_us00_minimal_persistence = {
	save_temporary_scope_as = modeu5_country
	scope:modeu5_country = {
		every_market_present_in_country = {
			save_temporary_scope_as = modeu5_market
			modeu5_clear_retired_us00_diagnostic_fields_all_goods = yes
		}
	}
}

modeu5_run_us00_monthly_pipeline_all_goods = {
	# Market-owned monthly dispatch: monthly_country_pulse still fires for every country,
	# but only countries owning market centers enter this loop, so each market-scale
	# US-00/US-10 pass is scheduled once from its market-center owner.
	every_market_center_in_country = {
		save_temporary_scope_as = modeu5_market
		save_temporary_scope_as = modeu5_market_country_cache_market
		modeu5_mark_monthly_market_seen = yes
		modeu5_rebuild_countries_present_in_market = yes
		if = {
			limit = { has_global_variable_list = modeu5_countries_present_in_market }
			every_in_global_list = {
				variable = modeu5_countries_present_in_market
				save_temporary_scope_as = modeu5_country
				modeu5_process_us00_monthly_market_all_goods = yes
			}
		}
	}
}
TXT

	first=1
	for good in "${goods[@]}"; do
		if (( first == 0 )); then
			printf '\n'
		fi
		first=0
		sed \
			-e "s/__GOOD__/$good/g" \
			-e "s/__STOCK_MAP__/modeu5_${good}_stock_by_market/g" \
			-e "s/__MARKET_MAP__/modeu5_${good}_market_stock/g" \
			-e "s/__DIRTY_LIST__/modeu5_${good}_dirty_markets/g" \
			-e "s/__ACTIVE_LIST__/modeu5_${good}_active_markets/g" \
			-e "s/__PRODUCED_MAP__/modeu5_${good}_produced_by_market/g" \
			-e "s/__ADDED_MAP__/modeu5_${good}_added_by_market/g" \
			-e "s/__REJECTED_MAP__/modeu5_${good}_rejected_by_market/g" \
			-e "s/__OVERPRODUCTION_RATIO_MAP__/modeu5_${good}_overproduction_ratio_by_market/g" \
			-e "s/__EFFECTIVE_OVERPRODUCTION_RATIO_MAP__/modeu5_${good}_effective_overproduction_ratio_by_market/g" \
			-e "s/__VOID_WEALTH_MAP__/modeu5_${good}_void_wealth_by_market/g" \
			-e "s/__VOID_TAXABLE_PROXY_MAP__/modeu5_${good}_void_taxable_income_proxy_by_market/g" \
			-e "s/__PRODUCTION_PENALTY_MAP__/modeu5_${good}_production_penalty_by_market/g" \
			-e "s/__US00_ACTIVE_MAP__/modeu5_${good}_us00_active_record_by_market/g" \
			-e "s/__UI_MONTHLY_SURPLUS_MAP__/modeu5_${good}_ui_monthly_surplus_by_market/g" \
			-e "s/__UI_MONTHLY_CONSUMPTION_MAP__/modeu5_${good}_ui_monthly_consumption_by_market/g" \
			"$template"
	done
} > "$output"
postprocess_stock_goods_output "$output"

{
	printf '%s\n' '# Generated by tools/generate_stock_good_helpers.sh.'
	printf '%s\n' '# Do not edit manually.'
	printf '%s\n\n' '# One location static modifier per good so add_location_modifier can use literal identifiers.'
	for good in "${goods[@]}"; do
		printf 'modeu5_%s_production_penalty_modifier = {\n' "$good"
		printf '\tgame_data = {\n'
		printf '\t\tcategory = location\n'
		printf '\t}\n'
		printf '\tlocal_%s_output_modifier = 1\n' "$good"
		printf '}\n\n'
	done
} > "$modifiers_output"

{
	printf '\357\273\277%s\n' 'l_english:'
	printf ' %s: "%s"\n' \
		'modeu5_us00_generated_static_modifiers_header' \
		'ModeU5 generated US-00 production penalty modifiers'
	for good in "${goods[@]}"; do
		label="$(printf '%s' "$good" | sed 's/_/ /g')"
		printf ' STATIC_MODIFIER_NAME_modeu5_%s_production_penalty_modifier: "ModeU5 %s production penalty"\n' \
			"$good" "$label"
		printf ' STATIC_MODIFIER_DESC_modeu5_%s_production_penalty_modifier: "ModeU5 overproduction correction for %s from the previous monthly stock cycle."\n' \
			"$good" "$label"
	done
} > "$modifiers_localization_output"

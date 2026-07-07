#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

search_lines() {
	local pattern="$1"
	shift

	if command -v rg >/dev/null 2>&1; then
		rg -n -- "$pattern" "$@"
	else
		grep -ERn -- "$pattern" "$@"
	fi
}

count_lines() {
	local pattern="$1"
	local file="$2"

	if command -v rg >/dev/null 2>&1; then
		rg -c -- "$pattern" "$file" 2>/dev/null || printf '0\n'
	else
		grep -Ec -- "$pattern" "$file" 2>/dev/null || printf '0\n'
	fi
}

assert_absent() {
	local label="$1"
	local pattern="$2"
	shift 2

	local matches
	matches="$(search_lines "$pattern" "$@" 2>/dev/null || true)"
	if [[ -n "$matches" ]]; then
		printf '%s\n' "$label" >&2
		printf '%s\n' "$matches" >&2
		exit 1
	fi
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

generated_stock="$tmp_dir/modeu5_stock_goods_generated.txt"
generated_modifiers="$tmp_dir/modeu5_us00_modifiers_generated.txt"
generated_localization="$tmp_dir/modeu5_us00_static_modifiers_generated_l_english.yml"

tools/generate_stock_good_helpers.sh \
	"$generated_stock" \
	"$generated_modifiers" \
	"$generated_localization" \
	>/dev/null

assert_absent \
	'Shared US-02 capacity refresh helpers must not be generated per good.' \
	'modeu5_(recalculate_saved_country_storage_capacities|recalculate_country_market_capacity|recalculate_country_market_capacity_from_prepared_pool|store_capacity_record|load_capacity_breakdown)_good_' \
	"$generated_stock"

traded_matches="$(search_lines 'traded_in_market:' in_game/common tools/templates tools/generate_stock_good_helpers.sh 2>/dev/null || true)"
unexpected_traded_matches="$(
	printf '%s\n' "$traded_matches" |
		grep -Ev 'tools/templates/modeu5_stock_good_adapter.template.txt:.*traded_in_market:__GOOD__|in_game/common/scripted_effects/modeu5_stock_goods_generated.txt:.*traded_in_market:[a-z_]+$' || true
)"
if [[ -n "$unexpected_traded_matches" ]]; then
	printf '%s\n' 'Runtime traded_in_market:<good> use is allowed only in the generated US-10 monthly trade-signal guard.' >&2
	printf '%s\n' "$unexpected_traded_matches" >&2
	exit 1
fi

printf 'ModeU5 per-good loop audit\n'
printf 'Generated stock adapters: %s\n' "$generated_stock"
printf 'CORE-01 add helpers: %s\n' "$(count_lines '^modeu5_add_stock_good_' "$generated_stock")"
printf 'CORE-01 remove helpers: %s\n' "$(count_lines '^modeu5_remove_stock_good_' "$generated_stock")"
printf 'CORE-01 transfer helpers: %s\n' "$(count_lines '^modeu5_transfer_stock_good_' "$generated_stock")"
printf 'CORE-01 decay helpers: %s\n' "$(count_lines '^modeu5_decay_stock_good_' "$generated_stock")"
printf 'CORE-02 opening-stock helpers: %s\n' "$(count_lines '^modeu5_initialize_opening_stocks_good_' "$generated_stock")"
printf 'US-00 monthly helpers: %s\n' "$(count_lines '^modeu5_run_us00_monthly_pipeline_good_' "$generated_stock")"
printf 'PERF-15 US-00 activity probes: %s\n' "$(count_lines '^modeu5_probe_us00_previous_record_activity_good_' "$generated_stock")"
printf 'PERF-15 US-00 loaded-clear helpers: %s\n' "$(count_lines '^modeu5_clear_loaded_void_economy_record_good_' "$generated_stock")"
printf 'US-11 active validators: %s\n' "$(count_lines '^modeu5_validate_active_market_good_' "$generated_stock")"
printf 'PERF-11 active repair helpers: %s\n' "$(count_lines '^modeu5_repair_active_markets_good_' "$generated_stock")"
printf 'Shared capacity per-good helpers: 0\n'
printf 'Runtime traded_in_market dependencies: US-10 monthly trade-signal guard only\n'

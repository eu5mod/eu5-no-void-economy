#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

search_quiet() {
	local pattern="$1"
	shift

	if command -v rg >/dev/null 2>&1; then
		rg -q -- "$pattern" "$@"
	else
		grep -ERq -- "$pattern" "$@"
	fi
}

search_lines() {
	local pattern="$1"
	shift

	if command -v rg >/dev/null 2>&1; then
		rg -n -- "$pattern" "$@"
	else
		grep -ERn -- "$pattern" "$@"
	fi
}

require_file() {
	local file="$1"
	if [[ ! -f "$file" ]]; then
		printf 'Required file is missing: %s\n' "$file" >&2
		exit 1
	fi
}

require_match() {
	local pattern="$1"
	local file="$2"
	local message="$3"
	if ! search_quiet "$pattern" "$file"; then
		printf '%s: %s\n' "$message" "$file" >&2
		exit 1
	fi
}

tracked_generated_files="$(git ls-files | grep -E '(^|/)cbp_[^/]*_generated(\.txt|_l_english\.yml)$' || true)"
if [[ -n "$tracked_generated_files" ]]; then
	printf 'Generated ModeU5 files must not be tracked by Git:\n%s\n' "$tracked_generated_files" >&2
	printf 'Keep them ignored and generated on demand with tools/generate_all.sh.\n' >&2
	exit 1
fi

local_user_path_pattern="/""Users/"'pierre'
crossover_steam_pattern="CrossOver/Bottles/"'Steam'
steam_common_pattern='Program Files [(]x86[)]/Steam/'"steamapps/common"
absolute_source_pattern="# Source: "'/'
local_path_pattern="${local_user_path_pattern}|${crossover_steam_pattern}|${steam_common_pattern}|${absolute_source_pattern}"

if search_lines "$local_path_pattern" \
	.github AGENTS.md CLAUDE.md README.md docs in_game main_menu packages \
	tools/README.md \
	tools/generate_all.sh \
	tools/generate_stock_good_helpers.sh \
	tools/generate_us09_economy_overrides.sh \
	tools/install_local_packages.sh \
	tools/templates; then
	printf 'Personal/local EU5 install paths must not be committed. Use <EU5_INSTALL_DIR> or <EU5_GAME_COMMON_DIR> placeholders.\n' >&2
	exit 1
fi

descriptors=(
	"descriptor.mod"
	"packages/cbp_economy_rebalance/descriptor.mod"
	"packages/cbp_trade_rebalance/descriptor.mod"
	"packages/cbp_war_rebalance/descriptor.mod"
	"packages/cbp_core_tests/descriptor.mod"
)

metadata_files=(
	".metadata/metadata.json"
	"packages/cbp_economy_rebalance/.metadata/metadata.json"
	"packages/cbp_trade_rebalance/.metadata/metadata.json"
	"packages/cbp_war_rebalance/.metadata/metadata.json"
	"packages/cbp_core_tests/.metadata/metadata.json"
)

expected_descriptor_names=(
	"No Void Economy"
	"Rebalance Economy"
	"Rebalance Estate Power"
	"Rebalance Early Blobbing"
	"No Void Economy Tests"
)

expected_metadata_names=(
	"NVE : No Void Economy (Required - Core)"
	"NVE : Economy balance patch (Optional)"
	"NVE : Estate Power balance patch (Optional)"
	"NVE : Early Blobbing balance patch (Optional)"
	"NVE : Core deterministic tests (Optional)"
)

expected_ids=(
	"cbp_core"
	"cbp_economy_rebalance"
	"cbp_trade_rebalance"
	"cbp_war_rebalance"
	"cbp_core_tests"
)

expected_description_prefixes=(
	"NVE removes the void-economy"
	"CAMPAIGN SETUP ONLY."
	"CAMPAIGN SETUP ONLY."
	"CAMPAIGN SETUP ONLY."
	"TESTING ONLY."
)

for index in "${!descriptors[@]}"; do
	descriptor="${descriptors[$index]}"
	expected_name="${expected_descriptor_names[$index]}"

	require_file "$descriptor"
	require_match "^name=\"${expected_name}\"$" "$descriptor" "Descriptor name mismatch"
	require_match '^version="0\.1\.0"$' "$descriptor" "Descriptor version mismatch"
done

if command -v jq >/dev/null 2>&1; then
	jq empty "${metadata_files[@]}"
	for index in "${!metadata_files[@]}"; do
		metadata_file="${metadata_files[$index]}"
		expected_id="${expected_ids[$index]}"
		expected_name="${expected_metadata_names[$index]}"
		expected_description_prefix="${expected_description_prefixes[$index]}"

		first_metadata_key="$(sed -n '/^[[:space:]]*"/{s/^[[:space:]]*"\([^"]*\)".*/\1/p;q;}' "$metadata_file")"
		if [[ "$first_metadata_key" != "id" ]]; then
			printf 'ModeU5 metadata must start with id as the first member: %s\n' "$metadata_file" >&2
			exit 1
		fi
		jq -e --arg expected_id "$expected_id" '.id == $expected_id' "$metadata_file" >/dev/null
		jq -e --arg expected_name "$expected_name" '.name == $expected_name' "$metadata_file" >/dev/null
		jq -e '.version == "0.1.0"' "$metadata_file" >/dev/null
		jq -e --arg prefix "$expected_description_prefix" '.short_description | startswith($prefix)' "$metadata_file" >/dev/null
	done

	jq -e '
		any(.relationships[]?;
			.rel_type == "dependency" and
			.id == "community_mod_framework" and
			.display_name == "Community Mod Framework" and
			.resource_type == "mod" and
			.version == "2.*"
		)
	' ".metadata/metadata.json" >/dev/null

	for metadata_file in "${metadata_files[@]:1}"; do
		jq -e '
			any(.relationships[]?;
				.rel_type == "dependency" and
				.id == "cbp_core" and
				.display_name == "No Void Economy (NVE)" and
				.resource_type == "mod" and
				.version == "0.1.*"
			)
		' "$metadata_file" >/dev/null
	done
else
	printf 'WARNING: jq is unavailable; JSON syntax was not checked.\n' >&2
fi

if search_lines 'set_global_variable = cbp_(economy|trade|war)_rebalance_loaded' in_game; then
	printf 'Core must not manufacture companion package markers.\n' >&2
	exit 1
fi

require_match 'set_global_variable = cbp_economy_rebalance_loaded' \
	packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt \
	'Economy companion package marker missing'
require_match 'set_global_variable = cbp_trade_rebalance_loaded' \
	packages/cbp_trade_rebalance/in_game/common/on_action/cbp_trade_package_on_actions.txt \
	'Trade companion package marker missing'
require_match 'set_global_variable = cbp_war_rebalance_loaded' \
	packages/cbp_war_rebalance/in_game/common/on_action/cbp_war_package_on_actions.txt \
	'War companion package marker missing'
require_match 'name = cbp_core_package_version' \
	in_game/common/scripted_effects/cbp_configuration_effects.txt \
	'Core package version marker missing'
require_match 'name = cbp_economy_package_version' \
	packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt \
	'Economy package version missing'
require_match 'name = cbp_trade_package_version' \
	packages/cbp_trade_rebalance/in_game/common/on_action/cbp_trade_package_on_actions.txt \
	'Trade package version missing'
require_match 'name = cbp_war_package_version' \
	packages/cbp_war_rebalance/in_game/common/on_action/cbp_war_package_on_actions.txt \
	'War package version missing'

us09_prices_file="packages/cbp_economy_rebalance/in_game/common/prices/00_hardcoded.txt"
us09_trade_buildings_file="packages/cbp_economy_rebalance/in_game/common/building_types/trade_buildings.txt"
us09_rgo_static_modifier_file="packages/cbp_economy_rebalance/main_menu/common/static_modifiers/cbp_us09_rgo_static_modifiers.txt"
us09_rgo_size_effects_file="packages/cbp_economy_rebalance/in_game/common/scripted_effects/cbp_us09_rgo_size_effects.txt"
require_file "$us09_prices_file"
require_file "$us09_trade_buildings_file"
require_file "$us09_rgo_static_modifier_file"
require_file "$us09_rgo_size_effects_file"
require_match '^# Source: <EU5_GAME_COMMON_DIR>/prices/00_hardcoded\.txt$' \
	"$us09_prices_file" \
	'US-09 RGO price override must preserve the vanilla prices file path'
require_match '^expand_rgo_gathering = \{$' \
	"$us09_prices_file" \
	'US-09 RGO price override must contain the vanilla expand_rgo_gathering key'
require_match '^# US-07 composed trade-building estate-power multiplier: 0\.5$' \
	"$us09_trade_buildings_file" \
	'US-09 trade-building override must document the composed US-07 multiplier'
require_match '^[[:space:]]+local_burghers_estate_power = 0\.05$' \
	"$us09_trade_buildings_file" \
	'US-09 trade-building override must compose the approved US-07 local_burghers_estate_power reduction'
require_match '^[[:space:]]+local_trades_per_burgher = 1\.1$' \
	"$us09_trade_buildings_file" \
	'US-09 trade-building override must apply the +10% local_trades_per_burgher compensation'
require_match '^[[:space:]]+local_merchant_capacity = 1\.1$' \
	"$us09_trade_buildings_file" \
	'US-09 trade-building override must apply the +10% local_merchant_capacity compensation'
require_match '^[[:space:]]+local_max_rgo_size = 1$' \
	"$us09_rgo_static_modifier_file" \
	'US-09 base RGO size static modifier must be scalable through add_location_modifier size'
require_match 'cbp_apply_us09_base_rgo_size_bonus = yes' \
	packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt \
	'US-09 base RGO size bonus must be applied by the Economy package on game start/load'
require_match 'cbp_refresh_us09_base_rgo_size_bonus_for_current_country = yes' \
	packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt \
	'US-09 base RGO size bonus must be refreshed by the Economy package monthly country pulse'
require_match 'every_location_in_the_world = \{' \
	"$us09_rgo_size_effects_file" \
	'US-09 base RGO size initial effect must iterate every world location through the confirmed iterator'
require_match 'every_owned_location = \{' \
	"$us09_rgo_size_effects_file" \
	'US-09 base RGO size monthly refresh must iterate owned locations from country scope'
require_match '^[[:space:]]*modifier = cbp_us09_base_rgo_size_10_percent_bonus$' \
	"$us09_rgo_size_effects_file" \
	'US-09 base RGO size effect must apply the generated static modifier'
require_match '^[[:space:]]*size = scope:cbp_us09_base_rgo_size_bonus_modifier_size$' \
	"$us09_rgo_size_effects_file" \
	'US-09 base RGO size effect must apply the monthly computed modifier size'
require_match '^[[:space:]]*multiply = 0\.000025$' \
	"$us09_rgo_size_effects_file" \
	'US-09 base RGO size effect must include the 10% population component'
require_match '^[[:space:]]*multiply = 0\.025$' \
	"$us09_rgo_size_effects_file" \
	'US-09 base RGO size effect must document the display-equivalent population formula'

stale_us09_override_files="$(
	{
		find packages/cbp_economy_rebalance/in_game/common/building_types -maxdepth 1 -type f -name 'zzzz_cbp_us09_*.txt' 2>/dev/null
		find packages/cbp_economy_rebalance/in_game/common/prices -maxdepth 1 \( -name 'zzzz_cbp_us09_expand_rgo_prices.txt' -o -name 'expand_rgo_prices.txt' \) 2>/dev/null
	} | sort -u
)"
if [[ -n "$stale_us09_override_files" ]]; then
	printf 'US-09 static overrides must preserve vanilla file paths; remove stale duplicate-key files:\n%s\n' "$stale_us09_override_files" >&2
	exit 1
fi

generated_stock_helpers="in_game/common/scripted_effects/cbp_stock_goods_generated.txt"
generated_us00_modifiers="main_menu/common/static_modifiers/cbp_us00_modifiers_generated.txt"
generated_us00_modifier_localization="main_menu/localization/english/cbp_us00_static_modifiers_generated_l_english.yml"
generated_us10_table="in_game/gui/cbp_us10_stock_table.gui"
generated_us10_market_production="in_game/common/scripted_effects/cbp_us10_ui_market_production_effects.txt"
stock_adapter_template="tools/templates/cbp_stock_good_adapter.template.txt"
stock_generator="tools/generate_stock_good_helpers.sh"
us10_ui_generator="tools/generate_us10_ui_helpers.sh"
stock_postprocessor="tools/postprocess_perf14_promotion_guards.py"
stock_overmaterialized_repair_postprocessor="tools/postprocess_perf14_overmaterialized_repair.py"
perf14_guarded_test_effects="packages/cbp_core_tests/in_game/common/scripted_effects/cbp_perf14_guarded_test_effects.txt"
perf14_test_effects="packages/cbp_core_tests/in_game/common/scripted_effects/cbp_perf14_test_effects.txt"
generator_validator="tools/validate_generators.sh"
script_safety_validator="tools/validate_cbp_script_safety.sh"
generated_stock_helpers_tmp="$(mktemp)"
generated_us00_modifiers_tmp="$(mktemp)"
generated_us00_modifier_localization_tmp="$(mktemp)"
generated_us10_table_tmp="$(mktemp)"
generated_us10_market_production_tmp="$(mktemp)"
perf14_guarded_test_effects_tmp="$(mktemp)"
perf14_test_effects_tmp="$(mktemp)"
trap 'rm -f "$generated_stock_helpers_tmp" "$generated_us00_modifiers_tmp" "$generated_us00_modifier_localization_tmp" "$generated_us10_table_tmp" "$generated_us10_market_production_tmp" "$perf14_guarded_test_effects_tmp" "$perf14_test_effects_tmp"' EXIT

require_file "$stock_adapter_template"
require_file "$stock_generator"
require_file "$us10_ui_generator"
require_file "$stock_postprocessor"
require_file "$stock_overmaterialized_repair_postprocessor"
require_file "$perf14_guarded_test_effects"
require_file "$perf14_test_effects"
require_file "$generator_validator"
require_file "$script_safety_validator"
require_file "$generated_stock_helpers"
require_file "$generated_us00_modifiers"
require_file "$generated_us00_modifier_localization"
require_file "$generated_us10_table"
require_file "$generated_us10_market_production"

bash "$generator_validator" >/dev/null
bash "$script_safety_validator" >/dev/null

"$stock_generator" \
	"$generated_stock_helpers_tmp" \
	"$generated_us00_modifiers_tmp" \
	"$generated_us00_modifier_localization_tmp"
python3 "$stock_postprocessor" "$generated_stock_helpers_tmp"
cp "$perf14_guarded_test_effects" "$perf14_guarded_test_effects_tmp"
cp "$perf14_test_effects" "$perf14_test_effects_tmp"
python3 "$stock_overmaterialized_repair_postprocessor" \
	"$generated_stock_helpers_tmp" \
	"$perf14_guarded_test_effects_tmp" \
	"$perf14_test_effects_tmp"
bash "$us10_ui_generator" \
	"$generated_us10_table_tmp" \
	"$generated_us10_market_production_tmp"

if ! cmp -s "$generated_stock_helpers" "$generated_stock_helpers_tmp"; then
	printf 'Generated stock helpers are stale. Run tools/generate_all.sh.\n' >&2
	exit 1
fi
if ! cmp -s "$generated_us00_modifiers" "$generated_us00_modifiers_tmp"; then
	printf 'Generated US-00 production modifiers are stale. Run tools/generate_all.sh.\n' >&2
	exit 1
fi
if ! cmp -s "$generated_us00_modifier_localization" "$generated_us00_modifier_localization_tmp"; then
	printf 'Generated US-00 production modifier localization is stale. Run tools/generate_all.sh.\n' >&2
	exit 1
fi
if ! cmp -s "$generated_us10_table" "$generated_us10_table_tmp"; then
	printf 'Generated US-10 UI table is stale. Run tools/generate_all.sh.\n' >&2
	exit 1
fi
if ! cmp -s "$generated_us10_market_production" "$generated_us10_market_production_tmp"; then
	printf 'Generated US-10 UI market-production helpers are stale. Run tools/generate_all.sh.\n' >&2
	exit 1
fi

if search_lines '\$[^$]+\$|__[A-Z_]+__' "$generated_stock_helpers"; then
	printf 'Generated stock adapters must contain only literal identifiers.\n' >&2
	exit 1
fi
if search_lines '\$[^$]+\$|__[A-Z_]+__' "$generated_us00_modifiers"; then
	printf 'Generated US-00 production modifiers must contain only literal identifiers.\n' >&2
	exit 1
fi
if search_lines '\$[^$]+\$|__[A-Z_]+__' "$generated_us00_modifier_localization"; then
	printf 'Generated US-00 production modifier localization must contain only literal identifiers.\n' >&2
	exit 1
fi

require_match 'variable_map\(cbp_wheat_stock_by_market\|scope:cbp_market\)' \
	"$generated_stock_helpers" \
	'Generated stock adapters must contain literal per-good map access'
require_match 'cbp_load_capacity_breakdown = yes' \
	"$generated_stock_helpers" \
	'Generated stock adapters must read shared US-02 capacity through the shared helper'
require_match 'cbp_us00_full_ledger_persistence_allowed_trigger = yes' \
	"$generated_stock_helpers" \
	'Generated stock adapters must gate full US-00 diagnostic ledger writes'
require_match 'cbp_wheat_us00_active_record_by_market' \
	"$generated_stock_helpers" \
	'Generated stock adapters must preserve the PERF-15 / US-00 active-record marker'
require_match 'cbp_us10_ui_capture_market_produced_row = \{ good = wheat key = wheat \}' \
	"$generated_us10_market_production" \
	'Generated US-10 UI helpers must contain literal per-good produced-by-market capture'
require_match "gui_cbp_us10_ui_wheat_visible" \
	"$generated_us10_table" \
	'Generated US-10 UI table must contain literal per-good visibility bindings'

printf '%s\n' 'ModeU5 module package validation passed'

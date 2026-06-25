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

tracked_generated_files="$(git ls-files | grep -E '(^|/)modeu5_[^/]*_generated(\.txt|_l_english\.yml)$' || true)"
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
	"packages/modeu5_economy_rebalance/descriptor.mod"
	"packages/modeu5_trade_rebalance/descriptor.mod"
	"packages/modeu5_war_rebalance/descriptor.mod"
	"packages/modeu5_core_tests/descriptor.mod"
)

metadata_files=(
	".metadata/metadata.json"
	"packages/modeu5_economy_rebalance/.metadata/metadata.json"
	"packages/modeu5_trade_rebalance/.metadata/metadata.json"
	"packages/modeu5_war_rebalance/.metadata/metadata.json"
	"packages/modeu5_core_tests/.metadata/metadata.json"
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
	"modeu5_core"
	"modeu5_economy_rebalance"
	"modeu5_trade_rebalance"
	"modeu5_war_rebalance"
	"modeu5_core_tests"
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
				.id == "modeu5_core" and
				.display_name == "No Void Economy (NVE)" and
				.resource_type == "mod" and
				.version == "0.1.*"
			)
		' "$metadata_file" >/dev/null
	done
else
	printf 'WARNING: jq is unavailable; JSON syntax was not checked.\n' >&2
fi

if search_lines 'set_global_variable = modeu5_(economy|trade|war)_rebalance_loaded' in_game; then
	printf 'Core must not manufacture companion package markers.\n' >&2
	exit 1
fi

require_match 'set_global_variable = modeu5_economy_rebalance_loaded' \
	packages/modeu5_economy_rebalance/in_game/common/on_action/modeu5_economy_package_on_actions.txt \
	'Economy companion package marker missing'
require_match 'set_global_variable = modeu5_trade_rebalance_loaded' \
	packages/modeu5_trade_rebalance/in_game/common/on_action/modeu5_trade_package_on_actions.txt \
	'Trade companion package marker missing'
require_match 'set_global_variable = modeu5_war_rebalance_loaded' \
	packages/modeu5_war_rebalance/in_game/common/on_action/modeu5_war_package_on_actions.txt \
	'War companion package marker missing'
require_match 'name = modeu5_core_package_version' \
	in_game/common/scripted_effects/modeu5_configuration_effects.txt \
	'Core package version marker missing'
require_match 'name = modeu5_economy_package_version' \
	packages/modeu5_economy_rebalance/in_game/common/on_action/modeu5_economy_package_on_actions.txt \
	'Economy package version marker missing'
require_match 'name = modeu5_trade_package_version' \
	packages/modeu5_trade_rebalance/in_game/common/on_action/modeu5_trade_package_on_actions.txt \
	'Trade package version marker missing'
require_match 'name = modeu5_war_package_version' \
	packages/modeu5_war_rebalance/in_game/common/on_action/modeu5_war_package_on_actions.txt \
	'War package version marker missing'

generated_stock_helpers="in_game/common/scripted_effects/modeu5_stock_goods_generated.txt"
generated_us00_modifiers="main_menu/common/static_modifiers/modeu5_us00_modifiers_generated.txt"
generated_us00_modifier_localization="main_menu/localization/english/modeu5_us00_static_modifiers_generated_l_english.yml"
stock_adapter_template="tools/templates/modeu5_stock_good_adapter.template.txt"
stock_generator="tools/generate_stock_good_helpers.sh"
generated_stock_helpers_tmp="$(mktemp)"
generated_us00_modifiers_tmp="$(mktemp)"
generated_us00_modifier_localization_tmp="$(mktemp)"
trap 'rm -f "$generated_stock_helpers_tmp" "$generated_us00_modifiers_tmp" "$generated_us00_modifier_localization_tmp"' EXIT

require_file "$stock_adapter_template"
require_file "$stock_generator"
require_file "$generated_stock_helpers"
require_file "$generated_us00_modifiers"
require_file "$generated_us00_modifier_localization"

"$stock_generator" \
	"$generated_stock_helpers_tmp" \
	"$generated_us00_modifiers_tmp" \
	"$generated_us00_modifier_localization_tmp"

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

require_match 'variable_map\(modeu5_wheat_stock_by_market\|scope:modeu5_market\)' \
	"$generated_stock_helpers" \
	'Generated stock adapters must contain literal per-good map access'
require_match 'modeu5_load_capacity_breakdown = yes' \
	"$generated_stock_helpers" \
	'Generated stock adapters must read shared US-02 capacity through the shared helper'
require_match 'modeu5_us00_full_ledger_persistence_allowed_trigger = yes' \
	"$generated_stock_helpers" \
	'Generated stock adapters must gate full US-00 diagnostic ledger writes'
require_match 'modeu5_wheat_us00_active_record_by_market' \
	"$generated_stock_helpers" \
	'Generated stock adapters must preserve the PERF-15 / US-00 active-record marker'

printf '%s\n' 'ModeU5 module package validation passed'

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

	test -f "$descriptor"
	search_quiet "^name=\"${expected_name}\"$" "$descriptor"
	search_quiet '^version="0\.1\.0"$' "$descriptor"
done

if command -v jq >/dev/null 2>&1; then
	jq empty "${metadata_files[@]}"
	for index in "${!metadata_files[@]}"; do
		metadata_file="${metadata_files[$index]}"
		expected_id="${expected_ids[$index]}"
		expected_name="${expected_metadata_names[$index]}"
		expected_description_prefix="${expected_description_prefixes[$index]}"

		test "$(jq -r '.id' "$metadata_file")" = "$expected_id"
		test "$(jq -r '.name' "$metadata_file")" = "$expected_name"
		test "$(jq -r '.version' "$metadata_file")" = "0.1.0"
		test "$(jq -r '.short_description | startswith($prefix)' --arg prefix "$expected_description_prefix" "$metadata_file")" = "true"
	done

	jq -e '.relationships == []' ".metadata/metadata.json" >/dev/null
	for metadata_file in "${metadata_files[@]:1}"; do
		jq -e '
			.relationships == [
				{
					"rel_type": "dependency",
					"id": "modeu5_core",
					"display_name": "No Void Economy (NVE)",
					"resource_type": "mod",
					"version": "0.1.*"
				}
			]
		' "$metadata_file" >/dev/null
	done
else
	printf 'WARNING: jq is unavailable; JSON syntax was not checked.\n' >&2
fi

if search_lines 'set_global_variable = modeu5_(economy|trade|war)_rebalance_loaded' in_game; then
	printf 'Core must not manufacture companion package markers.\n' >&2
	exit 1
fi

search_quiet 'set_global_variable = modeu5_economy_rebalance_loaded' \
	packages/modeu5_economy_rebalance/in_game/common/on_action/modeu5_economy_package_on_actions.txt
search_quiet 'set_global_variable = modeu5_trade_rebalance_loaded' \
	packages/modeu5_trade_rebalance/in_game/common/on_action/modeu5_trade_package_on_actions.txt
search_quiet 'set_global_variable = modeu5_war_rebalance_loaded' \
	packages/modeu5_war_rebalance/in_game/common/on_action/modeu5_war_package_on_actions.txt
search_quiet 'name = modeu5_core_package_version' \
	in_game/common/scripted_effects/modeu5_configuration_effects.txt
search_quiet 'name = modeu5_economy_package_version' \
	packages/modeu5_economy_rebalance/in_game/common/on_action/modeu5_economy_package_on_actions.txt
search_quiet 'name = modeu5_trade_package_version' \
	packages/modeu5_trade_rebalance/in_game/common/on_action/modeu5_trade_package_on_actions.txt
search_quiet 'name = modeu5_war_package_version' \
	packages/modeu5_war_rebalance/in_game/common/on_action/modeu5_war_package_on_actions.txt

generated_stock_helpers="in_game/common/scripted_effects/modeu5_stock_goods_generated.txt"
stock_adapter_template="tools/templates/modeu5_stock_good_adapter.template.txt"
stock_generator="tools/generate_stock_good_helpers.sh"
generated_stock_helpers_tmp="$(mktemp)"
trap 'rm -f "$generated_stock_helpers_tmp"' EXIT

test -f "$stock_adapter_template"
./tools/generate_stock_good_helpers.sh "$generated_stock_helpers_tmp"

if ! cmp -s "$generated_stock_helpers" "$generated_stock_helpers_tmp"; then
	printf 'Generated stock helpers are stale. Run tools/generate_stock_good_helpers.sh.\n' >&2
	exit 1
fi

if search_lines '\$[^$]+\$|__[A-Z_]+__' "$generated_stock_helpers"; then
	printf 'Generated stock adapters must contain only literal identifiers.\n' >&2
	exit 1
fi

if ! search_quiet 'variable_map\(modeu5_wheat_stock_by_market\|scope:modeu5_market\)' \
	"$generated_stock_helpers"; then
	printf 'Generated stock adapters must contain literal per-good map access.\n' >&2
	exit 1
fi

if search_lines 'has_(global_)?variable_map|is_key_in_(global_)?variable_map|variable_map\(|add_to_(global_)?variable_map|remove_from_(global_)?variable_map' \
	"$stock_generator"; then
	printf 'The shell generator must not own EU5 storage behavior; keep it in the adapter template.\n' >&2
	exit 1
fi

stock_effects="in_game/common/scripted_effects/modeu5_stock_effects.txt"
stock_test_effects="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_stock_test_effects.txt"
stock_test_event="packages/modeu5_core_tests/in_game/events/modeu5_debug_events.txt"

if search_lines '\$(stock_map|capacity_map|market_map)\$|has_(global_)?variable_map|is_key_in_(global_)?variable_map|variable_map\(|add_to_(global_)?variable_map|remove_from_(global_)?variable_map' \
	"$stock_effects"; then
	printf 'Shared stock calculations must not construct, forward, read, or write persistent map identifiers.\n' >&2
	exit 1
fi

if search_lines '^[[:space:]]*max = 0[[:space:]]*$|^[[:space:]]*min = scope:modeu5_(available_capacity|country_stock_before|seller_stock_before)[[:space:]]*$' \
	"$stock_effects"; then
	printf 'EU5 script values use min as the lower bound and max as the upper bound; stock clamps are reversed.\n' >&2
	exit 1
fi

if search_lines '(var|global_var):modeu5_test_[a-z_]+_passed[[:space:]]*=' \
	"$stock_test_event"; then
	printf 'Stock test result events must use presence triggers so unset markers remain valid failures.\n' >&2
	exit 1
fi

printf 'ModeU5 package descriptors, Core dependencies, package-owned markers, and literal stock adapters are valid.\n'

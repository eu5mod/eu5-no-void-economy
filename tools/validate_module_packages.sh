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

if ! search_quiet 'variable_map\(modeu5_wheat_base_capacity_by_market\|scope:modeu5_market\)' \
	"$generated_stock_helpers"; then
	printf 'Generated stock adapters must contain literal US-02 capacity breakdown access.\n' >&2
	exit 1
fi

for required_effect in \
	modeu5_read_country_stock_record_good_wheat \
	modeu5_recalculate_country_market_capacity_good_wheat \
	modeu5_scan_stock_sources_good_wheat \
	modeu5_rebuild_market_stock_good_wheat \
	modeu5_validate_stock_consistency_good_wheat; do
	if ! search_quiet "^${required_effect} = \\{" "$generated_stock_helpers"; then
		printf 'Generated stock adapters are missing %s.\n' "$required_effect" >&2
		exit 1
	fi
done

if search_lines 'has_(global_)?variable_map|is_key_in_(global_)?variable_map|variable_map\(|add_to_(global_)?variable_map|remove_from_(global_)?variable_map' \
	"$stock_generator"; then
	printf 'The shell generator must not own EU5 storage behavior; keep it in the adapter template.\n' >&2
	exit 1
fi

stock_effects="in_game/common/scripted_effects/modeu5_stock_effects.txt"
capacity_effects="in_game/common/scripted_effects/modeu5_capacity_effects.txt"
stock_test_effects="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_stock_test_effects.txt"
capacity_test_effects="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_capacity_test_effects.txt"
stock_test_event="packages/modeu5_core_tests/in_game/events/modeu5_debug_events.txt"
us01_test_event="packages/modeu5_core_tests/in_game/events/modeu5_us01_debug_events.txt"
us02_test_event="packages/modeu5_core_tests/in_game/events/modeu5_us02_debug_events.txt"

test -f "$stock_effects"
test -f "$capacity_effects"
test -f "$stock_test_effects"
test -f "$capacity_test_effects"
test -f "$stock_test_event"
test -f "$us01_test_event"
test -f "$us02_test_event"
core02_probe_on_action="packages/modeu5_core_tests/in_game/common/on_action/modeu5_core02_exposure_on_actions.txt"
core02_probe_effect="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_core02_exposure_effects.txt"
core02_probe_event="packages/modeu5_core_tests/in_game/events/modeu5_core02_exposure_events.txt"
core02_probe_localization="packages/modeu5_core_tests/main_menu/localization/english/modeu5_core02_exposure_l_english.yml"

for required_probe_file in \
	"$core02_probe_on_action" \
	"$core02_probe_effect" \
	"$core02_probe_event" \
	"$core02_probe_localization"; do
	if [[ ! -f "$required_probe_file" ]]; then
		printf 'The CORE-02 exposure probe is missing from the testing package: %s\n' \
			"$required_probe_file" >&2
		exit 1
	fi
done

for forbidden_core_probe_file in \
	in_game/common/on_action/modeu5_core02_exposure_on_actions.txt \
	in_game/common/scripted_effects/modeu5_core02_exposure_effects.txt \
	in_game/events/modeu5_core02_exposure_events.txt \
	main_menu/localization/english/modeu5_core02_exposure_l_english.yml; do
	if [[ -e "$forbidden_core_probe_file" ]]; then
		printf 'Test-only CORE-02 probe file must not be loaded by Core: %s\n' \
			"$forbidden_core_probe_file" >&2
		exit 1
	fi
done

if search_lines '\$(stock_map|capacity_map|market_map)\$|has_(global_)?variable_map|is_key_in_(global_)?variable_map|variable_map\(|add_to_(global_)?variable_map|remove_from_(global_)?variable_map' \
	"$stock_effects"; then
	printf 'Shared stock calculations must not construct, forward, read, or write persistent map identifiers.\n' >&2
	exit 1
fi

if search_lines 'has_(global_)?variable_map|is_key_in_(global_)?variable_map|variable_map\(|add_to_(global_)?variable_map|remove_from_(global_)?variable_map' \
	"$capacity_effects"; then
	printf 'Shared US-02 capacity calculations must not read or write persistent map identifiers.\n' >&2
	exit 1
fi

if search_lines '^[[:space:]]*max = 0[[:space:]]*$|^[[:space:]]*min = scope:modeu5_(available_capacity|country_stock_before|seller_stock_before)[[:space:]]*$' \
	"$stock_effects"; then
	printf 'EU5 script values use min as the lower bound and max as the upper bound; stock clamps are reversed.\n' >&2
	exit 1
fi

if search_lines '(var|global_var):modeu5_test_[a-z_]+_passed[[:space:]]*=' \
	"$stock_test_event" "$us01_test_event" "$us02_test_event"; then
	printf 'Stock test result events must use presence triggers so unset markers remain valid failures.\n' >&2
	exit 1
fi

if search_lines 'modeu5_debug_run_(country_stock_dimension|storage_capacity)_test' \
	"$stock_test_event"; then
	printf 'US-01 and US-02 tests must use dedicated events instead of modeu5_debug.1.\n' >&2
	exit 1
fi

if ! search_quiet 'modeu5_debug_run_country_stock_dimension_test' "$stock_test_effects"; then
	printf 'US-01 stock-dimension test helper is missing from the test package.\n' >&2
	exit 1
fi

if ! search_quiet 'modeu5_debug_run_storage_capacity_test' "$capacity_test_effects"; then
	printf 'US-02 storage-capacity test helper is missing from the test package.\n' >&2
	exit 1
fi

if ! search_quiet '^modeu5_us01_debug\.1 = \{' "$us01_test_event"; then
	printf 'US-01 tests must use a dedicated event instead of modeu5_debug.1.\n' >&2
	exit 1
fi

if ! search_quiet '^modeu5_us02_debug\.1 = \{' "$us02_test_event"; then
	printf 'US-02 tests must use a dedicated event instead of modeu5_debug.1.\n' >&2
	exit 1
fi

if search_lines 'test_log[[:space:]]*=' "$stock_test_event" "$us01_test_event" "$us02_test_event" "$stock_test_effects" "$capacity_test_effects"; then
	printf 'Console-driven stock tests must not use test_log; it localizes text while console command localization is disabled.\n' >&2
	exit 1
fi

if search_lines 'debug_log[[:space:]]*=' "$stock_test_event" "$us01_test_event" "$us02_test_event" "$stock_test_effects"; then
	printf 'Console-driven deterministic stock tests must not use debug_log outside explicitly approved log-dump probes.\n' >&2
	exit 1
fi

disallowed_capacity_debug_log="$(
	search_lines 'debug_log[[:space:]]*=' "$capacity_test_effects" 2>/dev/null | grep -v 'ModeU5 US-02 ' || true
)"
if [ -n "$disallowed_capacity_debug_log" ]; then
	printf 'US-02 capacity tests may use debug_log only for explicitly prefixed ModeU5 US-02 dumps/results.\n' >&2
	printf '%s\n' "$disallowed_capacity_debug_log" >&2
	exit 1
fi

if search_lines 'add_to_global_variable_map|remove_from_global_variable_map' \
	"$stock_test_effects"; then
	printf 'Deterministic tests must use the centralized test fault injector instead of mutating market stock directly.\n' >&2
	exit 1
fi

printf 'ModeU5 package descriptors, Core dependencies, package-owned markers, and literal stock adapters are valid.\n'

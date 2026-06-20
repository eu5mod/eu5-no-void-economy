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

has_utf8_bom() {
	local file="$1"

	LC_ALL=C perl -e '
		binmode STDIN;
		my $bytes = "";
		my $read = read STDIN, $bytes, 3;
		exit(($read == 3 && $bytes eq "\xEF\xBB\xBF") ? 0 : 1);
	' < "$file"
}

localization_starts_with_l_english_after_bom() {
	local file="$1"

	LC_ALL=C perl -e '
		binmode STDIN;
		my $line = <STDIN>;
		exit 1 unless defined $line;
		$line =~ s/^\xEF\xBB\xBF//;
		exit($line =~ /^l_english:/ ? 0 : 1);
	' < "$file"
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

		first_metadata_key="$(sed -n '/^[[:space:]]*"/{s/^[[:space:]]*"\([^"]*\)".*/\1/p;q;}' "$metadata_file")"
		if [ "$first_metadata_key" != "id" ]; then
			printf 'ModeU5 metadata must start with id as the first member: %s\n' "$metadata_file" >&2
			exit 1
		fi
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
generated_us00_modifiers="main_menu/common/static_modifiers/modeu5_us00_modifiers_generated.txt"
generated_us00_modifier_localization="main_menu/localization/english/modeu5_us00_static_modifiers_generated_l_english.yml"
stock_adapter_template="tools/templates/modeu5_stock_good_adapter.template.txt"
stock_generator="tools/generate_stock_good_helpers.sh"
generated_stock_helpers_tmp="$(mktemp)"
generated_us00_modifiers_tmp="$(mktemp)"
generated_us00_modifier_localization_tmp="$(mktemp)"
us09_generated_tmp_dir=""
trap 'rm -f "$generated_stock_helpers_tmp" "$generated_us00_modifiers_tmp" "$generated_us00_modifier_localization_tmp"; if [[ -n "${us09_generated_tmp_dir:-}" ]]; then rm -rf "$us09_generated_tmp_dir"; fi' EXIT

test -f "$stock_adapter_template"
if [[ ! -f "$generated_stock_helpers" ]]; then
	printf 'Generated stock helpers are missing. Run tools/generate_all.sh.\n' >&2
	exit 1
fi
if [[ ! -f "$generated_us00_modifiers" ]]; then
	printf 'Generated US-00 production modifiers are missing. Run tools/generate_all.sh.\n' >&2
	exit 1
fi
if [[ ! -f "$generated_us00_modifier_localization" ]]; then
	printf 'Generated US-00 production modifier localization is missing. Run tools/generate_all.sh.\n' >&2
	exit 1
fi

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

if ! search_quiet 'variable_map\(modeu5_wheat_stock_by_market\|scope:modeu5_market\)' \
	"$generated_stock_helpers"; then
	printf 'Generated stock adapters must contain literal per-good map access.\n' >&2
	exit 1
fi

if ! search_quiet 'variable_map\(modeu5_stock_cap_by_market\|scope:modeu5_market\)' \
	"$generated_stock_helpers"; then
	printf 'Generated stock adapters must contain shared US-02 country-market capacity access.\n' >&2
	exit 1
fi
if ! search_quiet 'variable_map\(modeu5_base_capacity_by_market\|scope:modeu5_market\)' \
	"$generated_stock_helpers"; then
	printf 'Generated stock adapters must contain shared US-02 capacity breakdown access.\n' >&2
	exit 1
fi
if search_lines 'modeu5_[a-z0-9_]+_(stock_cap|base_capacity|building_capacity|foreign_capacity)_by_market' \
	"$generated_stock_helpers" "$stock_adapter_template" "$stock_generator"; then
	printf 'US-02 capacity must be stored once per country-market, not once per good.\n' >&2
	exit 1
fi
if ! search_quiet '^modeu5_wheat_production_penalty_modifier = \{' "$generated_us00_modifiers"; then
	printf 'Generated US-00 production modifiers must contain the wheat modifier fixture.\n' >&2
	exit 1
fi
if ! search_quiet 'category = location' "$generated_us00_modifiers"; then
	printf 'Generated US-00 production modifiers must be location static modifiers.\n' >&2
	exit 1
fi
if [[ "$(LC_ALL=C head -c 3 "$generated_us00_modifier_localization" | od -An -tx1 | tr -d ' \n')" != "efbbbf" ]]; then
	printf 'Generated US-00 production modifier localization must use UTF-8 BOM encoding: %s\n' \
		"$generated_us00_modifier_localization" >&2
	exit 1
fi
if ! LC_ALL=C perl -0pe 's/^\xEF\xBB\xBF//' "$generated_us00_modifier_localization" | head -n 1 | grep -q '^l_english:'; then
	printf 'Generated US-00 production modifier localization must start with l_english: after the BOM: %s\n' \
		"$generated_us00_modifier_localization" >&2
	exit 1
fi
if ! search_quiet '^[[:space:]]STATIC_MODIFIER_NAME_modeu5_wheat_production_penalty_modifier:' \
	"$generated_us00_modifier_localization"; then
	printf 'Generated US-00 production modifier localization must contain the wheat modifier fixture.\n' >&2
	exit 1
fi

for required_effect in \
	modeu5_read_country_stock_record_good_wheat \
	modeu5_recalculate_country_market_capacity_good_wheat \
	modeu5_recalculate_country_market_capacity_from_prepared_pool_good_wheat \
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

us09_generator="tools/generate_us09_economy_overrides.sh"
us09_percent="5"
if [[ -x "$us09_generator" ]]; then
	us09_generated_tmp_dir="$(mktemp -d)"
	if "$us09_generator" "$us09_percent" --package-common-dir "$us09_generated_tmp_dir/common" >/dev/null 2>&1; then
		for generated_subdir in building_types prices; do
			tmp_generated_dir="$us09_generated_tmp_dir/common/$generated_subdir"
			if ! find "$tmp_generated_dir" -maxdepth 1 -type f -name 'zzzz_modeu5_us09_*.txt' | grep -q .; then
				printf 'US-09 offline generator produced no %s probe files.\n' "$generated_subdir" >&2
				exit 1
			fi
		done
	else
		printf 'WARNING: US-09 generator could not run; generated economy override staleness was not checked.\n' >&2
	fi
fi

stock_effects="in_game/common/scripted_effects/modeu5_stock_effects.txt"
capacity_effects="in_game/common/scripted_effects/modeu5_capacity_effects.txt"
stock_test_effects="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_stock_test_effects.txt"
capacity_test_effects="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_capacity_test_effects.txt"
core03_test_effects="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_core03_test_effects.txt"
revalidation_test_effects="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_revalidation_test_effects.txt"
stock_test_event="packages/modeu5_core_tests/in_game/events/modeu5_debug_events.txt"
us01_test_event="packages/modeu5_core_tests/in_game/events/modeu5_us01_debug_events.txt"
us02_test_event="packages/modeu5_core_tests/in_game/events/modeu5_us02_debug_events.txt"
core03_test_event="packages/modeu5_core_tests/in_game/events/modeu5_core03_debug_events.txt"
revalidation_test_event="packages/modeu5_core_tests/in_game/events/modeu5_revalidate_debug_events.txt"
revalidation_summary_tool="tools/summarize_modeu5_test_logs.sh"

test -f "$stock_effects"
test -f "$capacity_effects"
test -f "$stock_test_effects"
test -f "$capacity_test_effects"
test -f "$core03_test_effects"
test -f "$revalidation_test_effects"
test -f "$stock_test_event"
test -f "$us01_test_event"
test -f "$us02_test_event"
test -f "$core03_test_event"
test -f "$revalidation_test_event"
test -x "$revalidation_summary_tool"
core02_probe_on_action="packages/modeu5_core_tests/in_game/common/on_action/modeu5_core02_exposure_on_actions.txt"
core02_probe_effect="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_core02_exposure_effects.txt"
core02_probe_event="packages/modeu5_core_tests/in_game/events/modeu5_core02_exposure_events.txt"
core02_probe_localization="packages/modeu5_core_tests/in_game/localization/modeu5_core02_exposure_l_english.yml"
core_stock_localization="in_game/localization/modeu5_stock_l_english.yml"
core03_exposure_localization="in_game/localization/modeu5_core03_exposure_l_english.yml"
game_rules_localization="main_menu/localization/english/modeu5_game_rules_l_english.yml"

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

for required_localization_file in \
	"in_game/localization/modeu5_l_english.yml" \
	"$core_stock_localization" \
	"$core03_exposure_localization" \
	"$generated_us00_modifier_localization" \
	"$core02_probe_localization" \
	"$game_rules_localization"; do
	if [[ ! -f "$required_localization_file" ]]; then
		printf 'Required ModeU5 localization file is missing: %s\n' \
			"$required_localization_file" >&2
		exit 1
	fi
	if ! has_utf8_bom "$required_localization_file"; then
		printf 'ModeU5 localization file must use UTF-8 BOM encoding: %s\n' \
			"$required_localization_file" >&2
		exit 1
	fi
	if ! localization_starts_with_l_english_after_bom "$required_localization_file"; then
		printf 'ModeU5 localization file must start with l_english: after the BOM: %s\n' \
			"$required_localization_file" >&2
		exit 1
	fi
done

for in_game_key in \
	modeu5_debug.1.title \
	modeu5_us00_debug.1.title \
	modeu5_us02_debug.1.title \
	modeu5_core03_debug.1.title \
	modeu5_perf02_debug.1.title \
	modeu5_perf03_debug.1.title; do
	if ! search_quiet "^[[:space:]]${in_game_key}:" "$core_stock_localization"; then
		printf 'In-game test localization key is missing from %s: %s\n' \
			"$core_stock_localization" "$in_game_key" >&2
		exit 1
	fi
done

for probe_key in \
	modeu5_core03_probe.1.title \
	modeu5_core02_probe.1.title; do
	case "$probe_key" in
		modeu5_core03_probe.*)
			probe_localization_file="$core03_exposure_localization"
			;;
		modeu5_core02_probe.*)
			probe_localization_file="$core02_probe_localization"
			;;
	esac
	if ! search_quiet "^[[:space:]]${probe_key}:" "$probe_localization_file"; then
		printf 'In-game probe localization key is missing from %s: %s\n' \
			"$probe_localization_file" "$probe_key" >&2
		exit 1
	fi
done

for forbidden_core_probe_file in \
	in_game/common/on_action/modeu5_core02_exposure_on_actions.txt \
	in_game/common/scripted_effects/modeu5_core02_exposure_effects.txt \
	in_game/events/modeu5_core02_exposure_events.txt \
	main_menu/localization/english/modeu5_core02_exposure_l_english.yml \
	packages/modeu5_core_tests/main_menu/localization/english/modeu5_core02_exposure_l_english.yml; do
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

if search_lines 'limit = \{ modeu5_initialization_complete_trigger = yes \}' \
	"$stock_effects" "in_game/common/scripted_effects/modeu5_core03_succession_effects.txt"; then
	printf 'Runtime stock automation must use modeu5_stock_runtime_ready_trigger so CORE-02 schema state and initialization state stay aligned.\n' >&2
	exit 1
fi

if search_lines '(var|global_var):modeu5_test_[a-z_]+_passed[[:space:]]*=' \
	"$stock_test_event" "$us01_test_event" "$us02_test_event" "$core03_test_event"; then
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

if ! search_quiet 'modeu5_debug_run_core03_location_succession_test' "$core03_test_effects"; then
	printf 'CORE-03 location stock-succession test helper is missing from the test package.\n' >&2
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

if ! search_quiet '^modeu5_core03_debug\.1 = \{' "$core03_test_event"; then
	printf 'CORE-03 tests must use a dedicated event instead of modeu5_debug.1.\n' >&2
	exit 1
fi

if ! search_quiet '^modeu5_revalidate_debug\.1 = \{' "$revalidation_test_event"; then
	printf 'Main revalidation must use a dedicated event instead of modeu5_debug.1.\n' >&2
	exit 1
fi

if search_lines 'test_log[[:space:]]*=' "$stock_test_event" "$us01_test_event" "$us02_test_event" "$core03_test_event" "$revalidation_test_event" "$stock_test_effects" "$capacity_test_effects" "$core03_test_effects" "$revalidation_test_effects"; then
	printf 'Console-driven stock tests must not use test_log; it localizes text while console command localization is disabled.\n' >&2
	exit 1
fi

disallowed_stock_debug_log="$(
	search_lines 'debug_log[[:space:]]*=' "$stock_test_event" "$us01_test_event" "$us02_test_event" "$core03_test_event" "$revalidation_test_event" "$stock_test_effects" "$revalidation_test_effects" 2>/dev/null |
		grep -v 'ModeU5 CORE-01 ' |
		grep -v 'ModeU5 CORE-02 ' |
		grep -v 'ModeU5 US-11 ' |
		grep -v 'ModeU5 PERF-07 ' |
		grep -v 'ModeU5 TEST ' || true
)"
if [ -n "$disallowed_stock_debug_log" ]; then
	printf 'Console-driven deterministic stock tests may use debug_log only for approved static RESULT markers or explicitly approved log-dump probes.\n' >&2
	printf '%s\n' "$disallowed_stock_debug_log" >&2
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

disallowed_core03_debug_log="$(
	search_lines 'debug_log[[:space:]]*=' "$core03_test_effects" 2>/dev/null | grep -v 'ModeU5 CORE-03 ' || true
)"
if [ -n "$disallowed_core03_debug_log" ]; then
	printf 'CORE-03 stock-succession tests may use debug_log only for explicitly prefixed ModeU5 CORE-03 dumps/results.\n' >&2
	printf '%s\n' "$disallowed_core03_debug_log" >&2
	exit 1
fi

if search_lines 'add_to_global_variable_map|remove_from_global_variable_map' \
	"$stock_test_effects" "$core03_test_effects"; then
	printf 'Deterministic tests must use the centralized test fault injector instead of mutating market stock directly.\n' >&2
	exit 1
fi

printf 'ModeU5 package descriptors, Core dependencies, package-owned markers, and literal stock adapters are valid.\n'

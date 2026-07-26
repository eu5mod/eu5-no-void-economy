#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

local_config="${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"
if [[ -f "$local_config" ]]; then
	set -a
	# shellcheck source=/dev/null
	source "$local_config"
	set +a
fi

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
	tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh \
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

us09_prices_file="packages/cbp_economy_rebalance/in_game/common/prices/cbp_00_hardcoded.txt"
us09_trade_buildings_file="packages/cbp_economy_rebalance/in_game/common/building_types/trade_buildings.txt"
us09_market_buildings_file="packages/cbp_economy_rebalance/in_game/common/building_types/market_buildings.txt"
us09_rgo_static_modifier_file="packages/cbp_economy_rebalance/main_menu/common/static_modifiers/cbp_us09_rgo_static_modifiers.txt"
us09_rgo_size_effects_file="packages/cbp_economy_rebalance/in_game/common/scripted_effects/cbp_us09_rgo_size_effects.txt"
us09_market_stockpile_static_modifier_file="packages/cbp_economy_rebalance/main_menu/common/static_modifiers/cbp_market_stockpile_capacity.txt"
us09_market_stockpile_effects_file="packages/cbp_economy_rebalance/in_game/common/scripted_effects/cbp_market_stockpile_capacity_effects.txt"
us09_trade_capacity_percent=""
require_file "$us09_prices_file"
require_file "$us09_trade_buildings_file"
require_file "$us09_market_buildings_file"
require_file "$us09_rgo_static_modifier_file"
require_file "$us09_rgo_size_effects_file"
require_file "$us09_market_stockpile_static_modifier_file"
require_file "$us09_market_stockpile_effects_file"
require_match '^# Source: <EU5_GAME_COMMON_DIR>/prices/00_hardcoded\.txt$' \
	"$us09_prices_file" \
		'US-09 RGO price override must document its Vanilla source file'
require_match '^REPLACE:expand_rgo_gathering = \{$' \
	"$us09_prices_file" \
	'US-09 RGO price override must replace the Vanilla expand_rgo_gathering key without shadowing unrelated prices'
us09_trade_capacity_percent="$(
	python3 - "$us09_trade_buildings_file" <<'PY'
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(encoding="utf-8-sig").splitlines()

def header_value(label: str) -> tuple[float, float | None]:
    number = r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)"
    pattern = rf"^# {re.escape(label)}: ({number})(?: \(({number})%\))?$"
    for line in lines[:16]:
        match = re.match(pattern, line)
        if match:
            multiplier = float(match.group(1))
            percent = float(match.group(2)) if match.group(2) is not None else None
            return multiplier, percent
    raise SystemExit(f"US-09 trade-building override must document {label}")

trade_multiplier, trade_percent = header_value("Trade capacity multiplier")
if trade_percent is None:
    raise SystemExit("US-09 trade-capacity header must include the percent form")
if not math.isclose(trade_multiplier, 1 + trade_percent / 100, rel_tol=0, abs_tol=0.000001):
    raise SystemExit("US-09 trade-capacity multiplier and percent header disagree")

for label in (
    "Building maintenance multiplier",
    "Trade-building maintenance multiplier",
    "US-07 composed trade-building estate-power multiplier",
):
    header_value(label)

def code(line: str) -> str:
    return line.split("#", 1)[0]

def top_block(name: str) -> str:
    for index, line in enumerate(lines):
        if re.match(
            rf"^(?:(?:REPLACE|INJECT):)?{re.escape(name)}\s*=\s*\{{",
            code(line),
        ):
            depth = 0
            block: list[str] = []
            for child in lines[index:]:
                block.append(child)
                depth += code(child).count("{")
                depth -= code(child).count("}")
                if depth == 0:
                    return "\n".join(block)
    raise SystemExit(f"US-09 trade-building override must contain {name}")

def assignment(block: str, key: str) -> float:
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\b", block, re.M)
    if not match:
        raise SystemExit(f"US-09 trade-building override must contain {key}")
    return float(match.group(1))

def injected_assignment(block: str, key: str) -> tuple[float, float, float]:
    pattern = (
        rf"^\s*{re.escape(key)}\s*=\s*"
        r"(?P<delta>-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\s+"
        r"# VANILLA = (?P<vanilla>-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)); "
        r"TARGET = (?P<target>-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))$"
    )
    match = re.search(pattern, block, re.M)
    if not match:
        raise SystemExit(
            f"US-09 additive building override must trace {key} "
            "as delta, Vanilla, and target"
        )
    delta = float(match.group("delta"))
    vanilla = float(match.group("vanilla"))
    target = float(match.group("target"))
    if not math.isclose(vanilla + delta, target, rel_tol=0, abs_tol=0.000001):
        raise SystemExit(f"US-09 injected {key} delta does not reach its target")
    return delta, vanilla, target

marketplace_blocks = {
    name: top_block(name)
    for name in ("marketplace", "merchants_quarters", "grand_marketplace")
}
marketplace_maintenance: dict[str, float] | None = None
for name, block in marketplace_blocks.items():
    injected = block.lstrip().startswith("INJECT:")
    if injected:
        _delta, vanilla_capacity, merchant_capacity = injected_assignment(
            block, "local_merchant_capacity"
        )
        expected_capacity = vanilla_capacity * trade_multiplier
    else:
        trades_per_burgher = assignment(block, "local_trades_per_burgher")
        merchant_capacity = assignment(block, "local_merchant_capacity")
        expected_capacity = trades_per_burgher * trade_multiplier
    if not math.isclose(
        merchant_capacity,
        expected_capacity,
        rel_tol=0,
        abs_tol=0.000001,
    ):
        raise SystemExit(
            f"US-09 {name} local_merchant_capacity must equal "
            "local_trades_per_burgher x declared trade-capacity multiplier"
        )
    estate_power = (
        injected_assignment(block, "local_burghers_estate_power")[2]
        if injected
        else assignment(block, "local_burghers_estate_power")
    )
    if estate_power <= 0:
        raise SystemExit(f"US-09 {name} estate-power value must stay positive")

    maintenance_match = re.search(
        r"\b[A-Za-z0-9_]+_maintenance\s*=\s*\{(?P<body>.*?)^\s*\}",
        block,
        re.S | re.M,
    )
    if not maintenance_match and not injected:
        raise SystemExit(f"US-09 {name} must retain a maintenance block")
    if not maintenance_match:
        continue
    body = maintenance_match.group("body")
    values = {
        key: float(value)
        for key, value in re.findall(
            r"^\s*([A-Za-z0-9_]+)\s*=\s*(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\b",
            body,
            re.M,
        )
        if key != "category"
    }
    if not values:
        raise SystemExit(f"US-09 {name} maintenance block must retain goods")
    if marketplace_maintenance is None:
        marketplace_maintenance = values
    elif values != marketplace_maintenance:
        raise SystemExit(
            "US-08/US-05.3 composed marketplace maintenance must stay normalized "
            "across marketplace, merchants_quarters, and grand_marketplace"
        )

print(f"{trade_percent:g}")
PY
)"

python3 - "$us09_market_buildings_file" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8-sig").splitlines()

def code(line: str) -> str:
    return line.split("#", 1)[0]

stack: list[tuple[str, int, int]] = []
ranges: list[tuple[str, int, int, int]] = []
for index, line in enumerate(lines):
    match = re.match(r"^\s*(?:REPLACE:)?([A-Za-z0-9_]+)\s*=\s*\{", code(line))
    if match:
        stack.append((match.group(1), index, len(stack)))
    for _ in range(code(line).count("}")):
        if not stack:
            break
        key, start, depth = stack.pop()
        ranges.append((key, start, index, depth))

top_level = [item for item in ranges if item[0] == "market_warehouse" and item[3] == 0]
if not top_level:
    raise SystemExit("US-09 market-building override must contain market_warehouse")
_, start, end, depth = top_level[0]
children = {
    key: (child_start, child_end)
    for key, child_start, child_end, child_depth in ranges
    if start < child_start < end and child_depth == depth + 1
}
for key in ("country_potential", "location_potential"):
    if key not in children:
        raise SystemExit(f"US-09 market_warehouse override must contain {key}")
    child_start, child_end = children[key]
    child_text = "\n".join(lines[child_start : child_end + 1])
    if not re.search(r"\balways\s*=\s*no\b", child_text):
        raise SystemExit(f"US-09 market_warehouse {key} must be always = no")
PY
require_match '^[[:space:]]+local_max_rgo_size = 1$' \
	"$us09_rgo_static_modifier_file" \
	'US-09 base RGO size static modifier must be scalable through add_location_modifier size'
require_match 'cbp_apply_us09_base_rgo_size_bonus = yes' \
	packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt \
	'US-09 base RGO size bonus must be applied by the Economy package on game start/load'
require_match 'cbp_refresh_us09_base_rgo_size_bonus_for_current_country = yes' \
	packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt \
	'US-09 base RGO size bonus must be refreshed by the Economy package monthly country pulse'
require_match 'cbp_refresh_all_market_center_stockpile_capacity = yes' \
	packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt \
	'CBP market stockpile capacity must be applied by the Economy package on game start/load'
require_match 'cbp_refresh_market_center_stockpile_capacity_for_current_country = yes' \
	packages/cbp_economy_rebalance/in_game/common/on_action/cbp_economy_package_on_actions.txt \
	'CBP market stockpile capacity must be refreshed by the Economy package monthly country pulse'
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
require_match '^[[:space:]]*multiply = 0\.025$' \
	"$us09_rgo_size_effects_file" \
	'US-09 base RGO size effect must include the 10% population component'
require_match '^[[:space:]]*multiply = 0\.025$' \
	"$us09_rgo_size_effects_file" \
	'US-09 base RGO size effect must document the display-equivalent population formula'
require_match '^[[:space:]]*maximum_stockpile_capacity = 1$' \
	"$us09_market_stockpile_static_modifier_file" \
	'CBP market stockpile capacity static modifier must expose unit stockpile capacity'
require_match 'scope:cbp_market\.location = \{' \
	"$us09_market_stockpile_effects_file" \
	'CBP market stockpile capacity must apply to the market-center location'
require_match '^[[:space:]]*modifier = cbp_market_stockpile_capacity$' \
	"$us09_market_stockpile_effects_file" \
	'CBP market stockpile capacity effect must apply the CBP static modifier'
require_match 'every_market_center_in_country = \{' \
	"$us09_market_stockpile_effects_file" \
	'CBP market stockpile capacity monthly refresh must iterate market centers from country scope'
require_match '^[[:space:]]*STATIC_MODIFIER_cbp_us09_base_rgo_size_10_percent_bonus:0 "\(CBP\) 10% Bigger RGO"$' \
	packages/cbp_economy_rebalance/main_menu/localization/english/cbp_us09_rgo_l_english.yml \
	'US-09 base RGO size static modifier localization must include the engine-displayed STATIC_MODIFIER key'
require_match '^[[:space:]]*building_upkeep_costs = -1\.0$' \
	packages/cbp_economy_rebalance/in_game/common/auto_modifiers/cbp_building_upkeep_auto_modifiers.txt \
	'CBP building upkeep auto modifier must retain the -1.0 fail-closed Crown upkeep guard'
require_match '^[[:space:]]*BUILDING_UPKEEP_FACTOR = 0[[:space:]]+' \
	loading_screen/common/defines/cbp_rebase_scaling_cost.txt \
	'CBP zero Crown building upkeep must use the supported BUILDING_UPKEEP_FACTOR define'
if [[ -e packages/cbp_economy_rebalance/main_menu/common/static_modifiers/cbp_building_upkeep_static_modifiers.txt ]]; then
	printf '%s\n' 'CBP must not ship cbp_building_upkeep_static_modifiers.txt; its old REPLACE:years_since_game_start target does not exist in static_modifiers.' >&2
	exit 1
fi
# Preserve commented Vanilla provenance while rejecting an active assignment.
# A plain token search incorrectly flags lines such as
# `# building_upkeep_multiplier = 0.001` in generated building files.
if search_quiet '^[ \t]*building_upkeep_multiplier[ \t]*=' \
	packages/cbp_economy_rebalance/in_game/common/auto_modifiers \
	packages/cbp_economy_rebalance/main_menu/common/static_modifiers
then
	printf '%s\n' 'CBP building upkeep overrides must not use the invalid building_upkeep_multiplier modifier type.' >&2
	exit 1
fi

if [[ -n "${EU5_GAME_COMMON_DIR:-}" && -d "${EU5_GAME_COMMON_DIR:-}/building_types" ]]; then
	python3 tools/validate_us08_building_maintenance_overrides.py \
		--common-dir "$EU5_GAME_COMMON_DIR" \
		--package-common-dir packages/cbp_economy_rebalance/in_game/common \
		--generation-mode "${MODEU5_BUILDING_GENERATION_MODE:-override}" \
		--us09-percent "${MODEU5_US09_BONUS_PERCENT:-10}" \
		--trade-capacity-percent "$us09_trade_capacity_percent" \
		--maintenance-multiplier "${MODEU5_US08_BUILDING_MAINTENANCE_MULTIPLIER:-0.7}" \
			--trade-building-maintenance-multiplier "${MODEU5_US08_TRADE_BUILDING_MAINTENANCE_MULTIPLIER:-0.5}"
fi

unsafe_building_replace_outputs="$(
	find packages/cbp_economy_rebalance/in_game/common/building_types \
		-maxdepth 1 -type f -name 'cbp_*.txt' ! -name 'cbp_inject_*.txt' -print 2>/dev/null | sort
)"
if [[ -n "$unsafe_building_replace_outputs" ]]; then
	printf '%s\n' \
		'CBP structural building outputs must use complete exact-path files.' \
		'REPLACE:<building> does not purge Vanilla nested production methods:' \
		"$unsafe_building_replace_outputs" >&2
	exit 1
fi
if search_lines \
	'^[[:space:]]*(REPLACE|INJECT|TRY_INJECT):(unique_production_methods|production_methods|possible_production_methods)[[:space:]]*=' \
	packages/cbp_economy_rebalance/in_game/common/building_types
then
	printf '%s\n' \
		'Nested production-method containers must use plain field names.' \
		'No inspected M&T building uses REPLACE/INJECT on these containers, and CBP has no confirmed recursive replacement contract.' >&2
	exit 1
fi
if ! find packages/cbp_economy_rebalance/in_game/common/building_types \
	-maxdepth 1 -type f -name '*.txt' -print0 |
	while IFS= read -r -d '' building_output; do
		case "$(basename "$building_output")" in
			cbp_inject_*)
				if ! grep -Eq '^[[:space:]]*INJECT:[A-Za-z0-9_.:-]+[[:space:]]*=' "$building_output" ||
					grep -Eq '^[[:space:]]*(REPLACE|TRY_INJECT):' "$building_output"; then
					printf 'Generated additive building output must contain only INJECT entries: %s\n' "$building_output" >&2
					exit 1
				fi
				;;
			*)
				if grep -Eq '^[[:space:]]*(REPLACE|INJECT|TRY_INJECT):' "$building_output"; then
					printf 'Generated exact-path building output must contain plain Vanilla keys: %s\n' "$building_output" >&2
					exit 1
				fi
				;;
		esac
	done
then
	exit 1
fi
python3 tools/validate_cbp_building_injections.py

political_gods_file="packages/cbp_economy_rebalance/in_game/common/gods/hellenism.txt"
stale_political_gods_file="packages/cbp_economy_rebalance/in_game/common/gods/cbp_hellenism.txt"
require_file "$political_gods_file"
if [[ -e "$stale_political_gods_file" ]]; then
	printf '%s\n' \
		'Nested omen registries require an exact-path gods override.' \
		"Remove the runtime-unsafe REPLACE output: $stale_political_gods_file" >&2
	exit 1
fi
if grep -Eq '^[[:space:]]*(REPLACE|INJECT|TRY_INJECT):' "$political_gods_file"; then
	printf 'Exact-path gods output must contain plain Vanilla keys: %s\n' \
		"$political_gods_file" >&2
	exit 1
fi

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

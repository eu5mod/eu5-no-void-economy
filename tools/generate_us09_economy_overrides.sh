#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
local_config="$repo_root/.cbp.local.env"

if [[ -f "$local_config" ]]; then
	set -a
	# shellcheck source=/dev/null
	source "$local_config"
	set +a
fi

# shellcheck source=tools/cbp_goods.sh
source "$repo_root/tools/cbp_goods.sh"

usage() {
	cat <<'EOF_USAGE'
Usage:
  ./tools/generate_us09_economy_overrides.sh <percent> [options]
  ./tools/generate_us09_economy_overrides.sh --percent <percent> [options]

Options:
  --percent N                            Percent increase for building output
  --trade-capacity-percent N             Percent increase for merchant-capacity fields
                                          (default: same as --percent)
  --extra-burgher-promotion-speed N      Extra Burgher promotion speed percent (10 = +10%)
  --extra-laborer-promotion-speed N      Extra Laborer promotion speed percent (10 = +10%)
  --building-maintenance-multiplier N    Non-trade maintenance quantity multiplier (default: 0.7)
  --trade-building-maintenance-multiplier N
                                          Trade-building maintenance quantity multiplier (default: 0.5)
  --minting-income-multiplier N           Minting income multiplier composed into building overrides
                                          (default: MODEU5_US177_MINTING_MULTIPLIER or 2)
  --common-dir PATH                      EU5 `game/in_game/common` source directory
  --package-common-dir PATH              Output `in_game/common` directory for generated files
  --help                                 Show this help text

If no percent is passed and stdin is interactive, the script prompts for one.
Examples:
  ./tools/generate_us09_economy_overrides.sh 5
  ./tools/generate_us09_economy_overrides.sh 10
  ./tools/generate_us09_economy_overrides.sh --percent 7.5
  MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT=15 ./tools/generate_us09_economy_overrides.sh 10
  EXTRA_BURGHER_PROMOTION_SPEED=10 EXTRA_LABORER_PROMOTION_SPEED=10 ./tools/generate_us09_economy_overrides.sh 10

By default, this writes offline probe output under tools/generated/us09_economy_overrides.
Pass --package-common-dir packages/cbp_economy_rebalance/in_game/common only
when regenerating the package overrides. Generated static overrides must keep
the same relative file path as the vanilla source file so EU5 replaces the
vanilla definition instead of loading a second definition with duplicate keys.
EOF_USAGE
}

format_decimal() {
	local value="$1"
	local scale="${2:-10}"

	awk -v value="$value" -v scale="$scale" 'BEGIN {
		printf "%.*f", scale, value
	}' | sed -e 's/0*$//' -e 's/\.$/.0/'
}

source_label() {
	local source_file="$1"
	local relative_source="${source_file#"$common_dir"/}"

	printf '<EU5_GAME_COMMON_DIR>/%s\n' "$relative_source"
}

find_default_common_dir() {
	if [[ -n "${EU5_GAME_COMMON_DIR:-}" && -d "${EU5_GAME_COMMON_DIR:-}" ]]; then
		printf '%s\n' "$EU5_GAME_COMMON_DIR"
		return 0
	fi

	return 1
}

# Vanilla files may carry an UTF-8 BOM. If we copy that byte sequence into a
# generated override after the ModeU5 header, EU5 reads the first key as a
# different BOM-prefixed identifier such as `﻿cannon_maker` or even `﻿`.
# Strip BOMs at source-read boundaries so present and future US-09 generated
# files never leak BOM-prefixed keys into `common/building_types`, prices, or
# pop-type overrides.
strip_utf8_bom_stream() {
	perl -CSD -pe 's/^\x{FEFF}// if $. == 1' "$1"
}

strip_trailing_whitespace_in_place() {
	perl -0pi -e 's/[ \t]+(?=\n)//g; 1 while s/^(\t*) +\t/$1\t/gm' "$1"
}

validate_percent() {
	local label="$1"
	local value="$2"

	if [[ ! "$value" =~ ^-?[0-9]+([.][0-9]+)?$ ]]; then
		printf '%s must be numeric; got %s.\n' "$label" "$value" >&2
		exit 1
	fi

	if ! awk -v value="$value" 'BEGIN { exit !(value > -100) }'; then
		printf '%s must be greater than -100; got %s.\n' "$label" "$value" >&2
		exit 1
	fi
}

validate_nonnegative_number() {
	local label="$1"
	local value="$2"

	if [[ ! "$value" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
		printf '%s must be a non-negative number; got %s.\n' "$label" "$value" >&2
		exit 1
	fi
}

percent=""
trade_capacity_percent="${MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT:-}"
extra_burgher_promotion_speed="${EXTRA_BURGHER_PROMOTION_SPEED:-0}"
extra_laborer_promotion_speed="${EXTRA_LABORER_PROMOTION_SPEED:-0}"
building_maintenance_multiplier="${MODEU5_US08_BUILDING_MAINTENANCE_MULTIPLIER:-0.7}"
trade_building_maintenance_multiplier="${MODEU5_US08_TRADE_BUILDING_MAINTENANCE_MULTIPLIER:-0.5}"
minting_income_multiplier="${MODEU5_US177_MINTING_MULTIPLIER:-2}"
common_dir=""
package_common_dir="$repo_root/tools/generated/us09_economy_overrides/common"

while (($# > 0)); do
	case "$1" in
		--percent)
			percent="$2"
			shift 2
			;;
		--trade-capacity-percent)
			trade_capacity_percent="$2"
			shift 2
			;;
		--extra-burgher-promotion-speed)
			extra_burgher_promotion_speed="$2"
			shift 2
			;;
		--extra-laborer-promotion-speed)
			extra_laborer_promotion_speed="$2"
			shift 2
			;;
		--building-maintenance-multiplier)
			building_maintenance_multiplier="$2"
			shift 2
			;;
		--trade-building-maintenance-multiplier)
			trade_building_maintenance_multiplier="$2"
			shift 2
			;;
		--minting-income-multiplier)
			minting_income_multiplier="$2"
			shift 2
			;;
		--common-dir)
			common_dir="$2"
			shift 2
			;;
		--package-common-dir)
			package_common_dir="$2"
			shift 2
			;;
		--help)
			usage
			exit 0
			;;
		-*)
			printf 'Unknown argument: %s\n\n' "$1" >&2
			usage >&2
			exit 1
			;;
		*)
			if [[ -z "$percent" ]]; then
				percent="$1"
				shift
			else
				printf 'Unexpected extra argument: %s\n\n' "$1" >&2
				usage >&2
				exit 1
			fi
			;;
	esac
done

if [[ -z "$percent" ]]; then
	if [[ -t 0 ]]; then
		read -r -p "US-09 percent increase (5 = 5%, 10 = 10%): " percent
	else
		printf 'Missing percent. Pass one explicitly, for example `./tools/generate_us09_economy_overrides.sh 5`.\n' >&2
		exit 1
	fi
fi

validate_percent "US-09 percent" "$percent"
if [[ -z "$trade_capacity_percent" ]]; then
	trade_capacity_percent="$percent"
fi
validate_percent "MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT" "$trade_capacity_percent"
validate_percent "EXTRA_BURGHER_PROMOTION_SPEED" "$extra_burgher_promotion_speed"
validate_percent "EXTRA_LABORER_PROMOTION_SPEED" "$extra_laborer_promotion_speed"
validate_nonnegative_number "MODEU5_US08_BUILDING_MAINTENANCE_MULTIPLIER" "$building_maintenance_multiplier"
validate_nonnegative_number "MODEU5_US08_TRADE_BUILDING_MAINTENANCE_MULTIPLIER" "$trade_building_maintenance_multiplier"
validate_nonnegative_number "MODEU5_US177_MINTING_MULTIPLIER" "$minting_income_multiplier"

if [[ -z "$common_dir" ]]; then
	if ! common_dir="$(find_default_common_dir)"; then
		printf 'Could not find an EU5 `game/in_game/common` directory. Pass --common-dir or set EU5_GAME_COMMON_DIR.\n' >&2
		exit 1
	fi
fi

building_types_source_dir="$common_dir/building_types"
prices_source_file="$common_dir/prices/00_hardcoded.txt"
pop_types_source_dir="$common_dir/pop_types"
building_types_output_dir="$package_common_dir/building_types"
building_manifest_dir="$(cd "$package_common_dir/../.." && pwd)/cbp_generated/us09_buildings"
prices_output_dir="$package_common_dir/prices"
pop_types_output_dir="$package_common_dir/pop_types"

if [[ ! -d "$building_types_source_dir" ]]; then
	printf 'Missing source directory: %s\n' "$building_types_source_dir" >&2
	exit 1
fi

if [[ ! -f "$prices_source_file" ]]; then
	printf 'Missing source file: %s\n' "$prices_source_file" >&2
	exit 1
fi

if ! awk -v burghers="$extra_burgher_promotion_speed" -v laborers="$extra_laborer_promotion_speed" 'BEGIN { exit !((burghers != 0) || (laborers != 0)) }'; then
	promotion_overrides_enabled=0
else
	promotion_overrides_enabled=1
fi

if [[ "$promotion_overrides_enabled" -eq 1 && ! -d "$pop_types_source_dir" ]]; then
	printf 'Missing source directory: %s\n' "$pop_types_source_dir" >&2
	exit 1
fi

mkdir -p "$building_types_output_dir" "$prices_output_dir"
mkdir -p "$building_manifest_dir"
if [[ "$promotion_overrides_enabled" -eq 1 || -d "$pop_types_output_dir" ]]; then
	mkdir -p "$pop_types_output_dir"
fi

find "$building_types_output_dir" -maxdepth 1 -type f -name 'zzzz_cbp_us09_*.txt' -delete
rm -f \
	"$prices_output_dir/zzzz_cbp_us09_expand_rgo_prices.txt" \
	"$prices_output_dir/expand_rgo_prices.txt"

if [[ -d "$pop_types_output_dir" ]]; then
	while IFS= read -r -d '' generated_file; do
		if head -n 1 "$generated_file" | grep -qx '# Generated by tools/generate_us09_economy_overrides.sh.'; then
			rm -f "$generated_file"
		fi
	done < <(find "$pop_types_output_dir" -maxdepth 1 -type f -name '*.txt' -print0)
fi

output_multiplier="$(awk -v percent="$percent" 'BEGIN { printf "%.12f", 1 + (percent / 100) }')"
trade_capacity_multiplier="$(awk -v percent="$trade_capacity_percent" 'BEGIN { printf "%.12f", 1 + (percent / 100) }')"
rgo_price_multiplier="$(awk -v percent="$percent" 'BEGIN { printf "%.12f", 1 / (1 + (percent / 100)) }')"
burgher_promotion_multiplier="$(awk -v percent="$extra_burgher_promotion_speed" 'BEGIN { printf "%.12f", 1 + (percent / 100) }')"
laborer_promotion_multiplier="$(awk -v percent="$extra_laborer_promotion_speed" 'BEGIN { printf "%.12f", 1 + (percent / 100) }')"
us07_trade_burghers_estate_power_multiplier="0.5"

generated_building_files=0
building_staging_root="$(mktemp -d "${TMPDIR:-/tmp}/cbp-us09-buildings.XXXXXX")"
building_staging_dir="$building_staging_root/building_types"
manifest_staging_dir="$building_staging_root/manifests"
mkdir -p "$building_staging_dir" "$manifest_staging_dir"
trap 'rm -rf "$building_staging_root"' EXIT

while IFS= read -r -d '' source_file; do
	if [[ "$(basename "$source_file")" == "readme.txt" ]]; then
		continue
	fi

	source_basename="$(basename "$source_file")"
	output_file="$building_staging_dir/$source_basename"
	manifest_file="$manifest_staging_dir/${source_basename%.txt}.json"

	set +e
	python3 "$repo_root/tools/transform_cbp_economy_building_overrides.py" \
			--source "$source_file" \
			--source-basename "$source_basename" \
			--source-label "$(source_label "$source_file")" \
			--output "$output_file" \
			--manifest "$manifest_file" \
			--output-multiplier "$output_multiplier" \
			--trade-capacity-multiplier "$trade_capacity_multiplier" \
			--maintenance-multiplier "$building_maintenance_multiplier" \
			--trade-building-maintenance-multiplier "$trade_building_maintenance_multiplier" \
			--us07-trade-burghers-estate-power-multiplier "$us07_trade_burghers_estate_power_multiplier" \
			--minting-income-multiplier "$minting_income_multiplier" \
			--political-modifier-multiplier 0.75 \
			--goods "${cbp_goods[@]}"
	transform_status=$?
	set -e
	if [[ "$transform_status" -eq 3 ]]; then
		continue
	fi
	if [[ "$transform_status" -ne 0 ]]; then
		exit "$transform_status"
	fi

	generated_building_files=$((generated_building_files + 1))
done < <(find "$building_types_source_dir" -maxdepth 1 -type f -name '*.txt' -print0 | sort -z)

# Publish only after every vanilla file has parsed successfully. Existing
# generated overrides remain untouched when analysis fails part-way through.
while IFS= read -r -d '' generated_file; do
	if head -n 1 "$generated_file" | grep -qx '# Generated by tools/generate_us09_economy_overrides.sh.'; then
		rm -f "$generated_file"
	fi
done < <(find "$building_types_output_dir" -maxdepth 1 -type f -name '*.txt' -print0)
find "$building_manifest_dir" -maxdepth 1 -type f -name '*.json' -delete
find "$building_staging_dir" -maxdepth 1 -type f -name '*.txt' -exec cp {} "$building_types_output_dir/" \;
find "$manifest_staging_dir" -maxdepth 1 -type f -name '*.json' -exec cp {} "$building_manifest_dir/" \;

price_keys=(
	expand_rgo_mining
	expand_rgo_farming
	expand_rgo_hunting
	expand_rgo_gathering
	expand_rgo_forestry
)

prices_output_file="$prices_output_dir/00_hardcoded.txt"

{
	printf '%s\n' '# Generated by tools/generate_us09_economy_overrides.sh.'
	printf '%s\n' '# Do not edit manually.'
	printf '# Source: %s\n' "$(source_label "$prices_source_file")"
	printf '# RGO expansion gold multiplier: %s (inverse of 1 + %s%%)\n\n' "$(format_decimal "$rgo_price_multiplier")" "$percent"

	for price_key in "${price_keys[@]}"; do
		source_gold="$(
			strip_utf8_bom_stream "$prices_source_file" | TARGET_PRICE_KEY="$price_key" perl -0ne '
				my $key = $ENV{"TARGET_PRICE_KEY"};
				if (/\b\Q$key\E\s*=\s*\{[^{}]*?\bgold\s*=\s*([0-9]+(?:\.[0-9]+)?)/s) {
					print $1;
					exit 0;
				}
				exit 1;
			'
		)"
		adjusted_gold="$(awk -v gold="$source_gold" -v multiplier="$rgo_price_multiplier" 'BEGIN { printf "%.12f", gold * multiplier }')"

		printf '%s = {\n' "$price_key"
		printf '\tgold = %s\n' "$(format_decimal "$adjusted_gold" 2)"
		printf '}\n\n'
	done
} > "$prices_output_file"
strip_trailing_whitespace_in_place "$prices_output_file"

generated_pop_type_files=0
if [[ "$promotion_overrides_enabled" -eq 1 ]]; then
	python3 - "$pop_types_source_dir" "$pop_types_output_dir" "$extra_burgher_promotion_speed" "$extra_laborer_promotion_speed" <<'PY'
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
import sys

source_dir = Path(sys.argv[1])
output_dir = Path(sys.argv[2])
extra = {
    "burghers": float(sys.argv[3]),
    "laborers": float(sys.argv[4]),
}
multiplier = {key: 1.0 + value / 100.0 for key, value in extra.items()}
requested = {key for key, value in extra.items() if value != 0.0}
seen_targets: set[str] = set()
changed_targets: set[str] = set()
numeric_fields_by_target: dict[str, set[str]] = defaultdict(set)

# EU5 vanilla has changed this field name across builds / documentation. Prefer
# exact known surfaces, but also accept future numeric keys containing
# "promotion" or "promote" inside the selected top-level Pop-type block.
promotion_field_names = {
    "promotion",
    "promote",
    "promotion_speed",
    "promotion_speed_modifier",
    "pop_promotion",
    "pop_promotion_speed",
    "pop_promotion_speed_modifier",
    "local_pop_promotion_speed",
    "local_pop_promotion_speed_modifier",
    "local_pop_promotion_speed_scaled",
    "global_pop_promotion_speed",
    "global_pop_promotion_speed_modifier",
}

target_aliases = {
    "burgher": "burghers",
    "burghers": "burghers",
    "laborer": "laborers",
    "laborers": "laborers",
    "labourer": "laborers",
    "labourers": "laborers",
}

block_start = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{")
numeric_assignment = re.compile(
    r"^(\s*([A-Za-z0-9_]+)\s*=\s*)"
    r"(-?[0-9]+(?:\.[0-9]+)?)(\s*(?:#.*)?)$"
)


def format_decimal(value: float) -> str:
    formatted = f"{value:.10f}".rstrip("0").rstrip(".")
    return formatted if "." in formatted else f"{formatted}.0"


def source_label(path: Path) -> str:
    return f"<EU5_GAME_COMMON_DIR>/pop_types/{path.name}"


def brace_delta(line: str) -> int:
    # EU5 source files used here are declarative; a lightweight brace count is
    # sufficient and mirrors the existing shell/perl generator style.
    return line.count("{") - line.count("}")


def is_promotion_field(key: str) -> bool:
    lowered = key.lower()
    return key in promotion_field_names or "promotion" in lowered or "promote" in lowered


for source_file in sorted(source_dir.glob("*.txt")):
    text = source_file.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    out: list[str] = []
    current_target: str | None = None
    depth = 0
    file_changed = False

    for line in lines:
        match = block_start.match(line)
        if current_target is None and depth == 0 and match:
            current_target = target_aliases.get(match.group(1))
            if current_target in requested:
                seen_targets.add(current_target)

        if current_target in requested:
            assignment = numeric_assignment.match(line)
            if assignment:
                field_name = assignment.group(2)
                numeric_fields_by_target[current_target].add(field_name)
                if is_promotion_field(field_name):
                    old_value = float(assignment.group(3))
                    new_value = old_value * multiplier[current_target]
                    line = f"{assignment.group(1)}{format_decimal(new_value)}{assignment.group(4)}"
                    file_changed = True
                    changed_targets.add(current_target)

        out.append(line)
        depth += brace_delta(line)
        if current_target is not None and depth <= 0:
            current_target = None
            depth = 0

    if file_changed:
        output_file = output_dir / source_file.name
        header = [
            "# Generated by tools/generate_us09_economy_overrides.sh.",
            "# Do not edit manually.",
            f"# Source: {source_label(source_file)}",
        ]
        if "burghers" in requested:
            header.append(
                "# Burgher promotion-speed multiplier: "
                f"{format_decimal(multiplier['burghers'])} (+{format_decimal(extra['burghers'])}%)"
            )
        if "laborers" in requested:
            header.append(
                "# Laborer promotion-speed multiplier: "
                f"{format_decimal(multiplier['laborers'])} (+{format_decimal(extra['laborers'])}%)"
            )
        output_file.write_text("\n".join(header) + "\n\n" + "\n".join(out) + "\n", encoding="utf-8")

missing = requested - changed_targets
if missing:
    missing_list = ", ".join(sorted(missing))
    seen_list = ", ".join(sorted(seen_targets)) or "none"
    accepted_fields = ", ".join(sorted(promotion_field_names))
    detected_fields = "; ".join(
        f"{target}: {', '.join(sorted(numeric_fields_by_target.get(target, set()))) or 'no numeric fields'}"
        for target in sorted(missing)
    )
    raise SystemExit(
        "Could not generate US-09 pop-type promotion overrides for "
        f"{missing_list}; seen target blocks with no recognized numeric promotion field: {seen_list}. "
        f"Accepted exact fields: {accepted_fields}. "
        f"Detected numeric fields in missing target blocks: {detected_fields}."
    )
PY
	generated_pop_type_files="$(find "$pop_types_output_dir" -maxdepth 1 -type f -name '*.txt' -exec sh -c 'head -n 1 "$1" | grep -qx "# Generated by tools/generate_us09_economy_overrides.sh."' sh {} \; -print | wc -l | tr -d ' ')"
	while IFS= read -r -d '' generated_file; do
		strip_trailing_whitespace_in_place "$generated_file"
	done < <(find "$pop_types_output_dir" -maxdepth 1 -type f -name '*.txt' -print0)
fi

bom_scan_dirs=("$building_types_output_dir" "$prices_output_dir")
if [[ -d "$pop_types_output_dir" ]]; then
	bom_scan_dirs+=("$pop_types_output_dir")
fi
if LC_ALL=C grep -RIl $'\xEF\xBB\xBF' "${bom_scan_dirs[@]}" >/dev/null 2>&1; then
	printf '%s\n' 'Generated US-09 files must not contain UTF-8 BOM bytes.' >&2
	exit 1
fi

printf 'Generated %d building override files, 1 RGO expansion price override file, and %d pop-type promotion override files for US-09 (output/RGO %s%%; trade capacity %s%%).\n' \
	"$generated_building_files" "$generated_pop_type_files" "$percent" "$trade_capacity_percent"
printf 'Output directory: %s\n' "$package_common_dir"

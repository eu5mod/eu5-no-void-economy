#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config

source_file="${EU5_GAME_DEFINES_FILE:-}"
output_file="$repo_root/loading_screen/common/defines/00_defines.txt"
check_mode=0
production_efficiency_bonus_per_level="${MODEU5_US15_BONUS_PERCENT:-0.015}"
price_scale_from_eco_base="${MODEU5_PRICE_SCALE_FROM_ECO_BASE:-0}"
goods_rgo_base_cost="${MODEU5_GOODS_RGO_BASE_COST:-1}"
goods_rgo_price_scale="${MODEU5_GOODS_RGO_PRICE_SCALE:-0}"

usage() {
	cat <<'EOF_USAGE'
Usage: bash ./tools/generate_cbp_defines_override.sh [options]

Copies the complete current vanilla 00_defines.txt and patches only the
ModeU5-owned NEconomy keys. This is required because an EU5 mod file named
00_defines.txt replaces the complete vanilla file.

Options:
  --source-file PATH                         Vanilla 00_defines.txt
  --output-file PATH                         Generated complete override
  --production-efficiency-bonus-per-level N  PRODUCTION_EFFIENCY_BONUS_PER_LEVEL
  --price-scale-from-eco-base N              PRICE_SCALE_FROM_ECO_BASE
  --goods-rgo-base-cost N                    GOODS_RGO_BASE_COST
  --goods-rgo-price-scale N                  GOODS_RGO_PRICE_SCALE
  --check                                    Fail if the generated output is absent or stale
  --help                                     Show this help text

Source discovery order:
  1. --source-file
  2. EU5_GAME_DEFINES_FILE
  3. paths derived from EU5_GAME_COMMON_DIR
  4. paths derived from EU5_INSTALL_DIR
EOF_USAGE
}

while (($# > 0)); do
	case "$1" in
		--source-file)
			source_file="$2"
			shift 2
			;;
		--output-file)
			output_file="$2"
			shift 2
			;;
		--production-efficiency-bonus-per-level)
			production_efficiency_bonus_per_level="$2"
			shift 2
			;;
		--price-scale-from-eco-base)
			price_scale_from_eco_base="$2"
			shift 2
			;;
		--goods-rgo-base-cost)
			goods_rgo_base_cost="$2"
			shift 2
			;;
		--goods-rgo-price-scale)
			goods_rgo_price_scale="$2"
			shift 2
			;;
		--check)
			check_mode=1
			shift
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			printf 'Unknown argument: %s\n\n' "$1" >&2
			usage >&2
			exit 2
			;;
	esac
done

resolve_source_file() {
	local common_dir
	local game_root
	local install_root
	local candidate

	if [[ -n "$source_file" ]]; then
		[[ -f "$source_file" ]] && return 0
		printf 'Configured vanilla defines file does not exist: %s\n' "$source_file" >&2
		return 1
	fi

	common_dir="${EU5_GAME_COMMON_DIR:-}"
	common_dir="${common_dir%/}"
	if [[ -n "$common_dir" && "$common_dir" == */in_game/common ]]; then
		game_root="${common_dir%/in_game/common}"
		for candidate in \
			"$game_root/loading_screen/common/defines/00_defines.txt" \
			"${game_root%/game}/loading_screen/common/defines/00_defines.txt"
		do
			if [[ -f "$candidate" ]]; then
				source_file="$candidate"
				return 0
			fi
		done
	fi

	install_root="${EU5_INSTALL_DIR:-}"
	install_root="${install_root%/}"
	if [[ -n "$install_root" ]]; then
		for candidate in \
			"$install_root/game/loading_screen/common/defines/00_defines.txt" \
			"$install_root/loading_screen/common/defines/00_defines.txt"
		do
			if [[ -f "$candidate" ]]; then
				source_file="$candidate"
				return 0
			fi
		done
	fi

	printf '%s\n' 'Could not locate vanilla loading_screen/common/defines/00_defines.txt.' >&2
	printf '%s\n' 'Set EU5_GAME_DEFINES_FILE or pass --source-file explicitly.' >&2
	return 1
}

resolve_source_file

python3 - \
	"$source_file" \
	"$output_file" \
	"$check_mode" \
	"$production_efficiency_bonus_per_level" \
	"$price_scale_from_eco_base" \
	"$goods_rgo_base_cost" \
	"$goods_rgo_price_scale" <<'PY'
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
import os
import re
import sys
import tempfile

source_file = Path(sys.argv[1])
output_file = Path(sys.argv[2])
check_mode = sys.argv[3] == "1"
raw_values = {
    "PRODUCTION_EFFIENCY_BONUS_PER_LEVEL": sys.argv[4],
    "PRICE_SCALE_FROM_ECO_BASE": sys.argv[5],
    "GOODS_RGO_BASE_COST": sys.argv[6],
    "GOODS_RGO_PRICE_SCALE": sys.argv[7],
}

for key, value in raw_values.items():
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise SystemExit(f"{key} must be numeric; got {value!r}.") from exc
    if not parsed.is_finite():
        raise SystemExit(f"{key} must be finite; got {value!r}.")

source_bytes = source_file.read_bytes()
try:
    source_text = source_bytes.decode("utf-8-sig")
except UnicodeDecodeError as exc:
    raise SystemExit(f"Vanilla defines file is not UTF-8: {source_file}") from exc

lines = source_text.splitlines(keepends=True)
counts = {key: 0 for key in raw_values}

for index, line in enumerate(lines):
    for key, replacement in raw_values.items():
        pattern = re.compile(
            rf"^([ \t]*{re.escape(key)}[ \t]*=[ \t]*)"
            rf"([^ \t\r\n#]+)([ \t]*(?:#.*)?)(\r?\n)?$"
        )
        match = pattern.match(line)
        if not match:
            continue
        counts[key] += 1
        newline = match.group(4) or ""
        lines[index] = f"{match.group(1)}{replacement}{match.group(3)}{newline}"

invalid_counts = {key: count for key, count in counts.items() if count != 1}
if invalid_counts:
    details = ", ".join(f"{key}={count}" for key, count in invalid_counts.items())
    raise SystemExit(
        "Refusing to generate a partial or ambiguous 00_defines.txt; "
        f"each target must occur exactly once ({details})."
    )

source_digest = sha256(source_bytes).hexdigest()
header_lines = [
    "# Generated by tools/generate_cbp_defines_override.sh.",
    "# Do not edit manually; this is a complete copy of the current vanilla 00_defines.txt.",
    "# Source: <EU5_GAME_DEFINES_FILE>",
    f"# Source SHA-256: {source_digest}",
]
header_lines.extend(f"# Override: {key} = {value}" for key, value in raw_values.items())
expected_text = "\n".join(header_lines) + "\n\n" + "".join(lines)
expected_bytes = expected_text.encode("utf-8")

if expected_bytes.startswith(b"\xef\xbb\xbf"):
    raise SystemExit("Generated defines override must not contain a UTF-8 BOM.")

if check_mode:
    if not output_file.is_file():
        raise SystemExit(f"Generated defines override is missing: {output_file}")
    if output_file.read_bytes() != expected_bytes:
        raise SystemExit(
            "Generated defines override is stale. Run "
            "bash ./tools/generate_cbp_defines_override.sh."
        )
    print(f"ModeU5 complete defines override is current: {output_file}")
    raise SystemExit(0)

output_file.parent.mkdir(parents=True, exist_ok=True)
fd, temporary_name = tempfile.mkstemp(prefix=f".{output_file.name}.", dir=output_file.parent)
try:
    with os.fdopen(fd, "wb") as temporary_file:
        temporary_file.write(expected_bytes)
    os.replace(temporary_name, output_file)
finally:
    if os.path.exists(temporary_name):
        os.unlink(temporary_name)

print(f"Generated complete ModeU5 defines override: {output_file}")
print(f"Vanilla source SHA-256: {source_digest}")
PY

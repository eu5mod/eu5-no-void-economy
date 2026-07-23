#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo_root"
# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"

if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR before running focused CBG building parity.' >&2
	exit 1
fi

game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
bonus="${MODEU5_US09_BONUS_PERCENT:-5}"
trade_bonus="${MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT:-15}"
maintenance="${MODEU5_US08_BUILDING_MAINTENANCE_MULTIPLIER:-0.7}"
trade_maintenance="${MODEU5_US08_TRADE_BUILDING_MAINTENANCE_MULTIPLIER:-0.5}"
minting="${MODEU5_US177_MINTING_MULTIPLIER:-2}"
output_multiplier="$(awk -v value="$bonus" 'BEGIN { printf "%.12f", 1 + value / 100 }')"
trade_multiplier="$(awk -v value="$trade_bonus" 'BEGIN { printf "%.12f", 1 + value / 100 }')"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-buildings.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$work_dir/reference/in_game/common"

./tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh \
	--percent "$bonus" \
	--rgo-price-percent "${MODEU5_US09_RGO_PRICE_OFFSET_PERCENT:-8}" \
	--trade-capacity-percent "$trade_bonus" \
	--extra-burgher-promotion-speed "${EXTRA_BURGHER_PROMOTION_SPEED:-10}" \
	--extra-laborer-promotion-speed "${EXTRA_LABORER_PROMOTION_SPEED:-10}" \
	--building-maintenance-multiplier "$maintenance" \
	--trade-building-maintenance-multiplier "$trade_maintenance" \
	--minting-income-multiplier "$minting" \
	--common-dir "$EU5_GAME_COMMON_DIR" \
	--package-common-dir "$work_dir/reference/in_game/common" \
	--skip-rgo-prices --skip-pop-promotions >/dev/null
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_building_spec.py \
	--game-root "$game_root" --output "$work_dir/buildings.json" \
	--output-multiplier "$output_multiplier" \
	--trade-capacity-multiplier "$trade_multiplier" \
	--maintenance-multiplier "$maintenance" \
	--trade-maintenance-multiplier "$trade_maintenance" \
	--minting-multiplier "$minting" >/dev/null
python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/buildings.json" \
	--output-root "$work_dir/candidate" \
	--manifest "$work_dir/candidate/manifest.json" >/dev/null

python3 - "$work_dir" <<'PY'
from decimal import Decimal
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
reference = root / "reference/in_game/common/building_types"
candidate = root / "candidate/in_game/common/building_types"
expected = sorted(path.name for path in reference.glob("*.txt"))
actual = sorted(path.name for path in candidate.glob("*.txt"))
if actual != expected:
    raise SystemExit(f"Building CBG scope mismatch: expected={expected!r}, actual={actual!r}")
foreign_header = re.compile(
    rb"^# Foreign-building merchant capacity multiplier: 2\.0\r?\n", re.MULTILINE
)
foreign_value = re.compile(
    rb"^(\s*merchant_capacity_from_building\s*=\s*)([-0-9.]+) "
    rb"# FOREIGN BUILDING x2\.0; (.*)$",
    re.MULTILINE,
)


def format_decimal(value: Decimal) -> bytes:
    rendered = format(value.normalize(), "f")
    if "." not in rendered:
        rendered += ".0"
    return rendered.encode()


def normalize_pr193_extension(content: bytes) -> bytes:
    content, header_count = foreign_header.subn(b"", content)
    if header_count != 1:
        raise SystemExit(f"Expected one PR #193 header, found {header_count}")

    def restore_global_value(match: re.Match[bytes]) -> bytes:
        value = Decimal(match.group(2).decode()) / Decimal("2")
        return match.group(1) + format_decimal(value) + b" # " + match.group(3)

    return foreign_value.sub(restore_global_value, content)


for name in expected:
    normalized = normalize_pr193_extension((candidate / name).read_bytes())
    if (reference / name).read_bytes() != normalized:
        raise SystemExit(f"Building CBG byte parity failed: {name}")
print(f"CBP/CBG building parity passed: {len(expected)} byte-identical output files.")
PY

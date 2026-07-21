#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo_root"
# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"
if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR before running CBG RGO-price parity.' >&2
	exit 1
fi
game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
percent="${MODEU5_US09_BONUS_PERCENT:-5}"
rgo_price_percent="${MODEU5_US09_RGO_PRICE_OFFSET_PERCENT:-8}"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-rgo.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$work_dir/reference/in_game/common"

./tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh "$percent" \
	--rgo-price-percent "$rgo_price_percent" \
	--trade-capacity-percent "${MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT:-15}" \
	--extra-burgher-promotion-speed "${EXTRA_BURGHER_PROMOTION_SPEED:-10}" \
	--extra-laborer-promotion-speed "${EXTRA_LABORER_PROMOTION_SPEED:-10}" \
	--common-dir "$EU5_GAME_COMMON_DIR" --package-common-dir "$work_dir/reference/in_game/common" >/dev/null
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_rgo_prices_spec.py \
	--game-root "$game_root" --adapter offset --percent "$rgo_price_percent" --output "$work_dir/rgo.json"
python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/rgo.json" \
	--output-root "$work_dir/candidate" --manifest "$work_dir/candidate/manifest.json"

target="in_game/common/prices/00_hardcoded.txt"
if ! cmp -s "$work_dir/reference/$target" "$work_dir/candidate/$target"; then
	diff -u "$work_dir/reference/$target" "$work_dir/candidate/$target" || true
	exit 1
fi
printf '%s\n' 'CBP/CBG percentage-offset RGO-price parity passed: partial override is byte-identical.'

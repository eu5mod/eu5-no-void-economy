#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
local_config="$repo_root/.modeu5.local.env"

if [[ -f "$local_config" ]]; then
	set -a
	# shellcheck source=/dev/null
	source "$local_config"
	set +a
fi

"$repo_root/tools/generate_stock_good_helpers.sh"
python3 "$repo_root/tools/postprocess_perf14_promotion_guards.py" "$repo_root/in_game/common/scripted_effects/modeu5_stock_goods_generated.txt"
"$repo_root/tools/generate_good_transport_helpers.sh"

if [[ "${MODEU5_ENABLE_UNVERIFIED_US09_STATIC_OVERRIDES:-0}" == "1" && -x "$repo_root/tools/generate_us09_economy_overrides.sh" && -n "${EU5_GAME_COMMON_DIR:-}" ]]; then
	"$repo_root/tools/generate_us09_economy_overrides.sh" "${MODEU5_US09_BONUS_PERCENT:-5}"
elif [[ -x "$repo_root/tools/generate_us09_economy_overrides.sh" && -n "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf 'Skipping loaded US-09 static override regeneration; duplicate-key override loading is not confirmed. Set MODEU5_ENABLE_UNVERIFIED_US09_STATIC_OVERRIDES=1 only for local probes.\n'
elif [[ -x "$repo_root/tools/generate_us09_economy_overrides.sh" ]]; then
	printf 'Skipping US-09 static override regeneration; set EU5_GAME_COMMON_DIR to vanilla game/in_game/common to regenerate it.\n'
fi

#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=tools/modeu5_tool_lib.sh
source "$repo_root/tools/modeu5_tool_lib.sh"
modeu5_load_local_config

bash "$repo_root/tools/generate_local_runtime_config.sh"
"$repo_root/tools/generate_stock_good_helpers.sh"
python3 "$repo_root/tools/postprocess_perf14_promotion_guards.py" "$repo_root/in_game/common/scripted_effects/modeu5_stock_goods_generated.txt"
bash "$repo_root/tools/generate_pr71_active_good_dispatch_helpers.sh"
"$repo_root/tools/generate_good_transport_helpers.sh"
bash "$repo_root/tools/generate_us10_ui_helpers.sh"

if [[ -x "$repo_root/tools/generate_us09_economy_overrides.sh" ]]; then
	if [[ "${MODEU5_ENABLE_US09_STATIC_OVERRIDES:-true}" == "false" || "${MODEU5_ENABLE_US09_STATIC_OVERRIDES:-true}" == "0" ]]; then
		printf '%s\n' 'Skipping US-09 static file generation; MODEU5_ENABLE_US09_STATIC_OVERRIDES=false.'
	elif [[ -n "${EU5_GAME_COMMON_DIR:-}" ]]; then
		bash "$repo_root/tools/generate_us09_economy_overrides.sh" "${MODEU5_US09_BONUS_PERCENT:-5}" --package-common-dir "$repo_root/packages/modeu5_economy_rebalance/in_game/common"
	else
		printf '%s\n' 'Skipping US-09 static file generation; set EU5_GAME_COMMON_DIR to vanilla game/in_game/common.'
	fi
fi

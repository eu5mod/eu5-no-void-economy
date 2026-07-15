#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"

game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
source_file="${EU5_GAME_LOCATION_STATIC_MODIFIERS_FILE:-$game_root/main_menu/common/static_modifiers/location.txt}"
if [[ -z "${EU5_GAME_COMMON_DIR:-}" || ! -f "$source_file" ]]; then
	printf '%s\n' 'Configure a valid Vanilla location.txt before running CBG location parity.' >&2
	exit 1
fi
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-location.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

./tools/generate_cbp_location_overrides.sh \
	--source-file "$source_file" --output-file "$work_dir/reference/cbp_location.txt"
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_location_spec.py --output "$work_dir/location.json"
python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/location.json" \
	--output-root "$work_dir/candidate" --manifest "$work_dir/candidate/manifest.json"

candidate="$work_dir/candidate/main_menu/common/static_modifiers/cbp_location.txt"
if ! cmp -s "$work_dir/reference/cbp_location.txt" "$candidate"; then
	diff -u "$work_dir/reference/cbp_location.txt" "$candidate" || true
	exit 1
fi
printf '%s\n' 'CBP/CBG location parity passed: dedicated output is byte-identical.'

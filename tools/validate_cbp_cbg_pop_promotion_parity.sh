#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"
if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR before running CBG Pop-promotion parity.' >&2
	exit 1
fi
game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
percent="${MODEU5_US09_BONUS_PERCENT:-5}"
burgher="${EXTRA_BURGHER_PROMOTION_SPEED:-10}"
laborer="${EXTRA_LABORER_PROMOTION_SPEED:-10}"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-pop.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$work_dir/reference/in_game/common"

./tools/generate_us09_economy_overrides.sh "$percent" \
	--trade-capacity-percent "${MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT:-15}" \
	--extra-burgher-promotion-speed "$burgher" --extra-laborer-promotion-speed "$laborer" \
	--common-dir "$EU5_GAME_COMMON_DIR" --package-common-dir "$work_dir/reference/in_game/common" >/dev/null
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_pop_promotion_spec.py \
	--game-root "$game_root" --burgher-percent "$burgher" --laborer-percent "$laborer" \
	--output "$work_dir/pop.json"
python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/pop.json" \
	--output-root "$work_dir/candidate" --manifest "$work_dir/candidate/manifest.json"

python3 - "$work_dir" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
manifest = json.loads((root / "candidate/manifest.json").read_text())
for entry in manifest["files"]:
    relative = Path(entry["path"])
    if (root / "reference" / relative).read_bytes() != (root / "candidate" / relative).read_bytes():
        raise SystemExit(f"Pop-promotion CBG byte parity failed: {relative}")
print(f"CBP/CBG Pop-promotion parity passed: {len(manifest['files'])} byte-identical output file(s).")
PY

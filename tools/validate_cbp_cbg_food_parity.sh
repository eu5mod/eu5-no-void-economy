#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"

if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR before running focused CBG food parity.' >&2
	exit 1
fi

game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
divisor="${MODEU5_US177_FOOD_PRODUCTION_DIVISOR:-3}"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-food.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

python3 tools/generate_us177_food_goods_manifest.py \
	--game-root "$game_root" --package-root "$work_dir/reference" \
	--food-price "${MODEU5_US177_FOOD_PRICE:-0.3}" \
	--food-production-divisor "$divisor"
python3 tools/generate_cbp_cbg_food_spec.py \
	--game-root "$game_root" --divisor "$divisor" --output "$work_dir/food.json"
python3 tools/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/food.json" \
	--output-root "$work_dir/candidate" --manifest "$work_dir/candidate/manifest.json"

python3 - "$work_dir/reference/cbp_generated/us177_food_goods_manifest.json" "$work_dir" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
root = Path(sys.argv[2])
expected = sorted(item["path"] for item in manifest["generated_food_overrides"])
candidate_manifest = json.loads((root / "candidate/manifest.json").read_text(encoding="utf-8"))
actual = sorted(item["path"] for item in candidate_manifest["files"])
if actual != expected:
    raise SystemExit(f"Food CBG scope mismatch: expected={expected!r}, actual={actual!r}")
for relative in expected:
    reference = (root / "reference" / relative).read_bytes()
    candidate = (root / "candidate" / relative).read_bytes()
    if reference != candidate:
        raise SystemExit(f"Food CBG byte parity failed: {relative}")
print(f"CBP/CBG food parity passed: {len(expected)} byte-identical output file(s).")
PY

#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"
if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR before running political/minting CBG parity.' >&2
	exit 1
fi
game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
multiplier="${MODEU5_US177_MINTING_MULTIPLIER:-2}"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-political.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

python3 tools/generate_us177_minting_overrides.py \
	--game-root "$game_root" --package-root "$work_dir/reference" \
	--multiplier "$multiplier" >/dev/null
python3 tools/generate_political_reward_overrides.py \
	--game-root "$game_root" --package-root "$work_dir/reference" \
	--skip-central-default-values >/dev/null
python3 tools/generate_cbp_cbg_political_minting_spec.py \
	--game-root "$game_root" --minting-multiplier "$multiplier" \
	--output "$work_dir/spec.json" >/dev/null
python3 tools/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/spec.json" \
	--output-root "$work_dir/candidate" \
	--manifest "$work_dir/candidate/manifest.json" >/dev/null
python3 - "$work_dir" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
spec = json.loads((root / "spec.json").read_text())
paths = spec["scope_contract"]["owned_outputs"]
for relative in paths:
    if (root / "reference" / relative).read_bytes() != (root / "candidate" / relative).read_bytes():
        raise SystemExit(f"Political/minting CBG byte parity failed: {relative}")
print(f"CBP/CBG political/minting parity passed: {len(paths)} byte-identical output files.")
PY

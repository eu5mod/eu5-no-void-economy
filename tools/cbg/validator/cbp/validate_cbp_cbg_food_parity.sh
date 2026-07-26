#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
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
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_food_spec.py \
	--game-root "$game_root" --divisor "$divisor" --output "$work_dir/food.json"
python3 tools/cbg/cbp_community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/food.json" \
	--output-root "$work_dir/candidate" --manifest "$work_dir/candidate/manifest.json"

python3 - "$work_dir/reference/cbp_generated/us177_food_goods_manifest.json" "$work_dir" <<'PY'
import json
import re
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
root = Path(sys.argv[2])
reference_paths = sorted(item["path"] for item in manifest["generated_food_overrides"])
expected = sorted(
    (Path(path).parent / f"cbp_{Path(path).name}").as_posix()
    for path in reference_paths
)
candidate_manifest = json.loads((root / "candidate/manifest.json").read_text(encoding="utf-8"))
actual = sorted(item["path"] for item in candidate_manifest["files"])
if actual != expected:
    raise SystemExit(f"Food CBG scope mismatch: expected={expected!r}, actual={actual!r}")
sys.path.insert(0, str(Path.cwd()))
from tools.cbg.community_balance_generator import scan_objects


def blocks(content: bytes, *, strip_replace: bool) -> dict[str, bytes]:
    if strip_replace:
        content = re.sub(
            rb"^(?P<indent>[ \t]*)REPLACE:",
            rb"\g<indent>",
            content,
            flags=re.MULTILINE,
        )
    lines = content.decode("utf-8-sig").splitlines()

    def normalized_block(start: int, end: int) -> bytes:
        block = [line.rstrip() for line in lines[start : end + 1]]
        while block and not block[-1]:
            block.pop()
        return "\n".join(block).encode()

    return {
        obj.path[0]: normalized_block(obj.start, obj.end)
        for obj in scan_objects(lines)
        if len(obj.path) == 1
    }


objects = 0
for reference_relative, candidate_relative in zip(reference_paths, expected):
    reference_blocks = blocks(
        (root / "reference" / reference_relative).read_bytes(),
        strip_replace=False,
    )
    candidate_blocks = blocks(
        (root / "candidate" / candidate_relative).read_bytes(),
        strip_replace=True,
    )
    for name, body in candidate_blocks.items():
        if reference_blocks.get(name) != body:
            raise SystemExit(f"Food CBG object parity failed: {name}")
        objects += 1
print(f"CBP/CBG food parity passed: {len(expected)} file(s), {objects} REPLACE goods.")
PY

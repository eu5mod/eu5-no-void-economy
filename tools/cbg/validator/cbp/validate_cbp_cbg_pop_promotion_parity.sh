#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
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

./tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh "$percent" \
	--rgo-price-percent "${MODEU5_US09_RGO_PRICE_OFFSET_PERCENT:-8}" \
	--trade-capacity-percent "${MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT:-15}" \
	--extra-burgher-promotion-speed "$burgher" --extra-laborer-promotion-speed "$laborer" \
	--common-dir "$EU5_GAME_COMMON_DIR" --package-common-dir "$work_dir/reference/in_game/common" >/dev/null
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_pop_promotion_spec.py \
	--game-root "$game_root" --burgher-percent "$burgher" --laborer-percent "$laborer" \
	--output "$work_dir/pop.json"
python3 tools/cbg/cbp_community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/pop.json" \
	--output-root "$work_dir/candidate" --manifest "$work_dir/candidate/manifest.json"

python3 - "$work_dir" <<'PY'
import json
import re
import sys
from pathlib import Path
root = Path(sys.argv[1])
manifest = json.loads((root / "candidate/manifest.json").read_text())
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
for entry in manifest["files"]:
    relative = Path(entry["path"])
    if not relative.name.startswith("cbp_"):
        raise SystemExit(f"Pop-promotion output is not CBP-prefixed: {relative}")
    reference_relative = relative.parent / relative.name.removeprefix("cbp_")
    reference_blocks = blocks(
        (root / "reference" / reference_relative).read_bytes(),
        strip_replace=False,
    )
    candidate_blocks = blocks(
        (root / "candidate" / relative).read_bytes(),
        strip_replace=True,
    )
    for name, body in candidate_blocks.items():
        if reference_blocks.get(name) != body:
            raise SystemExit(f"Pop-promotion CBG object parity failed: {name}")
        objects += 1
print(
    f"CBP/CBG Pop-promotion parity passed: "
    f"{len(manifest['files'])} file(s), {objects} REPLACE Pop objects."
)
PY

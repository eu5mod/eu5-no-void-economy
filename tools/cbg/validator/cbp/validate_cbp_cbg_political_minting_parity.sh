#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
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
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_political_minting_spec.py \
	--game-root "$game_root" --minting-multiplier "$multiplier" \
	--output "$work_dir/spec.json" >/dev/null
python3 tools/cbg/cbp_community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/spec.json" \
	--output-root "$work_dir/candidate" \
	--manifest "$work_dir/candidate/manifest.json" >/dev/null
python3 - "$work_dir" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
spec = json.loads((root / "spec.json").read_text())
paths = spec["scope_contract"]["owned_outputs"]
sys.path.insert(0, str(Path.cwd()))
from tools.cbg.community_balance_generator import scan_objects


def object_blocks(content: bytes, *, strip_replace: bool) -> dict[str, bytes]:
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


objects_checked = 0
for relative in paths:
    candidate = root / "candidate" / relative
    if "/common/" not in f"/{relative}":
        if (root / "reference" / relative).read_bytes() != candidate.read_bytes():
            raise SystemExit(f"Political/minting event byte parity failed: {relative}")
        continue

    path = Path(relative)
    if not path.name.startswith("cbp_"):
        raise SystemExit(f"Common database output is not CBP-prefixed: {relative}")
    source_relative = path.parent / path.name.removeprefix("cbp_")
    reference = root / "reference" / source_relative
    reference_objects = object_blocks(reference.read_bytes(), strip_replace=False)
    candidate_content = candidate.read_bytes()
    candidate_objects = object_blocks(candidate_content, strip_replace=True)
    replace_entries = set(
        match.decode()
        for match in re.findall(
            rb"^[ \t]*REPLACE:([A-Za-z0-9_.:-]+)[ \t]*=",
            candidate_content,
            re.MULTILINE,
        )
    )
    if replace_entries != set(candidate_objects):
        raise SystemExit(f"Political/minting REPLACE scope mismatch: {relative}")
    for object_name, body in candidate_objects.items():
        if reference_objects.get(object_name) != body:
            raise SystemExit(
                f"Political/minting object parity failed: "
                f"{source_relative}:{object_name}"
            )
        objects_checked += 1

print(
    f"CBP/CBG political/minting parity passed: {len(paths)} files, "
    f"{objects_checked} common-database REPLACE objects."
)
PY

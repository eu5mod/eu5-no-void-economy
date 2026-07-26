#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo_root"
# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"

if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR before running focused CBG building parity.' >&2
	exit 1
fi

game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
bonus="${MODEU5_US09_BONUS_PERCENT:-5}"
trade_bonus="${MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT:-15}"
maintenance="${MODEU5_US08_BUILDING_MAINTENANCE_MULTIPLIER:-0.7}"
trade_maintenance="${MODEU5_US08_TRADE_BUILDING_MAINTENANCE_MULTIPLIER:-0.5}"
minting="${MODEU5_US177_MINTING_MULTIPLIER:-2}"
generation_mode="${MODEU5_BUILDING_GENERATION_MODE:-override}"
output_multiplier="$(awk -v value="$bonus" 'BEGIN { printf "%.12f", 1 + value / 100 }')"
trade_multiplier="$(awk -v value="$trade_bonus" 'BEGIN { printf "%.12f", 1 + value / 100 }')"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-buildings.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_building_spec.py \
	--game-root "$game_root" --output "$work_dir/buildings.json" \
	--generation-mode "$generation_mode" \
	--output-multiplier "$output_multiplier" \
	--trade-capacity-multiplier "$trade_multiplier" \
	--maintenance-multiplier "$maintenance" \
	--trade-maintenance-multiplier "$trade_maintenance" \
	--minting-multiplier "$minting" >/dev/null
python3 tools/cbg/cbp_community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/buildings.json" \
	--output-root "$work_dir/candidate" \
	--manifest "$work_dir/candidate/cbp_generated/cbg_building_manifest.json" >/dev/null
python3 tools/validate_us08_building_maintenance_overrides.py \
	--common-dir "$EU5_GAME_COMMON_DIR" \
	--package-common-dir "$work_dir/candidate/in_game/common" \
	--generation-mode "$generation_mode" \
	--us09-percent "$bonus" \
	--trade-capacity-percent "$trade_bonus" \
	--maintenance-multiplier "$maintenance" \
	--trade-building-maintenance-multiplier "$trade_maintenance" \
	--foreign-trade-capacity-multiplier 2 \
	--minting-multiplier "$minting" >/dev/null

python3 - "$work_dir" "$EU5_GAME_COMMON_DIR" "$bonus" "$generation_mode" <<'PY'
import json
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
vanilla = Path(sys.argv[2]) / "building_types"
bonus = float(sys.argv[3])
generation_mode = sys.argv[4]
candidate = root / "candidate/in_game/common/building_types"
actual_files = sorted(path.name for path in candidate.glob("*.txt"))
manifest = json.loads(
    (root / "candidate/cbp_generated/cbg_building_manifest.json").read_text()
)
entry_modes = {
    entry["path"]: entry.get("database_entry_mode")
    for entry in manifest.get("files", [])
    if entry["path"].startswith("in_game/common/building_types/")
}
unknown_modes = sorted(
    f"{path}:{mode}"
    for path, mode in entry_modes.items()
    if mode not in {None, "INJECT"}
)
if unknown_modes:
    raise SystemExit(f"Unsupported building database-entry modes: {unknown_modes!r}")
exact_files = sorted(
    Path(path).name for path, mode in entry_modes.items() if mode is None
)
inject_files = sorted(
    Path(path).name for path, mode in entry_modes.items() if mode == "INJECT"
)
if generation_mode == "override":
    if not exact_files or inject_files:
        raise SystemExit(
            "Override building generation must emit exact-path outputs only"
        )
elif generation_mode == "compatibility":
    if not exact_files or not inject_files:
        raise SystemExit(
            "Compatibility building generation must exercise exact-path and "
            "INJECT outputs"
        )
else:
    raise SystemExit(f"Unsupported building generation mode: {generation_mode}")
if sorted((*exact_files, *inject_files)) != actual_files:
    raise SystemExit(
        f"Building CBG manifest/output mismatch: manifest="
        f"{sorted((*exact_files, *inject_files))!r}, actual={actual_files!r}"
    )

for name in exact_files:
    content = (candidate / name).read_text(encoding="utf-8-sig")
    if re.search(r"^(?:REPLACE|INJECT|TRY_INJECT):", content, re.MULTILINE):
        raise SystemExit(
            f"Exact-path building output must use plain Vanilla keys: {name}"
        )

sys.path.insert(0, str(Path.cwd()))
from tools.transform_cbp_economy_building_overrides import (
    ASSIGNMENT,
    find_named_blocks,
)

expected_methods = 0
if generation_mode == "compatibility" and bonus != 0:
    for path in vanilla.glob("*.txt"):
        if path.name == "readme.txt":
            continue
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        blocks = find_named_blocks(lines)
        for index, line in enumerate(lines):
            match = ASSIGNMENT.match(line)
            if match is None or match.group(2) != "output":
                continue
            ancestors = sorted(
                (block for block in blocks if block.start <= index <= block.end),
                key=lambda block: block.depth,
            )
            if len(ancestors) < 3 or ancestors[-2].key != "unique_production_methods":
                raise SystemExit(
                    f"Vanilla output is outside unique production methods: "
                    f"{path.name}:{index + 1}"
                )
            expected_methods += 1

generated_methods: list[str] = []
for name in inject_files:
    content = (candidate / name).read_text(encoding="utf-8-sig")
    generated_methods.extend(
        re.findall(
            r"^\s*(cbp_us09_[A-Za-z0-9_]+)\s*=\s*\{",
            content,
            re.MULTILINE,
        )
    )
if len(generated_methods) != expected_methods:
    raise SystemExit(
        "Prefixed production-method coverage mismatch: "
        f"expected={expected_methods}, generated={len(generated_methods)}"
    )
if len(set(generated_methods)) != len(generated_methods):
    raise SystemExit("Generated cbp_us09_ production-method names are not unique")

vanilla_method_names = {
    method.removeprefix("cbp_us09_") for method in generated_methods
}
expected_unlocks: list[str] = []
unlock_pattern = re.compile(
    r"^\s*unlock_production_method\s*=\s*([A-Za-z0-9_.:-]+)",
    re.MULTILINE,
)
if generation_mode == "compatibility":
    for path in (Path(sys.argv[2]) / "advances").glob("*.txt"):
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            match = unlock_pattern.match(line.split("#", 1)[0])
            if match and match.group(1) in vanilla_method_names:
                expected_unlocks.append(f"cbp_us09_{match.group(1)}")
actual_unlocks: list[str] = []
advance_output = root / "candidate/in_game/common/advances"
for path in advance_output.glob("cbp_inject_us09_*.txt"):
    actual_unlocks.extend(unlock_pattern.findall(path.read_text(encoding="utf-8-sig")))
if sorted(actual_unlocks) != sorted(expected_unlocks):
    raise SystemExit(
        "Production-method unlock parity mismatch: "
        f"expected={sorted(expected_unlocks)!r}, generated={sorted(actual_unlocks)!r}"
    )

for name in exact_files:
    if name.startswith("cbp_"):
        raise SystemExit(f"Structural output must retain its Vanilla basename: {name}")

print(
    f"CBP/CBG {generation_mode} building contract passed: "
    f"{len(exact_files)} exact-path files, {len(inject_files)} INJECT files, "
    f"{len(generated_methods)} prefixed production-method alternatives, "
    f"{len(actual_unlocks)} Vanilla unlocks mirrored."
)
PY

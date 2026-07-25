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
output_multiplier="$(awk -v value="$bonus" 'BEGIN { printf "%.12f", 1 + value / 100 }')"
trade_multiplier="$(awk -v value="$trade_bonus" 'BEGIN { printf "%.12f", 1 + value / 100 }')"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-buildings.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$work_dir/reference/in_game/common"

./tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh \
	--percent "$bonus" \
	--rgo-price-percent "${MODEU5_US09_RGO_PRICE_OFFSET_PERCENT:-8}" \
	--trade-capacity-percent "$trade_bonus" \
	--extra-burgher-promotion-speed "${EXTRA_BURGHER_PROMOTION_SPEED:-10}" \
	--extra-laborer-promotion-speed "${EXTRA_LABORER_PROMOTION_SPEED:-10}" \
	--building-maintenance-multiplier "$maintenance" \
	--trade-building-maintenance-multiplier "$trade_maintenance" \
	--minting-income-multiplier "$minting" \
	--common-dir "$EU5_GAME_COMMON_DIR" \
	--package-common-dir "$work_dir/reference/in_game/common" \
	--skip-rgo-prices --skip-pop-promotions >/dev/null
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_building_spec.py \
	--game-root "$game_root" --output "$work_dir/buildings.json" \
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
	--us09-percent "$bonus" \
	--trade-capacity-percent "$trade_bonus" \
	--maintenance-multiplier "$maintenance" \
	--trade-building-maintenance-multiplier "$trade_maintenance" \
	--foreign-trade-capacity-multiplier 2 \
	--minting-multiplier "$minting" >/dev/null

python3 - "$work_dir" <<'PY'
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
reference = root / "reference/in_game/common/building_types"
candidate = root / "candidate/in_game/common/building_types"
expected_files = sorted(path.name for path in reference.glob("*.txt"))
actual_files = sorted(path.name for path in candidate.glob("*.txt"))
manifest = json.loads(
    (root / "candidate/cbp_generated/cbg_building_manifest.json").read_text()
)
entry_modes = {
    entry["path"]: entry.get("database_entry_mode")
    for entry in manifest.get("files", [])
}
unknown_modes = sorted(
    f"{path}:{mode}"
    for path, mode in entry_modes.items()
    if mode not in {"REPLACE", "INJECT"}
)
if unknown_modes:
    raise SystemExit(f"Unsupported building database-entry modes: {unknown_modes!r}")
replace_files = sorted(
    Path(path).name for path, mode in entry_modes.items() if mode == "REPLACE"
)
inject_files = sorted(
    Path(path).name for path, mode in entry_modes.items() if mode == "INJECT"
)
if not replace_files or not inject_files:
    raise SystemExit(
        "Hybrid building generation must exercise both REPLACE and INJECT outputs"
    )
if sorted((*replace_files, *inject_files)) != actual_files:
    raise SystemExit(
        f"Building CBG manifest/output mismatch: manifest="
        f"{sorted((*replace_files, *inject_files))!r}, actual={actual_files!r}"
    )

foreign_header = re.compile(
    rb"^# Foreign-building merchant capacity multiplier: 2\.0\r?\n", re.MULTILINE
)
foreign_value = re.compile(
    rb"^(\s*merchant_capacity_from_building\s*=\s*)([-0-9.]+) "
    rb"# FOREIGN BUILDING x2\.0; (.*)$",
    re.MULTILINE,
)


def format_decimal(value: Decimal) -> bytes:
    rendered = format(value.normalize(), "f")
    if "." not in rendered:
        rendered += ".0"
    return rendered.encode()


def normalize_pr193_extension(content: bytes) -> bytes:
    content, header_count = foreign_header.subn(b"", content)
    if header_count != 1:
        raise SystemExit(f"Expected one foreign-building header, found {header_count}")

    def restore_global_value(match: re.Match[bytes]) -> bytes:
        value = Decimal(match.group(2).decode()) / Decimal("2")
        return match.group(1) + format_decimal(value) + b" # " + match.group(3)

    return foreign_value.sub(restore_global_value, content)


def object_blocks(content: bytes, *, strip_replace: bool) -> dict[str, bytes]:
    if strip_replace:
        content = re.sub(
            rb"^(?P<indent>[ \t]*)REPLACE:",
            rb"\g<indent>",
            content,
            flags=re.MULTILINE,
        )
    lines = content.decode("utf-8-sig").splitlines()
    sys.path.insert(0, str(Path.cwd()))
    from tools.cbg.community_balance_generator import scan_objects

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
for generated_name in replace_files:
    name = generated_name.removeprefix("cbp_")
    if name not in expected_files:
        raise SystemExit(f"Missing legacy reference file for {generated_name}")
    candidate_content = normalize_pr193_extension(
        (candidate / generated_name).read_bytes()
    )
    if re.search(rb"^(?:INJECT|TRY_INJECT):", candidate_content, re.MULTILINE):
        raise SystemExit(
            f"Structural building output must use REPLACE entries only: {generated_name}"
        )
    reference_objects = object_blocks((reference / name).read_bytes(), strip_replace=False)
    candidate_objects = object_blocks(candidate_content, strip_replace=True)
    for object_name, candidate_body in candidate_objects.items():
        reference_body = reference_objects.get(object_name)
        if reference_body is None:
            raise SystemExit(f"Missing legacy reference object {name}:{object_name}")
        if candidate_body != reference_body:
            raise SystemExit(f"Building CBG object parity failed: {name}:{object_name}")
        objects_checked += 1

print(
    f"CBP/CBG hybrid building parity passed: "
    f"{len(replace_files)} REPLACE files, {len(inject_files)} INJECT files, "
    f"{objects_checked} complete objects plus validated additive deltas."
)
PY

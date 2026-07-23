#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo_root"
# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"
if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR before running CBG RGO-price validation.' >&2
	exit 1
fi

game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
percent="${MODEU5_US09_BONUS_PERCENT:-5}"
rgo_price_percent="${MODEU5_US09_RGO_PRICE_OFFSET_PERCENT:-8}"
fixed_price="${MODEU5_US09_RGO_FIXED_PRICE:-60}"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-rgo.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$work_dir/reference/in_game/common"

target="in_game/common/prices/00_hardcoded.txt"

# The retained offset adapter must remain byte-identical to the previous
# US-09 materializer for the same configured percentage.
./tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh "$percent" \
	--rgo-price-percent "$rgo_price_percent" \
	--trade-capacity-percent "${MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT:-15}" \
	--extra-burgher-promotion-speed "${EXTRA_BURGHER_PROMOTION_SPEED:-10}" \
	--extra-laborer-promotion-speed "${EXTRA_LABORER_PROMOTION_SPEED:-10}" \
	--common-dir "$EU5_GAME_COMMON_DIR" --package-common-dir "$work_dir/reference/in_game/common" >/dev/null
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_rgo_prices_spec.py \
	--game-root "$game_root" \
	--adapter offset \
	--percent "$rgo_price_percent" \
	--fixed-price "$fixed_price" \
	--output "$work_dir/offset.json"
python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/offset.json" \
	--output-root "$work_dir/offset-candidate" \
	--manifest "$work_dir/offset-candidate/manifest.json"
if ! cmp -s "$work_dir/reference/$target" "$work_dir/offset-candidate/$target"; then
	diff -u "$work_dir/reference/$target" "$work_dir/offset-candidate/$target" || true
	exit 1
fi

# The fixed adapter is validated after real CBG materialization. Objects whose
# Vanilla value already equals the configured target must remain omitted by
# generic effective-change detection; all other targeted objects must be emitted.
python3 tools/cbg/adapters/cbp/generate_cbp_cbg_rgo_prices_spec.py \
	--game-root "$game_root" \
	--adapter fixed \
	--percent "$rgo_price_percent" \
	--fixed-price "$fixed_price" \
	--output "$work_dir/fixed.json"
python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/fixed.json" \
	--output-root "$work_dir/fixed-candidate" \
	--manifest "$work_dir/fixed-candidate/manifest.json"

python3 - "$game_root/$target" "$work_dir/fixed-candidate/$target" "$fixed_price" <<'PY'
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

from tools.cbg.adapters.cbp.generate_cbp_cbg_rgo_prices_spec import TARGETS
from tools.cbg.community_balance_generator import ASSIGNMENT, field_matches, scan_objects

source_path = Path(sys.argv[1])
candidate_path = Path(sys.argv[2])
fixed_price = Decimal(sys.argv[3])


def values(path: Path) -> dict[str, Decimal]:
    if not path.is_file():
        return {}
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    objects = {obj.path: obj for obj in scan_objects(lines)}
    result: dict[str, Decimal] = {}
    for path_key, obj in objects.items():
        if len(path_key) != 1:
            continue
        matches = field_matches(lines, obj, "gold")
        if len(matches) != 1:
            continue
        match = ASSIGNMENT.match(lines[matches[0]].rstrip("\r\n"))
        if match is not None:
            result[path_key[0]] = Decimal(match.group("value"))
    return result


source_values = values(source_path)
candidate_values = values(candidate_path)
for name in TARGETS:
    if name not in source_values:
        raise SystemExit(f"Vanilla source is missing numeric {name}.gold")
    if source_values[name] == fixed_price:
        if name in candidate_values:
            raise SystemExit(f"No-op fixed-price object must be omitted: {name}")
    elif candidate_values.get(name) != fixed_price:
        raise SystemExit(
            f"Materialized {name}.gold is {candidate_values.get(name)}, expected {fixed_price}"
        )

unexpected = set(candidate_values) - set(TARGETS)
if unexpected:
    raise SystemExit(f"Fixed-price output contains unrelated objects: {sorted(unexpected)}")
PY

# The cross-family master specification must describe the same selected adapter,
# not retain an independent RGO-price formula.
python3 - "$game_root" "$fixed_price" "$rgo_price_percent" <<'PY'
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

from tools.cbg.adapters.cbp.generate_cbp_community_balance_spec import rgo_price_transformations
from tools.cbg.adapters.cbp.generate_cbp_cbg_rgo_prices_spec import (
    FIXED_ADAPTER,
    OFFSET_ADAPTER,
    build_selected_spec,
)

game_root = Path(sys.argv[1])
fixed_price = Decimal(sys.argv[2])
percent = Decimal(sys.argv[3])
for adapter in (FIXED_ADAPTER, OFFSET_ADAPTER):
    os.environ["MODEU5_US09_RGO_PRICE_ADAPTER"] = adapter
    os.environ["MODEU5_US09_RGO_FIXED_PRICE"] = str(fixed_price)
    os.environ["MODEU5_US09_RGO_PRICE_OFFSET_PERCENT"] = str(percent)
    master = rgo_price_transformations(game_root)
    focused = build_selected_spec(game_root, adapter, fixed_price, percent)["transformations"]
    master_values = {rule["object"]: str(rule["value"]) for rule in master}
    focused_values = {rule["object"]: str(rule["value"]) for rule in focused}
    if master_values != focused_values:
        raise SystemExit(
            f"Master RGO rules diverge from selected {adapter} adapter: "
            f"master={master_values}, focused={focused_values}"
        )
PY

printf 'CBP/CBG RGO-price validation passed: fixed target %s materialized; offset parity retained at %s%%.\n' \
	"$fixed_price" "$rgo_price_percent"

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
rgo_price="${MODEU5_US09_RGO_PRICE:-60}"
legacy_percent="${MODEU5_US09_RGO_PRICE_OFFSET_PERCENT:-40}"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-rgo.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

python3 tools/cbg/adapters/cbp/generate_cbp_cbg_rgo_prices_spec.py \
	--game-root "$game_root" \
	--mode absolute \
	--price "$rgo_price" \
	--percent "$legacy_percent" \
	--output "$work_dir/rgo.json"
python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" --spec "$work_dir/rgo.json" \
	--output-root "$work_dir/candidate" --manifest "$work_dir/candidate/manifest.json"

python3 tools/cbg/adapters/cbp/generate_cbp_cbg_rgo_prices_spec.py \
	--game-root "$game_root" \
	--mode inverse_percent \
	--price "$rgo_price" \
	--percent "$legacy_percent" \
	--output "$work_dir/rgo_legacy.json" >/dev/null

python3 - "$game_root" "$work_dir/rgo.json" "$work_dir/rgo_legacy.json" \
	"$work_dir/candidate/in_game/common/prices/00_hardcoded.txt" \
	"$rgo_price" "$legacy_percent" <<'PY'
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from tools.cbg.community_balance_generator import ASSIGNMENT, field_matches, scan_objects

TARGETS = (
    "expand_rgo_mining",
    "expand_rgo_farming",
    "expand_rgo_hunting",
    "expand_rgo_gathering",
    "expand_rgo_forestry",
)
SOURCE = "in_game/common/prices/00_hardcoded.txt"

game_root = Path(sys.argv[1])
absolute_spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
legacy_spec = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
candidate = Path(sys.argv[4]).read_text(encoding="utf-8")
absolute_price = Decimal(sys.argv[5])
legacy_percent = Decimal(sys.argv[6])

if absolute_spec.get("policy", {}).get("mode") != "absolute":
    raise SystemExit("RGO price policy must default to absolute mode")
absolute_rules = absolute_spec.get("transformations", [])
if len(absolute_rules) != len(TARGETS):
    raise SystemExit(f"Expected {len(TARGETS)} absolute RGO rules; found {len(absolute_rules)}")
for rule in absolute_rules:
    if Decimal(str(rule.get("value"))) != absolute_price:
        raise SystemExit(
            f"Absolute RGO rule {rule.get('object')} is {rule.get('value')}, expected {absolute_price}"
        )

for name in TARGETS:
    block = re.search(
        rf"(?ms)^{re.escape(name)}\s*=\s*\{{(?P<body>.*?)^\}}",
        candidate,
    )
    if block is None:
        raise SystemExit(f"Generated RGO override is missing {name}")
    gold = re.search(r"(?m)^\s*gold\s*=\s*([^\s#]+)", block.group("body"))
    if gold is None or Decimal(gold.group(1)) != absolute_price:
        actual = gold.group(1) if gold else "missing"
        raise SystemExit(f"Generated {name}.gold is {actual}, expected {absolute_price}")

if legacy_spec.get("policy", {}).get("mode") != "inverse_percent":
    raise SystemExit("Retained legacy RGO price policy is not selectable")
legacy_by_object = {
    rule["object"]: Decimal(str(rule["value"]))
    for rule in legacy_spec.get("transformations", [])
}
source_lines = (game_root / SOURCE).read_text(encoding="utf-8-sig").splitlines(keepends=True)
source_objects = {obj.path: obj for obj in scan_objects(source_lines)}
factor = Decimal(1) / (Decimal(1) + legacy_percent / Decimal(100))
for name in TARGETS:
    matches = field_matches(source_lines, source_objects[(name,)], "gold")
    if len(matches) != 1:
        raise SystemExit(f"Vanilla source does not expose exactly one {name}.gold")
    match = ASSIGNMENT.match(source_lines[matches[0]].rstrip("\r\n"))
    if match is None:
        raise SystemExit(f"Vanilla {name}.gold is not numeric")
    expected = (Decimal(match.group("value")) * factor).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    if legacy_by_object.get(name) != expected:
        raise SystemExit(
            f"Legacy {name}.gold is {legacy_by_object.get(name)}, expected {expected}"
        )
PY

printf 'CBP/CBG RGO-price validation passed: absolute target %s; legacy inverse-percent mode retained.\n' "$rgo_price"

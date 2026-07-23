#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo_root"

if [[ -f .cbp.local.env ]]; then
	set -a
	# shellcheck disable=SC1091
	source .cbp.local.env
	set +a
fi

if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR in .cbp.local.env before running focused CBG parity.' >&2
	exit 1
fi

game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
target="main_menu/common/script_values/default_values.txt"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-default-values.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

python3 tools/cbg/adapters/cbp/generate_cbp_cbg_default_values_spec.py \
	--game-root "$game_root" \
	--output "$work_dir/default_values.json"
python3 - "$game_root" "$work_dir/reference" <<'PY'
import io
import sys
from pathlib import Path

import tools.generate_political_reward_overrides as political_rewards
from tools.cbg.adapters.cbp.optional_vanilla_fields import (
    PROFIT_MARGIN_FIELDS,
    discover_optional_root_numeric_fields,
)

game_root = Path(sys.argv[1])
available_profit_margins = discover_optional_root_numeric_fields(
    game_root / "main_menu/common/script_values/default_values.txt",
    PROFIT_MARGIN_FIELDS,
    policy_name="production profit-margin",
    warning_stream=io.StringIO(),
)
# The legacy #188 reference materializer predates optional Vanilla fields.
# Narrow its historical mandatory set to the fields exposed by this game version
# so parity tests the same compatibility contract as the focused CBG adapter.
political_rewards.PROFIT_MARGIN_FIELDS = set(available_profit_margins)
political_rewards.write_central_script_value_override(
    game_root,
    Path(sys.argv[2]),
    political_rewards.centralizable_script_values(game_root),
)
PY
python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" \
	--spec "$work_dir/default_values.json" \
	--output-root "$work_dir/output" \
	--manifest "$work_dir/output/cbg_manifest.json"

python3 - "$work_dir/output/cbg_manifest.json" "$target" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
paths = [entry["path"] for entry in manifest.get("files", [])]
if paths != [sys.argv[2]]:
    raise SystemExit(f"Focused CBG scope violation: generated {paths!r}")
PY

if ! cmp -s "$work_dir/reference/$target" "$work_dir/output/$target"; then
	printf '%s\n' 'Focused CBG output differs from the corrected #188 default_values.txt:' >&2
	diff -u "$work_dir/reference/$target" "$work_dir/output/$target" || true
	exit 1
fi

printf '%s\n' 'CBP/CBG focused parity passed: default_values.txt is byte-identical and the only output.'

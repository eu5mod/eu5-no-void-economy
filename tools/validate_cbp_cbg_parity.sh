#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ -f .cbp.local.env ]]; then
	set -a
	# shellcheck disable=SC1091
	source .cbp.local.env
	set +a
fi

if [[ -z "${EU5_GAME_COMMON_DIR:-}" ]]; then
	printf '%s\n' 'Set EU5_GAME_COMMON_DIR in .cbp.local.env before running CBP/CBG parity.' >&2
	exit 1
fi

game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
tracked_spec="$repo_root/tools/specs/cbp_pr188_balance.generated.json"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cbp-cbg-parity.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

python3 tools/generate_cbp_community_balance_spec.py \
	--game-root "$game_root" \
	--output "$work_dir/cbp_balance.json"

if ! cmp -s "$tracked_spec" "$work_dir/cbp_balance.json"; then
	printf '%s\n' 'Tracked CBP CBG spec is stale. Regenerate it with:' >&2
	printf '%s\n' '  python3 tools/generate_cbp_community_balance_spec.py' >&2
	exit 1
fi

python3 tools/cbg/community_balance_generator.py \
	--game-root "$game_root" \
	--spec "$tracked_spec" \
	--output-root "$work_dir/output" \
	--manifest "$work_dir/output/cbg_manifest.json"

python3 tools/compare_cbp_cbg_outputs.py \
	--game-root "$game_root" \
	--reference-root "$repo_root/packages/cbp_economy_rebalance" \
	--repo-root "$repo_root" \
	--candidate-root "$work_dir/output" \
	--spec "$tracked_spec" \
	--report "$work_dir/parity-report.json"

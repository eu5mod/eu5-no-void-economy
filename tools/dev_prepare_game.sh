#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_args=()
run_idempotence="yes"
clear_logs="yes"

usage() {
	cat <<'EOF_USAGE'
Usage: ./tools/dev_prepare_game.sh [options]

Canonical local preparation before an in-game ModeU5 validation run:
  1. generate all artifacts;
  2. prove generation is idempotent;
  3. run the static validation suite;
  4. install the already validated package set;
  5. verify the installed branch/commit/package set;
  6. clear current EU5 logs;
  7. print the in-game events to run.

Options:
  --target PATH       Forward a non-default mod installation directory.
  --skip-idempotence  Generate once instead of proving a stable second pass.
  --keep-logs         Do not clear current EU5 logs.
  -h, --help          Show this help.

The command does not launch EU5 and does not stage, commit, or modify Git state.
EOF_USAGE
}

while (($# > 0)); do
	case "$1" in
		--target)
			if (($# < 2)); then
				printf '%s\n' 'Missing path after --target.' >&2
				exit 2
			fi
			target_args=(--target "$2")
			shift 2
			;;
		--skip-idempotence)
			run_idempotence="no"
			shift
			;;
		--keep-logs)
			clear_logs="no"
			shift
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			printf 'Unknown argument: %s\n' "$1" >&2
			usage >&2
			exit 2
			;;
	esac
done

cd "$repo_root"

step() {
	printf '\n%s\n' '########################################################################'
	printf '[%s] %s\n' "$1" "$2"
}

step '1/7' 'Generate all runtime and package artifacts'
./tools/generate_all.sh

if [[ "$run_idempotence" == "yes" ]]; then
	step '2/7' 'Verify that a second generation pass is idempotent'
	before_worktree="$(mktemp)"
	before_index="$(mktemp)"
	before_status="$(mktemp)"
	after_worktree="$(mktemp)"
	after_index="$(mktemp)"
	after_status="$(mktemp)"
	trap 'rm -f "$before_worktree" "$before_index" "$before_status" "$after_worktree" "$after_index" "$after_status"' EXIT

	git diff --binary --no-ext-diff > "$before_worktree"
	git diff --cached --binary --no-ext-diff > "$before_index"
	git status --porcelain=v1 --untracked-files=all > "$before_status"
	./tools/generate_all.sh
	git diff --binary --no-ext-diff > "$after_worktree"
	git diff --cached --binary --no-ext-diff > "$after_index"
	git status --porcelain=v1 --untracked-files=all > "$after_status"

	if ! cmp -s "$before_worktree" "$after_worktree" || \
		! cmp -s "$before_index" "$after_index" || \
		! cmp -s "$before_status" "$after_status"
	then
		printf '%s\n' 'Generation is not idempotent: the second pass changed the working tree.' >&2
		git status --short >&2
		exit 1
	fi
	printf '%s\n' 'Generation idempotence passed.'
else
	step '2/7' 'Skip generation idempotence by explicit request'
fi

step '3/7' 'Run canonical static validation suite'
python3 tools/validate_us04_pop_demand_architecture.py
./tools/validate_module_packages.sh
./tools/audit_cbp_persistent_state.sh
./tools/validate_cbp_script_safety.sh
./tools/normalize_cmm_value_links.sh --check
python3 tools/validate_ci_static_contracts.py
python3 tools/validate_cmm_configuration.py
python3 tools/validate_mandatory_expenses.py
python3 tools/validate_audit_catalog.py
git diff --check
git diff --cached --check

step '4/7' 'Install the generated and validated package set'
./tools/install_local_packages.sh --skip-generate "${target_args[@]}"

step '5/7' 'Verify installed package provenance and content'
./tools/install_local_packages.sh --check "${target_args[@]}"

if [[ "$clear_logs" == "yes" ]]; then
	step '6/7' 'Clear current EU5 logs'
	./tools/clear_eu5_logs.sh
else
	step '6/7' 'Keep current EU5 logs by explicit request'
fi

step '7/7' 'Preparation complete'
cat <<'EOF_EVENTS'
Run in EU5 with the Core Tests package loaded:

  event cbp_revalidate_debug.1

For the focused US-04 two-stage validation:

  event cbp_us04_debug.10
  wait at least two in-game days
  event cbp_us04_debug.60

Then summarize the current logs with:

  ./tools/summarize_cbp_logs.sh
EOF_EVENTS

#!/usr/bin/env bash

set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
current_step="startup"
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

status_file="$(mktemp "${TMPDIR:-/tmp}/cbp-dev-prepare-status.XXXXXX")"
before_worktree=""
before_index=""
before_status=""
after_worktree=""
after_index=""
after_status=""
export CBP_CONSOLE_STATUS_FILE="$status_file"

step_titles=(
	""
	"Generate all runtime and package artifacts"
	"Verify generation idempotence"
	"Run canonical static validation suite"
	"Install the generated and validated package set"
	"Verify installed package provenance and content"
	"Prepare clean runtime logs"
	"Print the in-game validation protocol"
)
step_statuses=("" "SKIPPED" "SKIPPED" "SKIPPED" "SKIPPED" "SKIPPED" "SKIPPED" "SKIPPED")
current_step_id=0

cleanup() {
	rm -f \
		"$status_file" \
		"${before_worktree:-}" \
		"${before_index:-}" \
		"${before_status:-}" \
		"${after_worktree:-}" \
		"${after_index:-}" \
		"${after_status:-}"
}

begin_step() {
	current_step_id="$1"
	current_step="$1/7 ${step_titles[$1]}"
	cbp_console_section_start "$1/7" "${step_titles[$1]}"
}

derive_step_status() {
	local step_id="$1"
	local child_statuses
	child_statuses="$(awk -F '\t' -v prefix="$step_id." 'index($1, prefix) == 1 { print $2 }' "$status_file")"
	if grep -qx FAILED <<<"$child_statuses"; then
		printf 'FAILED'
	elif grep -qx WARNING <<<"$child_statuses"; then
		printf 'WARNING'
	elif grep -qx OK <<<"$child_statuses"; then
		printf 'OK'
	elif grep -qx SKIPPED <<<"$child_statuses"; then
		printf 'SKIPPED'
	else
		printf 'OK'
	fi
}

finish_step() {
	local status="${1:-}"
	if [[ -z "$status" ]]; then
		status="$(derive_step_status "$current_step_id")"
	fi
	step_statuses[$current_step_id]="$status"
	printf '\n'
	cbp_console_section_end "$current_step_id/7" "$status" "${step_titles[$current_step_id]}"
}

print_summary_line() {
	local indent="$1"
	local status="$2"
	local id="$3"
	local title="$4"
	local detail="${5:-}"
	printf '%s' "$indent"
	cbp_console_status_badge "$status"
	printf ' %-5s %s' "$id" "$title"
	if [[ -n "$detail" ]]; then
		printf '  (%s)' "$detail"
	fi
	printf '\n'
}

print_summary() {
	local step_id
	local id
	local status
	local title
	local detail
	local ok_count=0
	local warning_count=0
	local failed_count=0
	local skipped_count=0

	printf '\n'
	cbp_console_major_separator
	cbp_console_styled '1' 'PREPARATION SUMMARY'
	printf '\n\n'

	for step_id in 1 2 3 4 5 6 7; do
		print_summary_line "" "${step_statuses[$step_id]}" "$step_id" "${step_titles[$step_id]}"
		while IFS=$'\t' read -r id status title detail; do
			[[ "$id" != "$step_id."* ]] && continue
			print_summary_line "    " "$status" "$id" "$title" "$detail"
		done < "$status_file"
	done

	while IFS=$'\t' read -r _id status _title _detail; do
		case "$status" in
			OK) ok_count=$((ok_count + 1)) ;;
			WARNING) warning_count=$((warning_count + 1)) ;;
			FAILED) failed_count=$((failed_count + 1)) ;;
			SKIPPED) skipped_count=$((skipped_count + 1)) ;;
		esac
	done < "$status_file"

	printf '\nSubsteps: '
	cbp_console_styled '1;32' "$ok_count OK"
	printf '  '
	cbp_console_styled '1;33' "$warning_count warning(s)"
	printf '  '
	cbp_console_styled '1;31' "$failed_count failed"
	printf '  '
	cbp_console_styled '1;36' "$skipped_count skipped"
	printf '\n'
}

run_generation_pass() {
	local prefix="$1"
	local -a pipeline_status

	set +e
	CBP_CONSOLE_STEP_PREFIX="$prefix" ./tools/generate_all.sh 2>&1 |
		cbp_console_filter_stream compact
	pipeline_status=("${PIPESTATUS[@]}")
	set -e
	return "${pipeline_status[0]}"
}

report_failure() {
	status=$?
	trap - ERR
	if ((current_step_id > 0)); then
		step_statuses[$current_step_id]="FAILED"
	fi
	printf '\n' >&2
	cbp_console_failure "Local game preparation stopped during: $current_step"
	printf '%s\n' 'Subsequent steps were not run. Review the failed substep output and the summary below.' >&2
	print_summary
	exit "$status"
}

trap report_failure ERR
trap cleanup EXIT

begin_step 1
run_generation_pass 1
finish_step

if [[ "$run_idempotence" == "yes" ]]; then
	begin_step 2
	before_worktree="$(mktemp)"
	before_index="$(mktemp)"
	before_status="$(mktemp)"
	after_worktree="$(mktemp)"
	after_index="$(mktemp)"
	after_status="$(mktemp)"

	capture_generation_state() {
		git diff --binary --no-ext-diff > "$1"
		git diff --cached --binary --no-ext-diff > "$2"
		git status --porcelain=v1 --untracked-files=all > "$3"
	}
	compare_generation_state() {
		capture_generation_state "$after_worktree" "$after_index" "$after_status"
		if ! cmp -s "$before_worktree" "$after_worktree" || \
			! cmp -s "$before_index" "$after_index" || \
			! cmp -s "$before_status" "$after_status"
		then
			printf '%s\n' 'Generation is not idempotent: the second pass changed the working tree.' >&2
			git status --short >&2
			return 1
		fi
	}

	cbp_console_run_task '2.0' 'Capture the first-pass Git state' quiet \
		capture_generation_state "$before_worktree" "$before_index" "$before_status"
	run_generation_pass 2
	cbp_console_run_task '2.7' 'Compare worktree, index, and untracked outputs' quiet \
		compare_generation_state
	finish_step
else
	begin_step 2
	cbp_console_task_start '2.1' 'Generation idempotence'
	cbp_console_task_end '2.1' SKIPPED 'Generation idempotence' 'explicit --skip-idempotence'
	cbp_console_status_record '2.1' SKIPPED 'Generation idempotence' 'explicit --skip-idempotence'
	finish_step SKIPPED
fi

begin_step 3
cbp_console_run_task '3.1' 'US-04 Pop-demand architecture' quiet \
	python3 tools/validate_us04_pop_demand_architecture.py
cbp_console_run_task '3.2' 'Module package contracts' quiet \
	./tools/validate_module_packages.sh
cbp_console_run_task '3.3' 'Persistent-state ownership audit' quiet \
	./tools/audit_cbp_persistent_state.sh
cbp_console_run_task '3.4' 'Runtime script safety' quiet \
	./tools/validate_cbp_script_safety.sh
cbp_console_run_task '3.5' 'CMM value-link normalization' quiet \
	./tools/normalize_cmm_value_links.sh --check
cbp_console_run_task '3.6' 'CI static contracts' quiet \
	python3 tools/validate_ci_static_contracts.py
cbp_console_run_task '3.7' 'CMM configuration' quiet \
	python3 tools/validate_cmm_configuration.py
cbp_console_run_task '3.8' 'Mandatory-expense business rules' quiet \
	python3 tools/validate_mandatory_expenses.py
cbp_console_run_task '3.9' 'Market-price adjustment speed' quiet \
	python3 tools/validate_market_price_speed.py
cbp_console_run_task '3.10' 'Audit-document catalog' quiet \
	python3 tools/validate_audit_catalog.py
cbp_console_run_task '3.11' 'Working-tree patch hygiene' quiet \
	cbp_check_patch_hygiene 'Working tree' git diff --check
cbp_console_run_task '3.12' 'Staging-area patch hygiene' quiet \
	cbp_check_patch_hygiene 'Staging area' git diff --cached --check
finish_step

begin_step 4
if ((${#target_args[@]} > 0)); then
	cbp_console_run_task '4.1' 'Install validated packages into the local mod directory' quiet \
		./tools/install_local_packages.sh --skip-generate "${target_args[@]}"
else
	cbp_console_run_task '4.1' 'Install validated packages into the local mod directory' quiet \
		./tools/install_local_packages.sh --skip-generate
fi
finish_step

begin_step 5
if ((${#target_args[@]} > 0)); then
	cbp_console_run_task '5.1' 'Compare installed provenance and package content' compact \
		./tools/install_local_packages.sh --check "${target_args[@]}"
else
	cbp_console_run_task '5.1' 'Compare installed provenance and package content' compact \
		./tools/install_local_packages.sh --check
fi
finish_step

begin_step 6
if [[ "$clear_logs" == "yes" ]]; then
	cbp_console_run_task '6.1' 'Clear error, game, and debug logs' compact \
		./tools/clear_eu5_logs.sh
	finish_step
else
	cbp_console_task_start '6.1' 'Clear error, game, and debug logs'
	cbp_console_task_end '6.1' SKIPPED 'Clear error, game, and debug logs' 'explicit --keep-logs'
	cbp_console_status_record '6.1' SKIPPED 'Clear error, game, and debug logs' 'explicit --keep-logs'
	finish_step SKIPPED
fi

print_runtime_protocol() {
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
}

begin_step 7
cbp_console_run_task '7.1' 'Display runtime events and log-summary command' full \
	print_runtime_protocol
finish_step

print_summary

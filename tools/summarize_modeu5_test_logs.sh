#!/usr/bin/env bash

set -euo pipefail

default_logs_dir="${MODEU5_LOG_DIR:-${HOME}/Documents/Paradox Interactive/Europa Universalis V/logs}"
logs_dir="$default_logs_dir"

usage() {
	printf 'Usage: %s [--logs-dir PATH]\n' "$0"
	printf '\n'
	printf 'Prints a compact summary of ModeU5 revalidation scenario markers.\n'
	printf 'Default logs directory: %s\n' "$default_logs_dir"
}

while (($# > 0)); do
	case "$1" in
		--logs-dir)
			if (($# < 2)); then
				printf 'Missing path after --logs-dir.\n' >&2
				exit 2
			fi
			logs_dir="$2"
			shift 2
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

if [[ ! -d "$logs_dir" ]]; then
	printf 'EU5 logs directory does not exist: %s\n' "$logs_dir" >&2
	exit 1
fi

log_files=()
for log_name in debug.log error.log game.log system.log; do
	log_file="$logs_dir/$log_name"
	if [[ -f "$log_file" ]]; then
		log_files+=("$log_file")
	fi
done

if ((${#log_files[@]} == 0)); then
	printf 'No EU5 log files found in: %s\n' "$logs_dir" >&2
	exit 1
fi

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

grep -hE 'ModeU5 TEST (ENTERED|PASS|FAIL|BLOCKED|PENDING) scenario=' "${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$tmp_file" || true

count_marker() {
	local marker="$1"
	grep -c "ModeU5 TEST ${marker} " "$tmp_file" || true
}

entered_count="$(count_marker ENTERED)"
pass_count="$(count_marker PASS)"
fail_count="$(count_marker FAIL)"
blocked_count="$(count_marker BLOCKED)"
pending_count="$(count_marker PENDING)"

expected_scenarios=(
	main_revalidation
	us02_capacity
	core01_single_record
	core01_same_market_transfer
	core01_inter_market_transfer
	core02_initialization
	us00_controlled_pipeline
	us00_monthly_runtime
	us10_demand_resolution
	us10_issue109_fast_path_pruning
	perf10_13_active_repair_metrics
	main_revalidation_summary
)

missing_scenarios=()
for scenario in "${expected_scenarios[@]}"; do
	if ! grep -q "scenario=${scenario}\\b" "$tmp_file"; then
		missing_scenarios+=("$scenario")
	fi
done

printf 'ModeU5 revalidation summary\n'
printf 'Logs directory: %s\n' "$logs_dir"
printf 'Files scanned: %s\n' "${#log_files[@]}"
printf 'Entered: %s\n' "$entered_count"
printf 'Passed:  %s\n' "$pass_count"
printf 'Failed:  %s\n' "$fail_count"
printf 'Blocked: %s\n' "$blocked_count"
printf 'Pending: %s\n' "$pending_count"
printf 'Missing expected scenarios: %s\n' "${#missing_scenarios[@]}"
printf '\n'

if [[ ! -s "$tmp_file" ]]; then
	printf 'No ModeU5 TEST scenario markers found.\n'
	printf 'Run: event modeu5_revalidate_debug.1\n'
	exit 0
fi

printf 'Scenario lines:\n'
cat "$tmp_file"

if ((${#missing_scenarios[@]} > 0)); then
	printf '\n'
	printf 'Missing expected scenario markers:\n'
	printf '%s\n' "${missing_scenarios[@]}"
fi

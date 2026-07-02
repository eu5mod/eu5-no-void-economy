#!/usr/bin/env bash

set -euo pipefail

default_logs_dir="${MODEU5_LOG_DIR:-${HOME}/Documents/Paradox Interactive/Europa Universalis V/logs}"
logs_dir="$default_logs_dir"

usage() {
	printf 'Usage: %s [--logs-dir PATH]\n' "$0"
	printf '\n'
	printf 'Prints a compact summary of ModeU5 revalidation scenario markers, debug level markers, main-mode traces, PERF-14 diagnostics, US-10 visibility traces, and CORE-04 topology diagnostics.\n'
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

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

scenario_file="$tmp_dir/scenario_lines"
debug_level_file="$tmp_dir/debug_level_lines"
main_mode_file="$tmp_dir/main_mode_lines"
perf14_file="$tmp_dir/perf14_lines"
us10ui_file="$tmp_dir/us10_ui_lines"
core04_file="$tmp_dir/core04_lines"
localization_only_file="$tmp_dir/localization_only_modeu5_lines"

grep -hE 'ModeU5 TEST (ENTERED|PASS|FAIL|BLOCKED|PENDING) scenario=' "${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$scenario_file" || true

grep -hE 'ModeU5 DEBUG_LEVEL ' "${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$debug_level_file" || true

grep -hE 'ModeU5 PERF-14 (MAIN_MODE|DUMP main_mode=)' "${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$main_mode_file" || true

grep -hE 'ModeU5 PERF-14 (DUMP|STOCK_MUTATION_GATE|MARKET_RUNTIME_GATE|PROMOTION|SPARSE_SUPPLIERS|FAIL_REASON|RESULT)' "${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$perf14_file" || true

grep -hE 'ModeU5 US-10(-UI)? (DUMP|CANDIDATE TRACE|MUTATION TRACE|SUMMARY|RESOLUTION|CANDIDATE_TRACE|MUTATION_TRACE|FAST_PATH|REASON_MAP)' "${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$us10ui_file" || true

grep -hE 'ModeU5 CORE-04 (MARKET_ENTRY|DUMP|FAIL_REASON|RESULT)' "${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$core04_file" || true

grep -hE 'Tried to localize with localization disabled.*ModeU5 (TEST|DEBUG_LEVEL|PERF-14|US-10|CORE-04)' "${log_files[@]}" \
	>"$localization_only_file" || true

count_marker() {
	local marker="$1"
	grep -c "ModeU5 TEST ${marker} " "$scenario_file" || true
}

entered_count="$(count_marker ENTERED)"
pass_count="$(count_marker PASS)"
fail_count="$(count_marker FAIL)"
blocked_count="$(count_marker BLOCKED)"
pending_count="$(count_marker PENDING)"
debug_level_count="$(grep -c 'ModeU5 DEBUG_LEVEL ' "$debug_level_file" || true)"
main_mode_count="$(grep -c 'ModeU5 PERF-14 ' "$main_mode_file" || true)"
perf14_count="$(grep -c 'ModeU5 PERF-14 ' "$perf14_file" || true)"
us10ui_count="$(grep -c 'ModeU5 US-10' "$us10ui_file" || true)"
core04_count="$(grep -c 'ModeU5 CORE-04 ' "$core04_file" || true)"
localization_only_count="$(grep -c 'ModeU5 ' "$localization_only_file" || true)"

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
	us10_ui_visibility
	perf10_13_active_repair_metrics
	core04_market_entry
	main_revalidation_summary
	perf14_performance_mode_cmm
)

missing_scenarios=()
for scenario in "${expected_scenarios[@]}"; do
	if ! grep -q "scenario=${scenario}\\b" "$scenario_file"; then
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
printf 'Debug level markers: %s\n' "$debug_level_count"
printf 'Main mode traces: %s\n' "$main_mode_count"
printf 'PERF-14 diagnostics: %s\n' "$perf14_count"
printf 'US-10 visibility diagnostics: %s\n' "$us10ui_count"
printf 'CORE-04 topology diagnostics: %s\n' "$core04_count"
printf 'Localization-disabled-only ModeU5 markers: %s\n' "$localization_only_count"
printf 'Missing expected full-revalidation scenarios: %s\n' "${#missing_scenarios[@]}"
printf '\n'

if [[ ! -s "$scenario_file" ]]; then
	printf 'No non-localization ModeU5 TEST scenario markers found.\n'
	if [[ -s "$localization_only_file" ]]; then
		printf 'Only localization-disabled copies of ModeU5 markers were found; inspect debug.log/game.log or enable Debug/Audit output before treating this run as PASS.\n'
	fi
	printf 'Run: event modeu5_revalidate_debug.1\n'
	printf 'For PERF-14 only: event modeu5_perf14_debug.1\n'
	printf 'For CORE-04 only: event modeu5_core04_debug.1\n'
	printf '\n'
fi

if [[ -s "$debug_level_file" ]]; then
	printf 'Debug level lines:\n'
	cat "$debug_level_file"
	printf '\n'
else
	printf 'No ModeU5 DEBUG_LEVEL markers found.\n\n'
fi

if [[ -s "$main_mode_file" ]]; then
	printf 'Main mode trace lines:\n'
	printf 'Mode map: main_mode=1 Active Performance; main_mode=2 Active Normal; main_mode=3 Deactivated.\n'
	cat "$main_mode_file"
	printf '\n'
else
	printf 'No ModeU5 PERF-14 main-mode trace lines found.\n\n'
fi

if [[ -s "$perf14_file" ]]; then
	printf 'PERF-14 diagnostic lines:\n'
	cat "$perf14_file"
	printf '\n'
else
	printf 'No non-localization PERF-14 diagnostic lines found.\n\n'
fi

if [[ -s "$us10ui_file" ]]; then
	printf 'US-10 visibility diagnostic lines:\n'
	cat "$us10ui_file"
	printf '\n'
else
	printf 'No non-localization US-10 visibility diagnostic lines found.\n\n'
fi

if [[ -s "$core04_file" ]]; then
	printf 'CORE-04 topology diagnostic lines:\n'
	cat "$core04_file"
	printf '\n'
else
	printf 'No non-localization CORE-04 topology diagnostic lines found.\n\n'
fi

if [[ -s "$scenario_file" ]]; then
	printf 'Scenario lines:\n'
	cat "$scenario_file"
fi

if ((${#missing_scenarios[@]} > 0)); then
	printf '\n'
	printf 'Missing expected full-revalidation scenario markers:\n'
	printf '%s\n' "${missing_scenarios[@]}"
fi

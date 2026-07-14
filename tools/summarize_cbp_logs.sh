#!/usr/bin/env bash

set -euo pipefail

default_logs_dir="${MODEU5_LOG_DIR:-${HOME}/Documents/Paradox Interactive/Europa Universalis V/logs}"
logs_dir="$default_logs_dir"
since_time="${MODEU5_LOG_SINCE:-}"
expected_mode="${MODEU5_EXPECTED_SCENARIOS:-full}"

usage() {
	printf 'Usage: %s [--logs-dir PATH] [--since HH:MM:SS] [--expected full|pr126|us04|us04-estate|none]\n' "$0"
	printf '\n'
	printf 'Prints a compact summary of ModeU5 revalidation scenario markers, debug level markers, main-mode traces, PERF-14 diagnostics, US-10 visibility traces, US-04 diagnostics, and CORE-04 topology diagnostics.\n'
	printf 'Use --since to focus on a fresh validation window, for example --since 16:15:00.\n'
	printf 'Use --expected pr126 after running only event cbp_pr126_profile_debug.1 / .2 / cbp_pr126_debug.1.\n'
	printf 'Use --expected us04 after running only event cbp_us04_debug.1 option A.\n'
	printf 'Use --expected us04-estate after running only event cbp_us04_debug.1 option C.\n'
	printf 'Default logs directory: %s\n' "$default_logs_dir"
}

while (($# > 0)); do
	case "$1" in
		--logs-dir)
			if (($# < 2)); then printf 'Missing path after --logs-dir.\n' >&2; exit 2; fi
			logs_dir="$2"; shift 2 ;;
		--since)
			if (($# < 2)); then printf 'Missing HH:MM:SS after --since.\n' >&2; exit 2; fi
			since_time="$2"; shift 2 ;;
		--expected)
			if (($# < 2)); then printf 'Missing mode after --expected.\n' >&2; exit 2; fi
			expected_mode="$2"; shift 2 ;;
		-h|--help)
			usage; exit 0 ;;
		*)
			printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
	esac
done

if [[ -n "$since_time" && ! "$since_time" =~ ^[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
	printf 'Invalid --since value: %s. Expected HH:MM:SS.\n' "$since_time" >&2
	exit 2
fi

case "$expected_mode" in
	full|pr126|us04|us04-estate|none) ;;
	*) printf 'Invalid --expected mode: %s. Expected full, pr126, us04, us04-estate, or none.\n' "$expected_mode" >&2; exit 2 ;;
esac

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

all_lines_file="$tmp_dir/all_lines"
scenario_file="$tmp_dir/scenario_lines"
debug_level_file="$tmp_dir/debug_level_lines"
main_mode_file="$tmp_dir/main_mode_lines"
perf14_file="$tmp_dir/perf14_lines"
us10ui_file="$tmp_dir/us10_ui_lines"
us04_file="$tmp_dir/us04_lines"
core04_file="$tmp_dir/core04_lines"
localization_only_file="$tmp_dir/localization_only_cbp_lines"
scenario_state_file="$tmp_dir/scenario_state"
incomplete_scenario_file="$tmp_dir/incomplete_scenarios"

cat "${log_files[@]}" > "$all_lines_file"

if [[ -n "$since_time" ]]; then
	filtered_all_lines_file="$tmp_dir/all_lines_since"
	awk -v since="$since_time" '
		match($0, /^\[([0-9][0-9]:[0-9][0-9]:[0-9][0-9])\]/, m) {
			if (m[1] >= since) { print }
		}
	' "$all_lines_file" > "$filtered_all_lines_file"
	all_lines_file="$filtered_all_lines_file"
fi

grep -hE 'ModeU5 TEST (ENTERED|PASS|FAIL|BLOCKED|PENDING) scenario=' "$all_lines_file" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$scenario_file" || true

sed -nE 's/.*ModeU5 TEST (ENTERED|PASS|FAIL|BLOCKED|PENDING) scenario=([^[:space:]]+).*/\2	\1	&/p' "$scenario_file" \
	>"$scenario_state_file" || true

awk -F '\t' '
	{
		last_marker[$1] = $2
		last_line[$1] = $3
	}
	END {
		for (scenario in last_marker) {
			if (last_marker[scenario] == "ENTERED") {
				print scenario "\t" last_line[scenario]
			}
		}
	}
' "$scenario_state_file" >"$incomplete_scenario_file" || true

grep -hE 'ModeU5 DEBUG_LEVEL ' "$all_lines_file" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$debug_level_file" || true

grep -hE 'ModeU5 PERF-14 (MAIN_MODE|DUMP main_mode=)' "$all_lines_file" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$main_mode_file" || true

grep -hE 'ModeU5 PERF-14 (DUMP|STOCK_MUTATION_GATE|MARKET_RUNTIME_GATE|PROMOTION|SPARSE_SUPPLIERS|FAIL_REASON|RESULT)' "$all_lines_file" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$perf14_file" || true

grep -hE 'ModeU5 US-10(-UI)? (DUMP|CANDIDATE TRACE|MUTATION TRACE|SUMMARY|TABLE|RESOLUTION|CANDIDATE_TRACE|MUTATION_TRACE|FAST_PATH|REASON_MAP)' "$all_lines_file" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$us10ui_file" || true

grep -hE 'ModeU5 US-04 (DUMP|FAIL_REASON|RESULT|INITIALIZATION (DUMP|FAIL_REASON|RESULT)|ENDPOINT (DUMP|FAIL_REASON|RESULT)|VANILLA DEMAND (DUMP|FAIL_REASON|RESULT)|INJECTION (CONTROL|CANDIDATE|RESULT|MATRIX|MATRIX SUMMARY))' "$all_lines_file" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$us04_file" || true

grep -hE 'ModeU5 CORE-04 (MARKET_ENTRY|DUMP|FAIL_REASON|RESULT)' "$all_lines_file" \
	| grep -v 'Tried to localize with localization disabled' \
	>"$core04_file" || true

grep -hE 'Tried to localize with localization disabled.*ModeU5 (TEST|DEBUG_LEVEL|PERF-14|US-10|US-04|CORE-04)' "$all_lines_file" \
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
incomplete_scenario_count="$(grep -c . "$incomplete_scenario_file" || true)"
debug_level_count="$(grep -c 'ModeU5 DEBUG_LEVEL ' "$debug_level_file" || true)"
main_mode_count="$(grep -c 'ModeU5 PERF-14 ' "$main_mode_file" || true)"
perf14_count="$(grep -c 'ModeU5 PERF-14 ' "$perf14_file" || true)"
us10ui_count="$(grep -c 'ModeU5 US-10' "$us10ui_file" || true)"
us04_count="$(grep -c 'ModeU5 US-04 ' "$us04_file" || true)"
core04_count="$(grep -c 'ModeU5 CORE-04 ' "$core04_file" || true)"
localization_only_count="$(grep -c 'ModeU5 ' "$localization_only_file" || true)"

expected_scenarios=()
case "$expected_mode" in
	full)
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
			us04_pop_demand_adaptation
			perf10_13_active_repair_metrics
			core04_market_entry
			us17_us20_route_reconciliation
			main_revalidation_summary
		)
		;;
	pr126)
		expected_scenarios=(pr126_monthly_dispatcher_compare)
		;;
	us04)
		expected_scenarios=(us04_pop_demand_adaptation)
		;;
	us04-estate)
		expected_scenarios=(us04_estate_level_accounting)
		;;
	none)
		;;
esac

missing_scenarios=()
if [[ "$expected_mode" != "none" ]]; then
	for scenario in "${expected_scenarios[@]}"; do
		if ! grep -q "scenario=${scenario}\b" "$scenario_file"; then
			missing_scenarios+=("$scenario")
		fi
	done
fi

printf 'ModeU5 revalidation summary\n'
printf 'Logs directory: %s\n' "$logs_dir"
printf 'Files scanned: %s\n' "${#log_files[@]}"
if [[ -n "$since_time" ]]; then printf 'Since: %s\n' "$since_time"; fi
printf 'Expected scenario set: %s\n' "$expected_mode"
printf 'Entered: %s\n' "$entered_count"
printf 'Passed:  %s\n' "$pass_count"
printf 'Failed:  %s\n' "$fail_count"
printf 'Blocked: %s\n' "$blocked_count"
printf 'Pending: %s\n' "$pending_count"
printf 'Incomplete latest scenario runs: %s\n' "$incomplete_scenario_count"
printf 'Debug level markers: %s\n' "$debug_level_count"
printf 'Main mode traces: %s\n' "$main_mode_count"
printf 'PERF-14 diagnostics: %s\n' "$perf14_count"
printf 'US-10 visibility diagnostics: %s\n' "$us10ui_count"
printf 'US-04 diagnostics: %s\n' "$us04_count"
printf 'CORE-04 topology diagnostics: %s\n' "$core04_count"
printf 'Localization-disabled-only ModeU5 markers: %s\n' "$localization_only_count"
case "$expected_mode" in
	full) printf 'Missing expected full-revalidation scenarios: %s\n' "${#missing_scenarios[@]}" ;;
	pr126) printf 'Missing expected PR126 dispatcher scenarios: %s\n' "${#missing_scenarios[@]}" ;;
	us04) printf 'Missing expected US-04 focused scenarios: %s\n' "${#missing_scenarios[@]}" ;;
	us04-estate) printf 'Missing expected US-04 Estate focused scenarios: %s\n' "${#missing_scenarios[@]}" ;;
	none) printf 'Expected scenario checking disabled.\n' ;;
esac
printf '\n'

if [[ ! -s "$scenario_file" ]]; then
	printf 'No non-localization ModeU5 TEST scenario markers found.\n'
	if [[ -s "$localization_only_file" ]]; then
		printf 'Only localization-disabled copies of ModeU5 markers were found; inspect debug.log/game.log or enable Debug/Audit output before treating this run as PASS.\n'
	fi
	printf 'Run: event cbp_revalidate_debug.1\n'
	printf 'For US-04 architecture probes: event cbp_us04_debug.1\n'
	printf 'For PR126 dispatcher only: event cbp_pr126_profile_debug.1; event cbp_pr126_profile_debug.2; event cbp_pr126_debug.1\n'
	printf 'For PERF-14 only: event cbp_perf14_debug.1\n'
	printf 'For CORE-04 only: event cbp_core04_debug.1\n'
	printf '\n'
fi

if [[ -s "$debug_level_file" ]]; then printf 'Debug level lines:\n'; cat "$debug_level_file"; printf '\n'; else printf 'No ModeU5 DEBUG_LEVEL markers found.\n\n'; fi
if [[ -s "$main_mode_file" ]]; then printf 'Main mode trace lines:\n'; printf 'Mode map: main_mode=1 Active Performance; main_mode=2 Active Normal; main_mode=3 Deactivated.\n'; cat "$main_mode_file"; printf '\n'; else printf 'No ModeU5 PERF-14 main-mode trace lines found.\n\n'; fi
if [[ -s "$perf14_file" ]]; then printf 'PERF-14 diagnostic lines:\n'; cat "$perf14_file"; printf '\n'; else printf 'No non-localization PERF-14 diagnostic lines found.\n\n'; fi
if [[ -s "$us10ui_file" ]]; then printf 'US-10 visibility diagnostic lines:\n'; cat "$us10ui_file"; printf '\n'; else printf 'No non-localization US-10 visibility diagnostic lines found.\n\n'; fi
if [[ -s "$us04_file" ]]; then printf 'US-04 diagnostic lines:\n'; cat "$us04_file"; printf '\n'; else printf 'No non-localization US-04 diagnostic lines found.\n\n'; fi
if [[ -s "$core04_file" ]]; then printf 'CORE-04 topology diagnostic lines:\n'; cat "$core04_file"; printf '\n'; else printf 'No non-localization CORE-04 topology diagnostic lines found.\n\n'; fi

if [[ -s "$scenario_file" ]]; then
	printf 'Scenario lines:\n'
	cat "$scenario_file"
fi

if [[ -s "$incomplete_scenario_file" ]]; then
	printf '\n'
	printf 'Incomplete latest scenario runs:\n'
	while IFS=$'\t' read -r scenario line; do
		printf '%s\n' "$line"
	done <"$incomplete_scenario_file"
fi

if [[ "$expected_mode" != "none" && ${#missing_scenarios[@]} -gt 0 ]]; then
	printf '\n'
	case "$expected_mode" in
		full) printf 'Missing expected full-revalidation scenario markers:\n' ;;
		pr126) printf 'Missing expected PR126 dispatcher scenario markers:\n' ;;
		us04) printf 'Missing expected US-04 focused scenario markers:\n' ;;
		us04-estate) printf 'Missing expected US-04 Estate focused scenario markers:\n' ;;
		none) printf 'Missing expected scenario markers:\n' ;;
	esac
	printf '%s\n' "${missing_scenarios[@]}"
fi

#!/usr/bin/env bash

set -euo pipefail

logs_dir="${MODEU5_LOG_DIR:-${HOME}/Documents/Paradox Interactive/Europa Universalis V/logs}"

if [[ ${1:-} == "--logs-dir" ]]; then
	if (($# < 2)); then
		printf 'Missing path after --logs-dir.\n' >&2
		exit 2
	fi
	logs_dir="$2"
fi

if [[ ! -d "$logs_dir" ]]; then
	printf 'EU5 logs directory does not exist: %s\n' "$logs_dir" >&2
	exit 1
fi

log_files=()
for log_name in debug.log error.log game.log system.log; do
	if [[ -f "$logs_dir/$log_name" ]]; then
		log_files+=("$logs_dir/$log_name")
	fi
done

if ((${#log_files[@]} == 0)); then
	printf 'No EU5 log files found in: %s\n' "$logs_dir" >&2
	exit 1
fi

printf 'US-04 additive injection syntax matrix\n'
printf 'Logs directory: %s\n\n' "$logs_dir"

grep -hE \
	'ModeU5 US-04 INJECTION (CONTROL|CANDIDATE|RESULT|MATRIX SUMMARY|MATRIX RESULT)|ModeU5 TEST (ENTERED|PASS|FAIL|BLOCKED) scenario=us04_pop_demand_injection_matrix' \
	"${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	|| true

printf '\nRelevant loader/parser errors:\n'
grep -hEi \
	'zz_modeu5_us04_probe_|INJECT:pop_demand|TRY_INJECT:pop_demand|INJECT_OR_CREATE:pop_demand|duplicate|duplicated key|database entry|parse error|failed to read' \
	"${log_files[@]}" \
	| grep -v 'Tried to localize with localization disabled' \
	|| true

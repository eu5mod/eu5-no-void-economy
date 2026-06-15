#!/usr/bin/env bash

set -euo pipefail

default_logs_dir="${MODEU5_LOG_DIR:-${HOME}/Documents/Paradox Interactive/Europa Universalis V/logs}"
logs_dir="$default_logs_dir"
dry_run="no"

usage() {
	printf 'Usage: %s [--dry-run] [--logs-dir PATH]\n' "$0"
	printf '\n'
	printf 'Truncates only error.log and game.log in the EU5 logs directory.\n'
	printf 'Close Europa Universalis V before running this command.\n'
	printf 'Default logs directory: %s\n' "$default_logs_dir"
}

while (($# > 0)); do
	case "$1" in
		--dry-run)
			dry_run="yes"
			shift
			;;
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

log_names=(
	"error.log"
	"game.log"
)

for log_name in "${log_names[@]}"; do
	log_file="$logs_dir/$log_name"

	if [[ ! -e "$log_file" ]]; then
		printf 'SKIP     %s (missing)\n' "$log_file"
		continue
	fi
	if [[ ! -f "$log_file" ]]; then
		printf 'Refusing to truncate a non-regular file: %s\n' "$log_file" >&2
		exit 1
	fi

	if [[ "$dry_run" == "yes" ]]; then
		printf 'WOULD CLEAR  %s\n' "$log_file"
	else
		: > "$log_file"
		printf 'CLEARED  %s\n' "$log_file"
	fi
done

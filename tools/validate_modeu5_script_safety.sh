#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v git >/dev/null 2>&1; then
	printf 'git is required for ModeU5 script-safety validation.\n' >&2
	exit 1
fi

failed=0

var_comparison_pattern='(^|[[:space:]{(])var:[A-Za-z0-9_]+[[:space:]]*(=|!=|>=|<=|>|<)[[:space:]]*var:[A-Za-z0-9_]+'
var_comparison_allow_marker='modeu5-allow-var-comparison'

while IFS= read -r file; do
	if [[ ! -f "$file" ]]; then
		continue
	fi
	while IFS= read -r line; do
		if [[ "$line" == *"$var_comparison_allow_marker"* ]]; then
			continue
		fi
		printf '%s\n' "$line" >&2
		failed=1
	done < <(grep -En "$var_comparison_pattern" "$file" || true)
done < <(git ls-files \
	'in_game/**/*.txt' \
	'main_menu/**/*.txt' \
	'packages/**/*.txt')

# Runtime proved on 2026-07-11 that `every_location = {` is rejected as an
# unknown effect from the root/start-game context. Keep it globally banned until
# an engine-safe scoped usage is documented with an explicit allow marker.
forbidden_every_location_allow_marker='modeu5-allow-every-location'
while IFS= read -r file; do
	if [[ ! -f "$file" ]]; then
		continue
	fi
	while IFS= read -r line; do
		if [[ "$line" == *"$forbidden_every_location_allow_marker"* ]]; then
			continue
		fi
		printf '%s\n' "$line" >&2
		failed=1
	done < <(grep -En '^[[:space:]]*every_location[[:space:]]*=\s*\{' "$file" || true)
done < <(git ls-files \
	'in_game/**/*.txt' \
	'main_menu/**/*.txt' \
	'packages/**/*.txt')

if [[ "$failed" -ne 0 ]]; then
	printf '\nModeU5 script-safety validation failed.\n' >&2
	printf 'Do not compare var: values directly against other var: values in limits/assertions; EU5 can reject them as an invalid comparison left side or fail when either variable is unset.\n' >&2
	printf 'Snapshot persistent/current variables into initialized scope: temporary values first, then compare scope: values.\n' >&2
	printf 'Root/global every_location is also banned because EU5 rejected it as an unknown effect in runtime parser validation. Use a proven scoped iterator such as every_owned_location from country scope, or add %s with runtime evidence.\n' "$forbidden_every_location_allow_marker" >&2
	printf 'If a direct var: comparison is intentionally proven safe, add %s on the same line and document the exception.\n' "$var_comparison_allow_marker" >&2
	exit 1
fi

printf 'ModeU5 script-safety validation passed\n'

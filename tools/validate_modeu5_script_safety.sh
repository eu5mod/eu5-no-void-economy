#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v git >/dev/null 2>&1; then
	printf 'git is required for ModeU5 script-safety validation.\n' >&2
	exit 1
fi

pattern='(^|[[:space:]{(])var:[A-Za-z0-9_]+[[:space:]]*(=|!=|>=|<=|>|<)[[:space:]]*var:[A-Za-z0-9_]+'
allow_marker='modeu5-allow-var-comparison'
failed=0

while IFS= read -r file; do
	if [[ ! -f "$file" ]]; then
		continue
	fi
	while IFS= read -r line; do
		if [[ "$line" == *"$allow_marker"* ]]; then
			continue
		fi
		printf '%s\n' "$line" >&2
		failed=1
	done < <(grep -En "$pattern" "$file" || true)
done < <(git ls-files \
	'in_game/**/*.txt' \
	'main_menu/**/*.txt' \
	'packages/**/*.txt')

if [[ "$failed" -ne 0 ]]; then
	printf '\nModeU5 script-safety validation failed.\n' >&2
	printf 'Do not compare var: values directly against other var: values in limits/assertions; EU5 can reject them as an invalid comparison left side or fail when either variable is unset.\n' >&2
	printf 'Snapshot persistent/current variables into initialized scope: temporary values first, then compare scope: values.\n' >&2
	printf 'If a direct var: comparison is intentionally proven safe, add %s on the same line and document the exception.\n' "$allow_marker" >&2
	exit 1
fi

printf 'ModeU5 script-safety validation passed\n'

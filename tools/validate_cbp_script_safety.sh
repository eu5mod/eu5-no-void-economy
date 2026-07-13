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

if ! python3 - <<'PY'
from pathlib import Path
import re
import subprocess
import sys

files = subprocess.check_output(
    [
        "git",
        "ls-files",
        "in_game/**/*.txt",
        "main_menu/**/*.txt",
        "packages/**/*.txt",
        "tools/templates/*.template.txt",
    ],
    text=True,
).splitlines()

failed = False
arithmetic_value = re.compile(r"value\s*=\s*\{[\s\S]*\b(add|subtract|multiply|divide)\s*=")

for file_name in files:
    path = Path(file_name)
    if not path.is_file():
        continue
    lines = path.read_text(errors="ignore").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if "add_to_variable_map" not in line:
            index += 1
            continue

        start_line = index + 1
        block = [line]
        depth = line.count("{") - line.count("}")
        index += 1
        while depth > 0 and index < len(lines):
            block.append(lines[index])
            depth += lines[index].count("{") - lines[index].count("}")
            index += 1

        block_text = "\n".join(block)
        if arithmetic_value.search(block_text):
            print(
                f"{file_name}:{start_line}: add_to_variable_map must receive a scalar/scope value; precompute arithmetic in save_temporary_scope_value_as",
                file=sys.stderr,
            )
            failed = True

    for line_number, line in enumerate(lines, start=1):
        if re.search(r"local_var:cbp_(pr126|perf14|core04)_", line):
            print(
                f"{file_name}:{line_number}: test local variable read is missing the test_cbp_ prefix",
                file=sys.stderr,
            )
            failed = True
        if "local_var:cbp_us10_ui_market_capacity_accumulator" in line:
            print(
                f"{file_name}:{line_number}: UI local variable read is missing the gui_ prefix",
                file=sys.stderr,
            )
            failed = True

if failed:
    sys.exit(1)
PY
then
	failed=1
fi

if [[ "$failed" -ne 0 ]]; then
	printf '\nModeU5 script-safety validation failed.\n' >&2
	printf 'Do not compare var: values directly against other var: values in limits/assertions; EU5 can reject them as an invalid comparison left side or fail when either variable is unset.\n' >&2
	printf 'Snapshot persistent/current variables into initialized scope: temporary values first, then compare scope: values.\n' >&2
	printf 'Do not put arithmetic value blocks directly inside add_to_variable_map; precompute them into a temporary scope value first.\n' >&2
	printf 'Test/UI local variable reads must use the same prefix as the set/change_local_variable name, for example test_cbp_* or gui_cbp_*.\n' >&2
	printf 'Root/global every_location is also banned because EU5 rejected it as an unknown effect in runtime parser validation. Use a proven scoped iterator such as every_owned_location from country scope, or add %s with runtime evidence.\n' "$forbidden_every_location_allow_marker" >&2
	printf 'If a direct var: comparison is intentionally proven safe, add %s on the same line and document the exception.\n' "$var_comparison_allow_marker" >&2
	exit 1
fi

printf 'ModeU5 script-safety validation passed\n'

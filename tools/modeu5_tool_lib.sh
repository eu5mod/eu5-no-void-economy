#!/usr/bin/env bash

# Shared helpers for ModeU5 generators and validators.
#
# Keep this file small and boring. Generators should put business-specific
# parsing in their own scripts, but repository paths, local config loading,
# canonical good registry loading, template rendering, and common validation
# helpers belong here.

if [[ -n "${MODEU5_TOOL_LIB_LOADED:-}" ]]; then
	return 0
fi
MODEU5_TOOL_LIB_LOADED=1

MODEU5_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

modeu5_load_local_config() {
	local local_config="${1:-$MODEU5_REPO_ROOT/.modeu5.local.env}"

	if [[ -f "$local_config" ]]; then
		set -a
		# shellcheck source=/dev/null
		source "$local_config"
		set +a
	fi
}

modeu5_load_goods_registry() {
	# shellcheck source=tools/modeu5_goods.sh
	source "$MODEU5_REPO_ROOT/tools/modeu5_goods.sh"
}

modeu5_require_file() {
	local file="$1"
	if [[ ! -f "$file" ]]; then
		printf 'Required file is missing: %s\n' "$file" >&2
		exit 1
	fi
}

modeu5_make_parent_dir() {
	local path="$1"
	mkdir -p "$(dirname "$path")"
}

modeu5_search_quiet() {
	local pattern="$1"
	shift

	if command -v rg >/dev/null 2>&1; then
		rg -q -- "$pattern" "$@"
	else
		grep -ERq -- "$pattern" "$@"
	fi
}

modeu5_search_lines() {
	local pattern="$1"
	shift

	if command -v rg >/dev/null 2>&1; then
		rg -n -- "$pattern" "$@"
	else
		grep -ERn -- "$pattern" "$@"
	fi
}

modeu5_require_match() {
	local pattern="$1"
	local file="$2"
	local message="$3"

	if ! modeu5_search_quiet "$pattern" "$file"; then
		printf '%s: %s\n' "$message" "$file" >&2
		exit 1
	fi
}

modeu5_render_template_to_stdout() {
	local template="$1"
	shift

	modeu5_require_file "$template"

	python3 - "$template" "$@" <<'PY'
from pathlib import Path
import re
import sys

template = Path(sys.argv[1])
replacements: dict[str, str] = {}

for raw in sys.argv[2:]:
    if "=" not in raw:
        raise SystemExit(f"Template replacement must be KEY=VALUE, got: {raw}")
    key, value = raw.split("=", 1)
    if not re.fullmatch(r"[A-Z0-9_]+", key):
        raise SystemExit(f"Template replacement key must be uppercase snake case, got: {key}")
    replacements[f"__{key}__"] = value

text = template.read_text(encoding="utf-8")
for token, value in replacements.items():
    text = text.replace(token, value)

unresolved = sorted(set(re.findall(r"__[A-Z0-9_]+__", text)))
if unresolved:
    raise SystemExit(
        f"Template {template} still has unresolved placeholders: " + ", ".join(unresolved)
    )

sys.stdout.write(text)
PY
}

modeu5_render_template_to_file() {
	local output="$1"
	local template="$2"
	shift 2

	modeu5_make_parent_dir "$output"
	modeu5_render_template_to_stdout "$template" "$@" > "$output"
}

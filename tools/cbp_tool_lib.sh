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

cbp_console_color_enabled() {
	local fd="${1:-1}"
	[[ "${CBG_COLOR:-auto}" != "never" ]] && \
		[[ -z "${NO_COLOR:-}" ]] && \
		{ [[ "${CBG_COLOR:-auto}" == "always" ]] || [[ -t "$fd" ]]; }
}

cbp_console_styled() {
	local code="$1"
	local text="$2"
	local fd="${3:-1}"
	if cbp_console_color_enabled "$fd"; then
		printf '\033[%sm%s\033[0m' "$code" "$text"
	else
		printf '%s' "$text"
	fi
}

cbp_console_major_separator() {
	cbp_console_styled '1;35' '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' "${1:-1}"
	printf '\n'
}

cbp_console_step_separator() {
	cbp_console_styled '1;36' '────────────────────────────────────────────────────────────────────────' "${1:-1}"
	printf '\n'
}

cbp_console_failure() {
	local message="$1"
	cbp_console_styled '1;31' '[FAILED]' 2 >&2
	printf ' ' >&2
	cbp_console_styled '1;31' "$message" 2 >&2
	printf '\n' >&2
}

cbp_display_path() {
	local input="$1"
	local directory
	local resolved
	local temporary_root
	case "$input" in
		"$MODEU5_REPO_ROOT"/*) printf './%s' "${input#"$MODEU5_REPO_ROOT"/}"; return ;;
		"${TMPDIR:-/tmp}"/*) printf '$TMPDIR/%s' "${input#"${TMPDIR:-/tmp}"/}"; return ;;
		"$HOME"/*) printf '~/%s' "${input#"$HOME"/}"; return ;;
	esac
	directory="$(cd "$(dirname "$input")" 2>/dev/null && pwd -P)" || {
		printf '%s' "$input"
		return
	}
	resolved="$directory/$(basename "$input")"
	temporary_root="$(cd "${TMPDIR:-/tmp}" 2>/dev/null && pwd -P)"
	case "$resolved" in
		"$MODEU5_REPO_ROOT"/*) printf './%s' "${resolved#"$MODEU5_REPO_ROOT"/}" ;;
		"$temporary_root"/*) printf '$TMPDIR/%s' "${resolved#"$temporary_root"/}" ;;
		"$HOME"/*) printf '~/%s' "${resolved#"$HOME"/}" ;;
		*) printf '%s' "$resolved" ;;
	esac
}

cbp_load_local_config() {
	local local_config="${1:-$MODEU5_REPO_ROOT/.cbp.local.env}"

	if [[ -f "$local_config" ]]; then
		set -a
		# shellcheck source=/dev/null
		source "$local_config"
		set +a
	fi
}

cbp_load_goods_registry() {
	# shellcheck source=tools/cbp_goods.sh
	source "$MODEU5_REPO_ROOT/tools/cbp_goods.sh"
}

cbp_require_file() {
	local file="$1"
	if [[ ! -f "$file" ]]; then
		printf 'Required file is missing: %s\n' "$file" >&2
		exit 1
	fi
}

cbp_make_parent_dir() {
	local path="$1"
	mkdir -p "$(dirname "$path")"
}

cbp_search_quiet() {
	local pattern="$1"
	shift

	if command -v rg >/dev/null 2>&1; then
		rg -q -- "$pattern" "$@"
	else
		grep -ERq -- "$pattern" "$@"
	fi
}

cbp_search_lines() {
	local pattern="$1"
	shift

	if command -v rg >/dev/null 2>&1; then
		rg -n -- "$pattern" "$@"
	else
		grep -ERn -- "$pattern" "$@"
	fi
}

cbp_require_match() {
	local pattern="$1"
	local file="$2"
	local message="$3"

	if ! cbp_search_quiet "$pattern" "$file"; then
		printf '%s: %s\n' "$message" "$file" >&2
		exit 1
	fi
}

cbp_render_template_to_stdout() {
	local template="$1"
	shift

	cbp_require_file "$template"

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

cbp_render_template_to_file() {
	local output="$1"
	local template="$2"
	shift 2

	cbp_make_parent_dir "$output"
	cbp_render_template_to_stdout "$template" "$@" > "$output"
}

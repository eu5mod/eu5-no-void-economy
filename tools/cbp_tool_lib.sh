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
	cbp_console_styled '1;36' '#########################################################################' "${1:-1}"
	printf '\n'
}

cbp_console_step_banner() {
	local text="$1"
	local fd="${2:-1}"
	local width=73
	local padding
	local left_padding
	local right_padding
	local hashes
	local left_hashes
	local right_hashes

	if ((${#text} + 2 >= width)); then
		cbp_console_step_separator "$fd"
		cbp_console_styled '1;36' "$text" "$fd"
		printf '\n'
		cbp_console_step_separator "$fd"
		return
	fi

	padding=$((width - ${#text} - 2))
	left_padding=$((padding / 2))
	right_padding=$((padding - left_padding))
	printf -v hashes '%*s' "$width" ''
	printf -v left_hashes '%*s' "$left_padding" ''
	printf -v right_hashes '%*s' "$right_padding" ''
	hashes="${hashes// /#}"
	left_hashes="${left_hashes// /#}"
	right_hashes="${right_hashes// /#}"

	cbp_console_styled '1;36' "$hashes" "$fd"
	printf '\n'
	cbp_console_styled '1;36' "${left_hashes} ${text} ${right_hashes}" "$fd"
	printf '\n'
	cbp_console_styled '1;36' "$hashes" "$fd"
	printf '\n'
}

cbp_console_failure() {
	local message="$1"
	cbp_console_styled '1;31' '[FAILED]' 2 >&2
	printf ' ' >&2
	cbp_console_styled '1;31' "$message" 2 >&2
	printf '\n' >&2
}

cbp_console_warning() {
	local message="$1"
	cbp_console_styled '1;33' '[WARNING]' 2 >&2
	printf ' ' >&2
	cbp_console_styled '1;33' "$message" 2 >&2
	printf '\n' >&2
}

cbp_console_status_badge() {
	local status="$1"
	local fd="${2:-1}"
	case "$status" in
		OK) cbp_console_styled '1;32' '[OK]' "$fd" ;;
		WARNING) cbp_console_styled '1;33' '[WARNING]' "$fd" ;;
		FAILED) cbp_console_styled '1;31' '[FAILED]' "$fd" ;;
		SKIPPED) cbp_console_styled '1;36' '[SKIPPED]' "$fd" ;;
		*) cbp_console_styled '1;37' "[$status]" "$fd" ;;
	esac
}

cbp_console_section_start() {
	local id="$1"
	local title="$2"
	printf '\n'
	cbp_console_step_banner "STEP $id  $title"
}

cbp_console_section_end() {
	local id="$1"
	local status="$2"
	local title="$3"
	local fd=1
	[[ "$status" == "FAILED" ]] && fd=2

	cbp_console_styled '1;36' "└─ [STEP $id]" "$fd"
	printf ' '
	cbp_console_status_badge "$status" "$fd"
	printf ' %s\n' "$title"
}

cbp_console_task_start() {
	local id="$1"
	local title="$2"
	local leading_blank="${3:-yes}"
	[[ "$leading_blank" == "yes" ]] && printf '\n'
	cbp_console_styled '1;36' "┌─ [$id] START" 1
	printf ' '
	cbp_console_styled '1' "$title" 1
	printf '\n'
}

cbp_console_status_symbol() {
	local status="$1"
	local fd="${2:-1}"
	case "$status" in
		OK) cbp_console_styled '1;32' '✅' "$fd" ;;
		WARNING) cbp_console_styled '1;33' '⚠️' "$fd" ;;
		FAILED) cbp_console_styled '1;31' '❌' "$fd" ;;
		SKIPPED) cbp_console_styled '1;36' '⏭' "$fd" ;;
		*) cbp_console_styled '1;37' "$status" "$fd" ;;
	esac
}

cbp_console_task_end() {
	local id="$1"
	local status="$2"
	local title="$3"
	local detail="${4:-}"
	local fd=1
	[[ "$status" == "FAILED" ]] && fd=2

	cbp_console_styled '1;36' "└─ [$id]" "$fd"
	printf ' END '
	cbp_console_status_symbol "$status" "$fd"
	printf ' %s' "$title"
	if [[ -n "$detail" ]]; then
		printf '  (%s)' "$detail"
	fi
	printf '\n'
}

cbp_console_status_record() {
	local id="$1"
	local status="$2"
	local title="$3"
	local detail="${4:-}"
	local status_file="${CBP_CONSOLE_STATUS_FILE:-}"
	[[ -z "$status_file" ]] && return 0

	title="${title//$'\t'/ }"
	title="${title//$'\n'/ }"
	detail="${detail//$'\t'/ }"
	detail="${detail//$'\n'/ }"
	printf '%s\t%s\t%s\t%s\n' "$id" "$status" "$title" "$detail" >> "$status_file"
}

cbp_console_filter_stream() {
	local mode="${1:-compact}"
	case "$mode" in
		full)
			cat
			;;
		quiet)
			awk '
				/\[WARNING\]|\[⚠️\]|^WARNING:|^Warning:|^warning:/ {
					print
					fflush()
				}
			'
			;;
		compact)
			awk '
				/^Generated .*\.json (with|from)/ { next }
				/^Generated \.\// { next }
				/^Reconciled .*\.json with [0-9]+ owned output/ { next }
				/^Manifest: .*\.json$/ { next }
				/^Output: \.\// { next }
				/^Output directory: \// { next }
				/^PURGE[[:space:]]+\// { next }
				/^[[:space:]]+source_path=\// { next }
				/^[[:space:]]+\/.*$/ { next }
				{
					if ($0 == "") {
						if (!blank) {
							print
							fflush()
						}
						blank = 1
					} else {
						print
						fflush()
						blank = 0
					}
				}
			'
			;;
		*)
			printf 'Unknown console output mode: %s\n' "$mode" >&2
			return 2
			;;
	esac
}

cbp_console_run_task() {
	local id="$1"
	local title="$2"
	local output_mode="$3"
	shift 3

	local log_file
	local started_at
	local finished_at
	local elapsed
	local command_status
	local warning_count
	local -a pipeline_status

	log_file="$(mktemp "${TMPDIR:-/tmp}/cbp-console-task.XXXXXX")"
	started_at="$(date +%s)"
	cbp_console_task_start "$id" "$title"

	set +e
	"$@" 2>&1 | tee "$log_file" | cbp_console_filter_stream "$output_mode"
	pipeline_status=("${PIPESTATUS[@]}")
	set -e
	command_status="${pipeline_status[0]}"

	finished_at="$(date +%s)"
	elapsed=$((finished_at - started_at))
	warning_count="$(
		grep -Eic '\[WARNING\]|\[⚠️\]|^WARNING:|^Warning:|^warning:' "$log_file" ||
			true
	)"

	if ((command_status != 0)); then
		cbp_console_task_end "$id" FAILED "$title" "exit $command_status; ${elapsed}s"
		cbp_console_status_record "$id" FAILED "$title" "exit $command_status"
		printf '\nFull diagnostic output for %s:\n' "$id" >&2
		cat "$log_file" >&2
		rm -f "$log_file"
		return "$command_status"
	fi

	if ((warning_count > 0)); then
		cbp_console_task_end "$id" WARNING "$title" "$warning_count warning(s); ${elapsed}s"
		cbp_console_status_record "$id" WARNING "$title" "$warning_count warning(s)"
	else
		cbp_console_task_end "$id" OK "$title" "${elapsed}s"
		cbp_console_status_record "$id" OK "$title"
	fi
	rm -f "$log_file"
}

cbp_check_patch_hygiene() {
	local label="$1"
	shift
	local output
	local diagnostics
	local unsafe
	if output="$("$@" 2>&1)"; then
		return 0
	fi
	diagnostics="$(
		printf '%s\n' "$output" |
			grep -E '^[^+].*:[0-9]+: ' || true
	)"
	unsafe="$(
		printf '%s\n' "$diagnostics" |
			grep -Ev ':[0-9]+: (trailing whitespace\.|space before tab in indent\.|new blank line at EOF\.)$' ||
			true
	)"
	if [[ -z "$diagnostics" || -n "$unsafe" ]]; then
		printf '%s\n' "$output" >&2
		return 1
	fi
	cbp_console_warning "$label has non-blocking whitespace findings:"
	printf '%s\n' "$output" >&2
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

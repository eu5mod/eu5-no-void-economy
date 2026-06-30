#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./tools/normalize_cmm_value_links.sh --check
  ./tools/normalize_cmm_value_links.sh --write

Ensures CMM variable-map value links are written in parser-safe quoted form:

  "variable_map(cmm|flag:<setting>)"
  "global_variable_map(cmm|flag:<setting>)"

The script scans tracked EU5 script files under in_game, main_menu, and
packages. It intentionally ignores docs and localization so examples can
explain both valid and invalid forms.
USAGE
}

mode="${1:---check}"
case "$mode" in
  --check|--write)
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

cd "$(dirname "$0")/.."

has_violation=0
scanned=0

is_scannable_file() {
  case "$1" in
    *.txt|*.gui)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

while IFS= read -r -d '' file; do
  is_scannable_file "$file" || continue
  scanned=$((scanned + 1))

  if [ "$mode" = "--write" ]; then
    perl -0pi -e 's/(?<!")\b((?:global_)?variable_map\(cmm\|flag:[^)]+\))(?!")/"$1"/g' "$file"
    continue
  fi

  matches="$(
    perl -ne 'while (/(?<!")\b((?:global_)?variable_map\(cmm\|flag:[^)]+\))(?!")/g) { print "$.: $1\n" }' "$file"
  )"
  if [ -n "$matches" ]; then
    if [ "$has_violation" -eq 0 ]; then
      cat >&2 <<'HEADER'
Unquoted CMM variable-map value links found.

Use quoted value-link syntax so EU5 parses the expression as a value:

  "variable_map(cmm|flag:<setting>)"
  "global_variable_map(cmm|flag:<setting>)"

Run ./tools/normalize_cmm_value_links.sh --write to normalize locally.

HEADER
    fi
    has_violation=1
    printf '%s\n%s\n' "$file" "$matches" >&2
  fi
done < <(git ls-files -z -- in_game main_menu packages)

if [ "$mode" = "--write" ]; then
  echo "ModeU5 CMM value-link normalization complete"
  exit 0
fi

if [ "$has_violation" -ne 0 ]; then
  exit 1
fi

echo "ModeU5 CMM value-link validation passed (${scanned} tracked files scanned)"

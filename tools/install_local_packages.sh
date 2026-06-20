#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_target="${MODEU5_MOD_DIR:-${HOME}/Documents/Paradox Interactive/Europa Universalis V/mod}"
target_root="$default_target"
action="install"
generator="$repo_root/tools/generate_all.sh"

usage() {
	printf 'Usage: %s [--install|--check] [--target PATH]\n' "$0"
	printf '\n'
	printf 'Publishes the ModeU5 package roots as sibling local mods.\n'
	printf 'Default target: %s\n' "$default_target"
}

while (($# > 0)); do
	case "$1" in
		--install)
			action="install"
			shift
			;;
		--check)
			action="check"
			shift
			;;
		--target)
			if (($# < 2)); then
				printf 'Missing path after --target.\n' >&2
				exit 2
			fi
			target_root="$2"
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

package_ids=(
	"modeu5_core"
	"modeu5_economy_rebalance"
	"modeu5_trade_rebalance"
	"modeu5_war_rebalance"
	"modeu5_core_tests"
)

package_sources=(
	"$repo_root"
	"$repo_root/packages/modeu5_economy_rebalance"
	"$repo_root/packages/modeu5_trade_rebalance"
	"$repo_root/packages/modeu5_war_rebalance"
	"$repo_root/packages/modeu5_core_tests"
)

if [[ "$action" == "install" ]]; then
	"$generator"
fi

source_branch="$(git -C "$repo_root" branch --show-current 2>/dev/null || true)"
source_commit="$(git -C "$repo_root" rev-parse HEAD 2>/dev/null || printf 'unknown')"
source_branch="${source_branch:-detached}"
source_dirty="no"
if [[ -n "$(git -C "$repo_root" status --porcelain 2>/dev/null || true)" ]]; then
	source_dirty="yes"
fi

write_provenance() {
	local destination="$1"
	{
		printf 'source_path=%s\n' "$repo_root"
		printf 'source_branch=%s\n' "$source_branch"
		printf 'source_commit=%s\n' "$source_commit"
		printf 'source_dirty=%s\n' "$source_dirty"
		printf 'installed_at_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
	} > "$destination/MODEU5_SOURCE.txt"
}

ensure_utf8_bom_file() {
	local file="$1"
	local prefix
	local tmp

	prefix="$(LC_ALL=C head -c 3 "$file" | od -An -tx1 | tr -d ' \n')"
	if [[ "$prefix" == "efbbbf" ]]; then
		return 0
	fi

	tmp="$(mktemp)"
	printf '\357\273\277' > "$tmp"
	cat "$file" >> "$tmp"
	mv "$tmp" "$file"
}

normalize_eu5_text_encoding() {
	local destination="$1"
	local file

	while IFS= read -r -d '' file; do
		case "$file" in
			*/.metadata/*|*/MODEU5_SOURCE.txt|*/descriptor.mod)
				continue
				;;
		esac
		ensure_utf8_bom_file "$file"
	done < <(
		find "$destination" -type f \
			\( -name '*.txt' -o -name '*.yml' -o -name '*.gui' \) \
			-print0
	)
}

install_core() {
	local destination="$target_root/modeu5_core"

	mkdir -p "$destination"
	rsync -a --delete --exclude '.DS_Store' "$repo_root/.metadata/" "$destination/.metadata/"
	rsync -a --delete --exclude '.DS_Store' "$repo_root/in_game/" "$destination/in_game/"
	rsync -a --delete --exclude '.DS_Store' "$repo_root/main_menu/" "$destination/main_menu/"
	cp "$repo_root/descriptor.mod" "$destination/descriptor.mod"
	write_provenance "$destination"
	normalize_eu5_text_encoding "$destination"
}

install_companion() {
	local source="$1"
	local destination="$2"

	mkdir -p "$destination"
	rsync -a --delete --exclude '.DS_Store' "$source/" "$destination/"
	write_provenance "$destination"
	normalize_eu5_text_encoding "$destination"
}

check_packages() {
	local failed=0
	local index

	for index in "${!package_ids[@]}"; do
		local package_id="${package_ids[$index]}"
		local destination="$target_root/$package_id"

		if [[ ! -f "$destination/descriptor.mod" ]]; then
			printf 'MISSING  %s\n' "$destination"
			failed=1
			continue
		fi

		local package_name
		package_name="$(sed -n 's/^name="\(.*\)"$/\1/p' "$destination/descriptor.mod")"
		printf 'OK       %-32s %s\n' "$package_id" "$package_name"

		local metadata_file="$destination/.metadata/metadata.json"
		if [[ ! -f "$metadata_file" ]]; then
			printf '         metadata missing: %s\n' "$metadata_file"
			failed=1
		elif ! grep -Eq '"id"[[:space:]]*:' "$metadata_file"; then
			printf '         metadata missing id: %s\n' "$metadata_file"
			failed=1
		fi

		if [[ -f "$destination/MODEU5_SOURCE.txt" ]]; then
			sed 's/^/         /' "$destination/MODEU5_SOURCE.txt"
		else
			printf '         source provenance missing\n'
			failed=1
		fi

		while IFS= read -r -d '' file; do
			if [[ "$(LC_ALL=C head -c 3 "$file" | od -An -tx1 | tr -d ' \n')" != "efbbbf" ]]; then
				printf '         missing UTF-8 BOM in installed EU5 text file: %s\n' "$file"
				failed=1
			fi
		done < <(
			find "$destination" -type f \
				\( -name '*.txt' -o -name '*.yml' -o -name '*.gui' \) \
				! -path '*/.metadata/*' \
				! -name 'MODEU5_SOURCE.txt' \
				-print0
		)
	done

	while IFS= read -r -d '' metadata_file; do
		if grep -q 'ModeU5 Country Stocks Within Markets' "$metadata_file" && \
			! grep -Eq '"id"[[:space:]]*:' "$metadata_file"; then
			printf 'STALE    ModeU5 metadata without id may still be visible to the launcher: %s\n' \
				"$metadata_file"
			failed=1
		fi
	done < <(find "$target_root" -maxdepth 4 -path '*/.metadata/metadata.json' -type f -print0 2>/dev/null)

	return "$failed"
}

if [[ "$action" == "check" ]]; then
	check_packages
	exit $?
fi

if ! command -v rsync >/dev/null 2>&1; then
	printf 'rsync is required to install the local package set.\n' >&2
	exit 1
fi

mkdir -p "$target_root"
install_core

for index in 1 2 3 4; do
	install_companion \
		"${package_sources[$index]}" \
		"$target_root/${package_ids[$index]}"
done

printf 'Installed the ModeU5 packages in:\n  %s\n\n' "$target_root"
check_packages

if [[ -e "$target_root/eu5voideco" ]]; then
	printf '\nOlder single-package path detected: %s\n' "$target_root/eu5voideco"
	printf 'If the launcher shows two "No Void Economy" entries, disable the one backed by eu5voideco.\n'
fi

printf '\nRefresh the launcher, add the four campaign ModeU5 entries to one playset, and enable the test package only for deterministic validation sessions.\n'

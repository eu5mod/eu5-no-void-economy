#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mode="generate"
if [[ "${1:-}" == "--check" ]]; then
	mode="check"
fi

asset_roots=(
	"docs/assets"
	"in_game/gfx/interface/illustrations"
)

require_command() {
	local command_name="$1"
	if ! command -v "$command_name" >/dev/null 2>&1; then
		printf 'Required command not found: %s\n' "$command_name" >&2
		exit 1
	fi
}

select_imagemagick() {
	if command -v magick >/dev/null 2>&1; then
		printf '%s\n' magick
	elif command -v convert >/dev/null 2>&1; then
		printf '%s\n' convert
	else
		printf '%s\n' "ImageMagick not found. Install ImageMagick so SVG raster output can be converted to DDS." >&2
		exit 1
	fi
}

asset_format() {
	local path="$1"
	local ext="${path##*.}"
	ext="$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')"

	case "$ext" in
		svg|svgz) printf '%s\n' svg ;;
		png) printf '%s\n' png ;;
		jpg|jpeg) printf '%s\n' jpg ;;
		dds)
			if [[ "$(LC_ALL=C head -c 4 "$path" 2>/dev/null || true)" == "DDS " ]]; then
				printf '%s\n' dds
			else
				printf '%s\n' unknown
			fi
			;;
		*) printf '%s\n' unknown ;;
	esac
}

append_output_targets() {
	local source="$1"
	local targets_file="$2"
	local adjacent_output="${source%.*}.dds"

	printf '%s\n' "$adjacent_output" >> "$targets_file"

	case "$source" in
		docs/assets/pr157/review_popup_1524_event_source.*)
			printf '%s\n' "in_game/gfx/interface/illustrations/modeu5_review/modeu5_review_popup_1524_event.dds" >> "$targets_file"
			;;
	esac
}

require_command rsvg-convert
imagemagick_cmd="$(select_imagemagick)"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

sources_file="$tmp_dir/sources.txt"
: > "$sources_file"

for assets_root in "${asset_roots[@]}"; do
	if [[ ! -d "$assets_root" ]]; then
		printf 'No %s directory found; skipping.\n' "$assets_root"
		continue
	fi
	find "$assets_root" \
		-type f \
		! -path 'docs/assets/pr157/source/*' \
		\( -iname '*.svg' -o -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) \
		| sort >> "$sources_file"
done

if [[ ! -s "$sources_file" ]]; then
	printf '%s\n' "No SVG/PNG/JPG source assets found under configured asset roots."
	exit 0
fi

while IFS= read -r source; do
	format="$(asset_format "$source")"
	case "$format" in
		svg|png|jpg) ;;
		*)
			printf 'Skipping unsupported source asset: %s\n' "$source" >&2
			continue
			;;
	esac

	png_tmp="$tmp_dir/$(basename "${source%.*}").png"

	if [[ "$format" == "svg" ]]; then
		rsvg-convert "$source" -o "$png_tmp"
	elif [[ "$format" == "png" ]]; then
		cp "$source" "$png_tmp"
	else
		"$imagemagick_cmd" "$source" "$png_tmp"
	fi

	targets_file="$tmp_dir/$(basename "${source%.*}").targets"
	: > "$targets_file"
	append_output_targets "$source" "$targets_file"

	while IFS= read -r output; do
		mkdir -p "$(dirname "$output")"

		# ImageMagick writes DDS files from the raster PNG. The dds:compression define
		# is accepted by modern ImageMagick builds; older builds may fall back to an
		# uncompressed DDS while still preserving the required DDS container.
		if "$imagemagick_cmd" "$png_tmp" -define dds:compression=dxt5 "$output"; then
			:
		else
			printf 'DDS conversion failed for %s -> %s\n' "$source" "$output" >&2
			exit 1
		fi

		if [[ "$(LC_ALL=C head -c 4 "$output" 2>/dev/null || true)" != "DDS " ]]; then
			printf 'Generated file is not a DDS container: %s\n' "$output" >&2
			exit 1
		fi

		printf 'Generated %s from %s\n' "$output" "$source"
	done < "$targets_file"
done < "$sources_file"

if [[ "$mode" == "check" ]]; then
	status="$(git status --porcelain -- "${asset_roots[@]}" || true)"
	if [[ -n "$status" ]]; then
		printf '%s\n' 'DDS assets are missing or stale. Run tools/generate_dds_assets.sh and commit the generated .dds files.' >&2
		printf '%s\n' "$status" >&2
		exit 1
	fi
fi

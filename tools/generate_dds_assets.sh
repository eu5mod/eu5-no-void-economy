#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mode="generate"
if [[ "${1:-}" == "--check" ]]; then
	mode="check"
fi

assets_root="docs/assets"
if [[ ! -d "$assets_root" ]]; then
	printf '%s\n' "No $assets_root directory found; nothing to generate."
	exit 0
fi

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

require_command rsvg-convert
imagemagick_cmd="$(select_imagemagick)"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

mapfile -t sources < <(find "$assets_root" -type f \( -iname '*.svg' -o -iname '*.png' \) | sort)

if [[ "${#sources[@]}" -eq 0 ]]; then
	printf '%s\n' "No SVG/PNG source assets found under $assets_root."
	exit 0
fi

for source in "${sources[@]}"; do
	format="$(asset_format "$source")"
	case "$format" in
		svg|png) ;;
		*)
			printf 'Skipping unsupported source asset: %s\n' "$source" >&2
			continue
			;;
	esac

	output="${source%.*}.dds"
	mkdir -p "$(dirname "$output")"
	png_tmp="$tmp_dir/$(basename "${source%.*}").png"

	if [[ "$format" == "svg" ]]; then
		rsvg-convert "$source" -o "$png_tmp"
	else
		cp "$source" "$png_tmp"
	fi

	# ImageMagick writes DDS files from the raster PNG. The dds:compression define
	# is accepted by modern ImageMagick builds; older builds may fall back to an
	# uncompressed DDS while still preserving the required DDS container.
	if "$imagemagick_cmd" "$png_tmp" -define dds:compression=dxt5 "$output"; then
		:
	else
		printf 'DDS conversion failed for %s\n' "$source" >&2
		exit 1
	fi

	if [[ "$(LC_ALL=C head -c 4 "$output" 2>/dev/null || true)" != "DDS " ]]; then
		printf 'Generated file is not a DDS container: %s\n' "$output" >&2
		exit 1
	fi

	printf 'Generated %s from %s\n' "$output" "$source"
done

if [[ "$mode" == "check" ]]; then
	# DDS previews are generated artifacts. Only fail when generation dirties
	# tracked files; missing ignored DDS previews should not block pull requests.
	status="$(git status --porcelain --untracked-files=no -- "$assets_root" || true)"
	if [[ -n "$status" ]]; then
		printf '%s\n' 'Tracked DDS assets are stale. Run tools/generate_dds_assets.sh and commit the tracked updates.' >&2
		printf '%s\n' "$status" >&2
		exit 1
	fi
fi

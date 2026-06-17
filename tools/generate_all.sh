#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$repo_root/tools/generate_stock_good_helpers.sh"

if [[ -x "$repo_root/tools/generate_us09_economy_overrides.sh" ]]; then
	"$repo_root/tools/generate_us09_economy_overrides.sh" "${MODEU5_US09_BONUS_PERCENT:-5}"
fi

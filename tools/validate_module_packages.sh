#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
core_validator="$repo_root/tools/validate_module_packages_core.sh"
patched_validator="$(mktemp "${TMPDIR:-/tmp}/cbp-module-validator.XXXXXX.sh")"
trap 'rm -f "$patched_validator"' EXIT

python3 - "$core_validator" "$patched_validator" "$repo_root" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
repo_root = Path(sys.argv[3])
text = source.read_text(encoding="utf-8")

root_anchor = 'repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"'
if root_anchor not in text:
    raise SystemExit(f"Package-validator migration anchor is missing: {root_anchor}")
text = text.replace(root_anchor, f'repo_root="{repo_root}"', 1)

building_root = repo_root / "packages/cbp_economy_rebalance/in_game/common/building_types"
prefixed_trade = building_root / "cbp_trade_buildings.txt"
prefixed_market = building_root / "cbp_market_buildings.txt"
using_replace_outputs = prefixed_trade.is_file() or prefixed_market.is_file()

if using_replace_outputs:
    if not prefixed_trade.is_file() or not prefixed_market.is_file():
        raise SystemExit(
            "Incomplete CBG building migration: both cbp_trade_buildings.txt and "
            "cbp_market_buildings.txt must be present"
        )
    replacements = {
        'in_game/common/building_types/trade_buildings.txt"':
            'in_game/common/building_types/cbp_trade_buildings.txt"',
        'in_game/common/building_types/market_buildings.txt"':
            'in_game/common/building_types/cbp_market_buildings.txt"',
        'rf"^{re.escape(name)}\\s*=\\s*\\{{"':
            'rf"^(?:REPLACE:)?{re.escape(name)}\\s*=\\s*\\{{"',
        'r"^\\s*([A-Za-z0-9_]+)\\s*=\\s*\\{"':
            'r"^\\s*(?:REPLACE:)?([A-Za-z0-9_]+)\\s*=\\s*\\{"',
        'US-09 static overrides must preserve vanilla file paths; remove stale duplicate-key files:':
            'Remove obsolete pre-CBG US-09 duplicate-key files:',
    }
    for old, new in replacements.items():
        if old not in text:
            raise SystemExit(f"Package-validator migration anchor is missing: {old}")
        text = text.replace(old, new)

    anchor = '''require_file "$us09_market_buildings_file"\n'''
    addition = '''require_file "$us09_market_buildings_file"\nrequire_match '^REPLACE:marketplace = \\{$' \\\n\t"$us09_trade_buildings_file" \\\n\t'US-09 trade-building override must package marketplace as a REPLACE entry'\nrequire_match '^REPLACE:market_warehouse = \\{$' \\\n\t"$us09_market_buildings_file" \\\n\t'US-09 market-building override must package market_warehouse as a REPLACE entry'\n'''
    if anchor not in text:
        raise SystemExit("Package-validator building require_file anchor is missing")
    text = text.replace(anchor, addition, 1)

destination.write_text(text, encoding="utf-8")
PY

bash "$patched_validator"

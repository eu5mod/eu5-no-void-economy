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
repo_root = sys.argv[3]
text = source.read_text(encoding="utf-8")

replacements = {
    'repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"':
        f'repo_root="{repo_root}"',
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

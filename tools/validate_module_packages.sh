#!/usr/bin/env bash
set -euo pipefail

# The delegated core runs tools/validate_us08_building_maintenance_overrides.py
# whenever an installed Vanilla common directory and generated building outputs
# are available.
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
legacy_trade = building_root / "trade_buildings.txt"
legacy_market = building_root / "market_buildings.txt"

prefixed_present = [path for path in (prefixed_trade, prefixed_market) if path.is_file()]
legacy_present = [path for path in (legacy_trade, legacy_market) if path.is_file()]

if prefixed_present and len(prefixed_present) != 2:
    raise SystemExit(
        "Incomplete CBG building generation: both cbp_trade_buildings.txt and "
        "cbp_market_buildings.txt must be present"
    )
if legacy_present:
    rendered = ", ".join(path.name for path in legacy_present)
    raise SystemExit(
        "Obsolete full-file building override(s) remain after REPLACE migration: "
        + rendered
    )

using_replace_outputs = len(prefixed_present) == 2

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

if using_replace_outputs:
    anchor = '''require_file "$us09_market_buildings_file"\n'''
    addition = '''require_file "$us09_market_buildings_file"\nrequire_match '^REPLACE:marketplace = \\{$' \\
\t"$us09_trade_buildings_file" \\
\t'US-09 trade-building override must package marketplace as a REPLACE entry'\nrequire_match '^REPLACE:market_warehouse = \\{$' \\
\t"$us09_market_buildings_file" \\
\t'US-09 market-building override must package market_warehouse as a REPLACE entry'\n'''
    if anchor not in text:
        raise SystemExit("Package-validator building require_file anchor is missing")
    text = text.replace(anchor, addition, 1)
else:
    # A clean checkout intentionally has no Vanilla-derived building artifacts.
    # Keep validating all source-owned package files, but skip checks whose only
    # input is a locally generated cbp_ building file.
    required = '''require_file "$us09_trade_buildings_file"\nrequire_file "$us09_market_buildings_file"\n'''
    if required not in text:
        raise SystemExit("Package-validator clean-state require_file anchor is missing")
    text = text.replace(required, "", 1)

    trade_start = 'us09_trade_capacity_percent="$(\n\tpython3 - "$us09_trade_buildings_file" <<\'PY\'\n'
    market_start = 'python3 - "$us09_market_buildings_file" <<\'PY\'\n'
    after_buildings = "require_match '^[[:space:]]+local_max_rgo_size = 1$' \\\n"
    trade_index = text.find(trade_start)
    market_index = text.find(market_start, trade_index + 1)
    after_index = text.find(after_buildings, market_index + 1)
    if min(trade_index, market_index, after_index) < 0:
        raise SystemExit("Package-validator generated-building block anchors are missing")
    text = text[:trade_index] + text[after_index:]

    validator_condition = (
        'if [[ -n "${EU5_GAME_COMMON_DIR:-}" && '
        '-d "${EU5_GAME_COMMON_DIR:-}/building_types" ]]; then'
    )
    if validator_condition not in text:
        raise SystemExit("Package-validator US-08 condition anchor is missing")
    text = text.replace(validator_condition, "if false; then", 1)

destination.write_text(text, encoding="utf-8")
PY

bash "$patched_validator"

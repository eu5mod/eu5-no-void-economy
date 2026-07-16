#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${EU5_GAME_COMMON_DIR:?Set EU5_GAME_COMMON_DIR to the Vanilla in_game/common directory}"

game_root="${EU5_GAME_COMMON_DIR%/in_game/common}"
package_root="$repo_root/packages/cbp_economy_rebalance"
spec="$package_root/cbp_generated/cbg_building_cost_reconciliation_spec.json"
manifest="$package_root/cbp_generated/cbg_building_cost_reconciliation_manifest.json"

python3 "$repo_root/tools/cbg/adapters/cbp/generate_cbp_cbg_building_cost_reconciliation.py" \
  --game-root "$game_root" \
  --package-root "$package_root" \
  --output "$spec" \
  --factor "${MODEU5_BUILDING_COST_RECONCILIATION_FACTOR:-1.5}"

python3 "$repo_root/tools/cbg/adapters/cbp/helpers/bootstrap_cbg_manifest_from_git.py" \
  --spec "$spec" \
  --output-root "$package_root" \
  --manifest "$manifest"

python3 "$repo_root/tools/cbg/community_balance_generator.py" \
  --game-root "$game_root" \
  --spec "$spec" \
  --output-root "$package_root" \
  --manifest "$manifest" \
  --adopt-identical-output

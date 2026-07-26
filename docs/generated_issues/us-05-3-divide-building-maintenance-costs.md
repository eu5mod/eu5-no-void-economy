# US-05.3 / US-08 — Reduce building maintenance quantities

Labels: `module:economy`, `static-override`, `generator`

GitHub issue: #171

## Functional objective

When the Rebalance Economy package is loaded, vanilla building maintenance
production methods should consume less than their vanilla maintenance quantity:

```txt
non-trade building maintenance = vanilla_maintenance_quantity * 0.7
trade-category building maintenance = vanilla_maintenance_quantity * 0.5
```

This is a static building-definition override. It does not add a monthly pulse,
runtime CMM toggle, stock mutation, or vanilla-file edit.

## Package boundary

```txt
Package: Rebalance Economy
Activation: launcher/playset package selection
Behavior when absent: vanilla building maintenance quantities remain unchanged
```

The implementation is composed into the Economy building-source generator
because US-07, US-08/US-05.3, US-09, and US-177 can all touch the same Vanilla
source. Maintenance changes are structural and therefore promote the complete
Vanilla source file to exact-path ownership. A source with modifier-only changes
may instead produce sparse additive injections. This avoids competing static
overrides. Complete `REPLACE:<building>` objects were rejected after runtime
reported duplicate production-method registrations for reused nested keys.

## Implementation rule

- Read vanilla `game/in_game/common/building_types/*.txt` as source input.
- Identify explicit `category = building_maintenance` production-method blocks.
- Inside those blocks, multiply ModeU5-covered good quantities by `0.7`.
- If the enclosing building has `category = trade_category`, use `0.5`
  instead. This covers marketplaces and other trade buildings.
- Preserve zero as zero and preserve the sign of unusual negative quantities.
- Leave construction demand, production output, employment, estate power,
  merchant capacity, RGO size, and unrelated numeric fields unchanged unless an
  approved composed story owns that field.
- Keep the composed US-07 and US-09 transformations in the same generator.
- Do not hand-edit generated building override files.

## Validation

Static validation compares generated package outputs against the local vanilla
source when `EU5_GAME_COMMON_DIR` is configured:

```bash
python3 tools/validate_us08_building_maintenance_overrides.py \
  --common-dir "$EU5_GAME_COMMON_DIR" \
  --package-common-dir packages/cbp_economy_rebalance/in_game/common \
  --us09-percent "${MODEU5_US09_BONUS_PERCENT:-10}" \
  --maintenance-multiplier 0.7 \
  --trade-building-maintenance-multiplier 0.5
```

The validator proves:

- every structurally changed Vanilla maintenance source has a complete
  exact-path output;
- every maintenance-changed building is present once in that complete source;
- modifier-only buildings may be emitted once as sparse `INJECT:<building>`
  objects containing exact `target - Vanilla` deltas;
- no CBP-prefixed structural building file exists;
- no production-method container uses a nested `REPLACE:` or `INJECT:` prefix;
- every non-trade maintenance-good quantity is exactly `source * 0.7`;
- every trade-category maintenance-good quantity is exactly `source * 0.5`;
- the generated body matches the shared transformer used by the generator.

## Test protocol

```bash
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/validate_cbp_script_safety.sh
./tools/audit_cbp_persistent_state.sh
./tools/normalize_cmm_value_links.sh --check
python3 tools/validate_ci_static_contracts.py
python3 tools/validate_cmm_configuration.py
git diff --check
```

Runtime validation must confirm that the generated exact-path sources
load without duplicate building keys, duplicated production-method names, or
unexpected-token errors in `error.log`.

# TEST — US-17 modifier refresh lifecycle and runtime constants

## Static validation

```bash
python3 tools/validate_us17_modifier_refresh_lifecycle.py
```

Expected:

```txt
US17 modifier refresh lifecycle validation passed: named runtime constants and promoted-market guards verified; 8 trade-efficiency privileges covered in Core and Economy package
```

## Installation boundary

Regenerate and reinstall the complete package, then fully restart EU5. Script-value and database replacement files must not be validated through a partial hot reload or an old deployed mod directory.

```bash
./tools/generate_all.sh
./tools/install_local_packages.sh
```

## Existing v7 save affected by zero-valued custom Defines

1. Load the affected save.
2. Advance one in-game day.
3. Confirm the country has:

```txt
cbp_us17_native_modifier_state_version = 7
cbp_us17_runtime_constant_source_version = 1
```

4. Confirm the persisted route-loss coefficient is non-zero. With reconstructed non-CBP Selling Efficiency `S = 0`, it must be `0.05`.
5. Confirm effective Selling is `-0.05` when `S = 0`.
6. Confirm Merchant Maintenance follows the mixed denominator rather than remaining exactly `-M` or zero solely because the custom Define inputs vanished.
7. Advance through the next monthly country pulse and confirm the values do not drift.

## Focused arithmetic and live-application probe

Run the exact current event name (`cbp`, not `cbd`):

```txt
event cbp_us17_owner_modifiers.1
```

Wait one in-game day for the hidden continuation.

Expected final marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 selling_shared_coefficient=verified mixed_denominator_formula=verified import_export_price_effect=zero route_money_delta=zero proportional_goods_loss=verified idempotence=passed live_auto_modifier_application=passed cmm_gate=open
```

None of these assertions may appear:

```txt
shared_coefficient_calculated_upstream
selling_correction_uses_shared_coefficient
maintenance_vanilla_half_term
maintenance_directional_five_term
mixed_denominator_formula
mixed_denominator_maintenance_target
mixed_denominator_maintenance_correction
selling_effective_shared_residual
us20_trade_volume_times_persisted_coefficient
```

## Current-save no-op

1. Save a campaign after the runtime constant source marker has reached `1`.
2. Reload it and advance one day.
3. Confirm the global migration does not rewrite already-current country state.
4. Confirm the ordinary monthly refresh remains idempotent.

## Privilege activation and revocation

Use a country able to activate one of the covered trade-efficiency privileges.

1. Record the four vanilla source modifiers and the four persisted US-17 corrections.
2. Grant the privilege.
3. Confirm `cbp_us17_native_modifier_refresh_scheduled` is set.
4. Advance one day.
5. Confirm the scheduled marker is removed and the relevant US-17 baseline/correction reflects the granted privilege.
6. Revoke the privilege.
7. Confirm the marker is scheduled again.
8. Advance one day and confirm the removed privilege no longer contributes to the reconstructed baseline.

## Monthly promoted-market regression

Advance through a monthly pulse and inspect `error.log`. The following errors must be absent:

```txt
Event target link 'scope' returned an unset scope
cbp_promoted_market_cycle_effects.txt:653
Value of wrong type in cbp_promoted_market_cycle_effects.txt:649
```

This is a separate diagnostic-counter regression test; it is not part of the US-17 arithmetic result.

# TEST — US-17 modifier refresh lifecycle

## Static validation

```bash
python3 tools/validate_us17_modifier_refresh_lifecycle.py
```

Expected:

```txt
US17 modifier refresh lifecycle validation passed: 8 trade-efficiency privileges covered in Core and Economy package
```

## Existing-save migration

1. Load a save created before US-17 modifier state version `7`.
2. Advance one in-game day.
3. Confirm each migrated country has `cbp_us17_native_modifier_state_version = 7`.
4. For a country whose vanilla Selling, Import, Export, and Merchant Maintenance inputs are all zero, confirm effective Selling is `-0.05`, Import is `0`, Export is `0`, and Merchant Maintenance is `0`.
5. Advance through the next monthly country pulse and confirm the values do not drift.

## Current-save no-op

1. Save a campaign after countries have reached state version `7`.
2. Reload it and advance one day.
3. Confirm the global migration does not rewrite already-v7 country state.
4. Confirm the ordinary monthly refresh still remains idempotent.

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

The existing focused PR #204 probe remains authoritative for the formula and live auto-modifier application:

```txt
event cbp_us17_owner_modifiers.1
```

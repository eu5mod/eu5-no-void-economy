# US-17 modifier refresh lifecycle

## Purpose

US-17 stores reconstructed non-CBP modifier baselines and CBP correction values on each country. Those variables must be recalculated when a save first adopts state version `7` and when an estate privilege changes one of the source modifiers.

The authoritative calculation remains `cbp_refresh_us17_native_profit_modifiers_for_current_country` from PR #204. This lifecycle layer only decides when that calculation must run.

## Game start and save load

Both `on_game_start` and `on_game_load` schedule a migration after one day. The delayed global dispatcher visits every country but refreshes only when:

```txt
cbp_us17_native_modifier_state_version is absent
or
cbp_us17_native_modifier_state_version < 7
```

Countries already on version `7` are not recalculated by the global migration. The normal monthly country refresh remains the fallback for later research, temporary modifiers, conditional modifier blocks, and sources without a dedicated lifecycle hook.

## Estate privilege activation and revocation

EU5 estate privileges expose `on_activate` and `on_deactivate`. Core and Economy-package database-injection files add those effects without replacing the original privilege definitions. The package-local file sorts after the full Burghers and Nobles overrides, preserving the hooks in both modular and combined installations.

The injections cover every privilege in the current CBP Burghers and Nobles privilege files that contains one of:

```txt
selling_efficiency
import_efficiency
export_efficiency
merchant_maintenance_efficiency
```

Activation or revocation calls `cbp_schedule_us17_native_profit_modifier_refresh`. Same-day requests are coalesced through `cbp_us17_native_modifier_refresh_scheduled`, then a hidden country event performs the refresh one day later. Waiting one day ensures the privilege modifier has reached the live country modifier surfaces before US-17 reconstructs its baselines.

Conditional modifier blocks inside an already-active privilege can change without activating or revoking the privilege. Those cases continue to rely on the monthly fallback.

## Validation

Run:

```bash
python3 tools/validate_us17_modifier_refresh_lifecycle.py
```

The validator derives the expected injection set from the current Burghers and Nobles privilege files, then requires identical Core and Economy-package coverage. CI fails when a new privilege adds a US-17 source modifier without both activation and deactivation hooks.

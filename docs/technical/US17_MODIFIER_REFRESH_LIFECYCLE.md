# US-17 modifier refresh lifecycle and runtime source

## Purpose

US-17 stores reconstructed non-CBP modifier baselines and CBP correction values on each country. Those variables must be recalculated when a save first adopts state version `7`, when the runtime constant source changes, and when an estate privilege changes one of the source modifiers.

The authoritative refresh remains `cbp_refresh_us17_native_profit_modifiers_for_current_country`. The production calculation and source-version marker now live directly in `cbp_trade_owner_modifier_reconciliation_effects.txt`; there is no secondary calculation override.

## Runtime constant correction

The initial PR #204 implementation added arbitrary `CBP_*` keys under `NCountry` and read them through `define:NCountry|...`. In the focused game probe those custom keys resolved as zero. This produced the observed failure pattern:

```txt
shared Selling coefficient = 0
Selling correction = -S
M/2 term = 0
5*(I+Ex) term = 0
mixed-denominator maintenance = 0
```

Direct Import and Export cancellation still worked because those calculations did not use the custom Define keys.

The authoritative runtime implementation now reads named script values directly:

```txt
cbp_us17_us20_route_loss_coefficient_max = 0.05
cbp_us17_us20_route_loss_coefficient_curve = 10
cbp_us17_maintenance_component_weight = 0.5
cbp_us17_maintenance_efficiency_scale = 10
```

The algebra is unchanged:

```txt
C = 0.05 / (1 + 10*S)
M_effective = 1 - 1 / (1 + 0.5*M + 10*0.5*(I+Ex))
```

A country refreshed from this source receives:

```txt
cbp_us17_runtime_constant_source_version = 1
```

The obsolete custom Define entries, compatibility aliases, and `zz_cbp_us17_runtime_constant_replacements.txt` have been removed.

## Game start and save load

Both `on_game_start` and `on_game_load` schedule a migration after one day. The delayed global dispatcher refreshes a country when any of these conditions is true:

```txt
cbp_us17_native_modifier_state_version is absent
cbp_us17_native_modifier_state_version < 7
cbp_us17_runtime_constant_source_version is absent
cbp_us17_runtime_constant_source_version < 1
```

The extra source marker is required because an affected save may already report state version `7` even though its values were calculated with zero-valued custom Defines.

The normal monthly country refresh remains the fallback for later research, temporary modifiers, conditional modifier blocks, and sources without a dedicated lifecycle hook.

## Estate privilege activation and revocation

EU5 estate privileges expose `on_activate` and `on_deactivate`. Core and Economy-package database-injection files add those effects without replacing the original privilege definitions. The package-local file sorts after the full Burghers and Nobles overrides, preserving the hooks in both modular and combined installations.

The injections cover every privilege in the current CBP Burghers and Nobles privilege files that contains one of:

```txt
selling_efficiency
import_efficiency
export_efficiency
merchant_maintenance_efficiency
```

Activation or revocation calls `cbp_schedule_us17_native_profit_modifier_refresh`. Same-day requests are coalesced through `cbp_us17_native_modifier_refresh_scheduled`, then a hidden country event performs the refresh one day later.

Conditional modifier blocks inside an already-active privilege can change without activating or revoking the privilege. Those cases continue to rely on the monthly fallback.

## Promoted-market diagnostic guard

The monthly error at `cbp_promoted_market_cycle_effects.txt:649-653` is independent of the US-17 formula. It comes from diagnostic counters reading an absent zero-valued global or an unset generated good-count target. The separate promoted-market metric replacements initialize the globals safely and skip the diagnostic good-scan increment when the target is unavailable. These counters must never interrupt the economy cycle.

## Focused runtime event

The exact current event name is:

```txt
event cbp_us17_owner_modifiers.1
```

The prefix is `cbp`, not `cbd`. Wait one in-game day for the hidden live-auto-modifier continuation.

## Validation

Run:

```bash
python3 tools/validate_us17_modifier_refresh_lifecycle.py
```

The validator now requires:

- named runtime constants consumed by the direct production effects;
- no arbitrary `CBP_*`/`CBD_*` custom Defines;
- no duplicate US-17 runtime replacement layer;
- the runtime-source migration marker in the direct clear and refresh effects;
- guarded promoted-market diagnostic counters;
- identical Core and Economy-package privilege lifecycle coverage.

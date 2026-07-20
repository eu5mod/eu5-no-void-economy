# US-17 — Modifier refresh lifecycle and runtime source

## Objective

Ensure the persisted US-17 country baselines and corrections are calculated from valid runtime constants and recalculated when their source state changes outside the normal monthly fallback.

## Runtime defect confirmed in game

The initial implementation read arbitrary custom `CBP_*` keys through `define:NCountry|...`. The focused probe showed those values resolving as zero. Direct Import and Export cancellation passed, while every Selling and Merchant Maintenance assertion depending on those custom keys failed.

The accepted formula is retained through named script values:

```txt
C_max = 0.05
C_curve = 10
maintenance_component_weight = 0.5
maintenance_efficiency_scale = 10
```

## Lifecycle contract

```txt
new game or save load, delayed one day
  -> every country missing state version 7
     or below state version 7
     or missing runtime constant source version 1
     or below runtime constant source version 1
  -> refresh US-17

covered trade-efficiency privilege activated or revoked
  -> coalesce same-day requests
  -> delayed country refresh after one day

monthly country pulse
  -> unchanged authoritative fallback
```

## Save compatibility

The migration preserves previous correction variables long enough for the refresh to reconstruct the non-CBP baselines. It must not clear the old values before reconstruction.

A country calculated from the valid named script-value source receives:

```txt
cbp_us17_runtime_constant_source_version = 1
```

State version `7` alone is insufficient because an affected save may already have v7 state calculated with zero-valued custom Defines.

## Privilege coverage

The injection set is derived from the current Burghers and Nobles privilege files. Any privilege containing one of these modifier keys requires both activation and deactivation scheduling hooks:

```txt
selling_efficiency
import_efficiency
export_efficiency
merchant_maintenance_efficiency
```

Database injection is required; the original privilege definitions must not be replaced solely to add lifecycle effects.

## Promoted-market diagnostic boundary

The unset scope at `cbp_promoted_market_cycle_effects.txt:653` is independent of the US-17 formula. Diagnostic counters must initialize absent zero-valued globals safely and skip the good-scan increment when the generated count target is unavailable.

## Focused event

```txt
event cbp_us17_owner_modifiers.1
```

The namespace prefix is `cbp`, not `cbd`. Wait one in-game day for the live auto-modifier continuation.

## Acceptance criteria

```txt
- no executable runtime replacement reads define:NCountry|CBP_*;
- named script values reproduce C=0.05/(1+10*S);
- named script values reproduce M_effective=1-1/(1+M/2+5*(I+Ex));
- game start/load refreshes missing, pre-v7, and pre-runtime-source countries;
- current v7/source-v1 countries are skipped by global migration;
- relevant privilege activation and revocation schedule one delayed refresh;
- multiple same-day requests are coalesced per country;
- monthly refresh remains the fallback for conditional and temporary sources;
- promoted-market diagnostic counters cannot emit the reported unset-scope error;
- CI derives privilege injection coverage and validates runtime-source guards.
```

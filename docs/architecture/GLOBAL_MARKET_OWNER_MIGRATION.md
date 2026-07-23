# Global Once-Per-Month Market Owner Migration

## Decision

Monthly market-local accounting now has one live traversal architecture:

```text
first eligible monthly country pulse
  -> cbp_run_monthly_q8_7_global_market_local_cycle_once
     -> every_market_in_world
        -> shared per-market accounting

later monthly country pulses
  -> skip every_market_in_world through the global month stamp
  -> continue current-country trade and US-04 work
```

The former rollback route is retired:

```text
current country
  -> every_market_center_in_country
  -> shared per-market accounting
```

## Rationale

The global owner has been the default active route and has received sustained live
use. The dual-path architecture was retained during the original migration because
changing market-local ownership was high risk. That rollback window has now served
its purpose.

Keeping only the global route gives one explicit monthly phase barrier:

```text
all selected markets finish US-00 and US-10
  -> country-owned trade work starts
  -> monthly US-04 work starts
```

This avoids the ordering ambiguity of a market-center route, where one country can
continue to its completion work before a different market-center owner has run its
market-local accounting.

## Removed runtime surfaces

- `cbp_q8_7_live_global_market_owner_disabled`;
- `cbp_enable_q8_7_live_global_market_owner`;
- `cbp_disable_q8_7_live_global_market_owner`;
- `cbp_q8_7_live_global_market_owner_enabled_trigger`;
- `cbp_q8_7_live_global_market_owner_disabled_trigger`;
- the monthly owner branch calling `cbp_run_monthly_promoted_market_local_cycle`;
- the loaded trigger file `cbp_q8_7_global_owner_triggers.txt`.

The historical wrapper name
`cbp_run_monthly_stock_cycle_q8_7_owner_switch` remains as a stable technical entry
point, but it no longer performs owner selection.

## Retained boundaries

The migration does not remove or merge:

- the global month stamp;
- `every_market_in_world`;
- detailed per-market CBP accounting;
- per-market Vanilla fallback;
- per-market blocked accounting;
- the two-pass US-00-before-US-10 invariant;
- country-owned `every_trade` processing;
- #215 sparse monthly US-04 processing;
- audit reconciliation and location-market memory.

The old `cbp_run_monthly_promoted_market_local_cycle` helper may remain as
historical or test-support code, but it is no longer reachable from the live monthly
owner.

## Static contract

`tools/validate_cbp_global_market_owner_only.py` prevents the retired switch,
trigger file, disable variable, or market-center branch from returning to the live
owner. It also verifies the ordering:

```text
global market pass
  -> country trade owner
  -> monthly US-04 owner
```

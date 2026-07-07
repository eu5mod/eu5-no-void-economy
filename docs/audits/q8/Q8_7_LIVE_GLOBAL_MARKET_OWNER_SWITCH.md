# Q8.7 — Live global market-owner switch

## Status

Implemented as the final Q8.7 runtime-migration layer, then cleaned up by pruning the temporary rollback owner branch.

Q8.7 moved the live market-local owner from the market-center workaround to a once-per-month global market pass:

```txt
old live owner:
  monthly_country_pulse
    -> current country
    -> every_market_center_in_country
    -> market-local branch

current live owner:
  monthly_country_pulse
    -> current country
    -> once-per-month every_market_in_world
    -> market-local branch
```

The old owner-selection rollback switch has been removed. The Q8.7 monthly wrapper no longer supports:

```txt
Q8.7 global owner disabled
  -> legacy rollback owner
     -> every_market_center_in_country
     -> detailed / vanilla fallback / blocked
```

The permanent per-market vanilla fallback/blocked paths remain inside the global owner loop.

## Runtime entry point

The monthly on-action calls:

```txt
modeu5_run_monthly_stock_cycle_q8_7_owner_switch
```

instead of calling `modeu5_run_monthly_stock_cycle` directly.

That wrapper preserves the existing monthly ordering:

```txt
1. stock runtime gate
2. performance-mode human-relevant market preparation
3. current-country capacity refresh
4. monthly market-seen registry preparation
5. human-relevant full-ledger preparation
6. market-local owner pass
7. country trade-owner pass
8. optional audit reconciliation
```

Only step 6 changed owner shape.

## Live owner shape

The live owner is now unconditionally:

```txt
modeu5_run_monthly_q8_7_global_market_local_cycle_once
  -> monthly stamp guard
  -> every_market_in_world
     -> modeu5_prepare_market_runtime_accounting_mode
     -> existing market-local branch for detailed markets
     -> vanilla fallback accounting for fallback markets
     -> blocked accounting for blocked markets
```

The monthly stamp guard prevents the mutating market-local pass from running once per country. Later monthly country pulses only record a skip counter and continue to the country-owned trade pass.

## Preserved market-local branch

The mutating market-local branch is still the existing helper:

```txt
modeu5_run_promoted_market_live_local_branch_market_all_goods
```

This means Q8.7 does not rewrite generated-good internals. It preserves the existing Q4.1/PR7.1 live branch shape:

```txt
for each country present in market:
  refresh country-market capacity
  run US-00 active-good dispatcher

then, after all US-00 passes:
  for each country present in market:
    run US-10 pending-good dispatcher
```

That keeps the core invariant intact:

```txt
all US-00 admission facts before any same-market US-10 consumption
```

## Trade boundary

Q8.7 does not move trade.

The country trade-owner pass remains after the market-local branch:

```txt
modeu5_run_monthly_country_trade_owner_cycle
```

There is still no `every_trade` call from market scope.

## Performance Mode boundary

The global owner relies on the #160 clarification:

```txt
Performance Mode detailed processing is scoped by human-relevant markets,
not by human countries only.
```

Once a market is relevant, the market-local work surface remains all countries present in that market, including AI countries.

## Diagnostics

Q8.7 live-owner counters:

```txt
modeu5_q8_7_live_global_owner_runs
modeu5_q8_7_live_global_owner_skip_runs
modeu5_q8_7_live_global_owner_markets_seen
modeu5_q8_7_live_global_owner_markets_detailed
modeu5_q8_7_live_global_owner_markets_fallback
modeu5_q8_7_live_global_owner_markets_blocked
modeu5_q8_7_live_global_owner_us00_before_us10_guard
modeu5_q8_7_live_global_owner_no_market_scope_trade_guard
```

The existing live dispatcher counters are still populated:

```txt
modeu5_promoted_market_live_dispatcher_runs
modeu5_promoted_market_live_markets_detailed
modeu5_promoted_market_live_markets_fallback
modeu5_promoted_market_live_markets_blocked
modeu5_promoted_market_live_country_cache_rebuilds
modeu5_promoted_market_live_capacity_country_count
modeu5_promoted_market_live_us00_country_passes
modeu5_promoted_market_live_us10_country_passes
modeu5_promoted_market_live_us00_good_scans
modeu5_promoted_market_live_us10_good_scans
modeu5_promoted_market_live_local_markets_processed
modeu5_promoted_market_live_trade_owner_passes
```

## Required validation

Static:

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_modeu5_persistent_state.sh
git diff --check
```

Runtime:

```txt
Run full revalidation with the Q8.7 global owner enabled.
```

The result should show:

```txt
- no duplicate market-local mutation;
- relevant-market surface is preserved;
- US-00 country passes before US-10 country passes;
- country trade-owner pass still runs after market-local work;
- no market-scope every_trade path;
- stock validation remains clean.
```

## Cleanup applied

Removed from the Q8.7 owner-selection path:

```txt
modeu5_q8_7_live_global_market_owner_disabled
modeu5_enable_q8_7_live_global_market_owner
modeu5_disable_q8_7_live_global_market_owner
modeu5_q8_7_live_global_market_owner_enabled_trigger
modeu5_q8_7_live_global_market_owner_disabled_trigger
owner-selection else branch -> modeu5_run_monthly_promoted_market_local_cycle
```

Kept:

```txt
modeu5_run_monthly_q8_7_global_market_local_cycle_once
  -> every_market_in_world
  -> per-market detailed / vanilla fallback / blocked runtime paths
modeu5_run_monthly_country_trade_owner_cycle
```

This cleanup removes only the old owner-selection rollback branch. It does not remove per-market vanilla fallback.

## Merge reading

A successful merge means Q8.7 has moved from proof track to live owner migration and the temporary rollback branch has been pruned.

It does not mean Q8.2 sparse pending scheduling or Q8.4 body-helper splitting are implemented. Those remain separate backlog items.

# Q8.7 — Live global market-owner switch

## Status

Implemented in this PR as the final Q8.7 runtime-migration layer.

The PR moves the live market-local owner from the market-center workaround to a once-per-month global market pass:

```txt
old live owner:
  monthly_country_pulse
    -> current country
    -> every_market_center_in_country
    -> market-local branch

new live owner:
  monthly_country_pulse
    -> current country
    -> once-per-month every_market_in_world
    -> market-local branch
```

The old owner is not deleted. It remains available behind the fallback switch:

```txt
modeu5_q8_7_live_global_market_owner_disabled
```

When that global variable is present, the monthly wrapper falls back to the old `modeu5_run_monthly_promoted_market_local_cycle` path.

## Runtime entry point

The monthly on-action now calls:

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

Only step 6 changes owner shape.

## New owner shape

The new owner is:

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

This means the PR does not rewrite generated-good internals. It preserves the existing Q4.1/PR7.1 live branch shape:

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

The new global owner relies on the #160 clarification:

```txt
Performance Mode detailed processing is scoped by human-relevant markets,
not by human countries only.
```

Once a market is relevant, the market-local work surface remains all countries present in that market, including AI countries.

## Diagnostics

The PR adds Q8.7 live-owner counters:

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

Runtime, new owner:

```txt
Run full revalidation with default Q8.7 global owner enabled.
```

Runtime, fallback owner:

```txt
Set modeu5_q8_7_live_global_market_owner_disabled.
Run the same save and full revalidation again.
```

The result should show:

```txt
- no duplicate market-local mutation;
- same relevant-market surface;
- US-00 country passes before US-10 country passes;
- country trade-owner pass still runs after market-local work;
- no market-scope every_trade path;
- stock validation remains clean.
```

## Merge reading

A successful merge means Q8.7 has moved from proof track to live owner migration.

It does not mean Q8.2 sparse pending scheduling or Q8.4 body-helper splitting are implemented. Those remain separate backlog items.

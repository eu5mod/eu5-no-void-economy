# PERF-08 Shared Storage Capacity Runbook

## Purpose

Validate the shared US-02 storage-capacity model end to end:

```txt
US-02 creates one country-level location/rank capacity pool
-> US-02 writes market trade capacity plus the per-market location share to each country-market capacity record
-> generated per-good adapters read that shared capacity
-> CORE-01 stock operators enforce it
-> CORE-02 initialization uses it as the allocation weight
-> US-00 monthly stock admission can consume it without missing per-good maps
```

This runbook is the runtime validation gate for the shared-capacity PR. Static
checks alone are not enough for `ai-review:ok`.

## Business Decisions Covered

### Runtime Validation

The PR is review-pending until this runbook is executed and the PR receives a
commit-specific validation comment with dump lines from logs.

### Location-Rank Scan

The remaining location-rank scan is country-level only:

```txt
current country -> every_owned_location
```

The ordinary monthly saved refresh path must not scan owned locations. The
country location pool is rebuilt by campaign start, location-owner change,
location-rank change, capital move, or explicit debug/manual full recalculation.

### Country-Level Pooling

Validate this PR as a pooled-capacity business-rule change:

```txt
market_trade_capacity + country_location_pool / count(markets present in country) = country_market_capacity
```

The stock-facing record still belongs to `country x market`, but the non-trade
portion is a location-pool share.

## Build And Install

Close EU5, then run from the repository root:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
git diff --check
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Confirm every installed `MODEU5_SOURCE.txt` reports:

```txt
source_branch=perf/storage-capacity-shared-cache
source_dirty=no
source_commit=<tested commit>
```

Use a dedicated playset with:

```txt
No Void Economy
No Void Economy Tests
```

The optional rebalance packages may remain enabled, but no older duplicate
ModeU5 package should be enabled.

If `debug.log` shows `Running console command: modeu5_us02_debug.1` followed by
`Unknown command`, the event ID was entered without the required console
`event` command. Rerun it as `event modeu5_us02_debug.1`. If the exact command
`event modeu5_us02_debug.1` reports `not a valid ID`, the `No Void Economy
Tests` package is not loaded or EU5 was not restarted after changing the
playset.

## Scenario Setup

Start a disposable 1337 campaign. Playing Castille is fine; the deterministic
fixtures use FRA/ENG internally where required.

Unpause and wait:

```txt
at least one delayed CORE-02 startup day
preferably one full month before monthly-runtime smoke tests
```

If a result says runtime is not ready, wait another day/monthly tick as the
specific runbook says, then rerun that scenario.

## Scenario A - US-02 Shared Capacity

Run:

```txt
event modeu5_us02_debug.1
```

Select:

```txt
Run US-02 storage-capacity test
```

Expected visible result:

```txt
PASS - Storage capacity reconciles without mutating stock
```

Expected `debug.log` lines:

```txt
ModeU5 US-02 DUMP capacity country=FRA good=wheat ...
ModeU5 US-02 RESULT capacity PASS
```

Review the dump and confirm:

```txt
capacity > 0
country_location_count > 0
market_count > 0
market_trade_capacity + country_location_pool_total / market_count == capacity
wheat capacity == iron_wrapper_capacity
available = max(0, capacity - wheat stock)
over_cap = max(0, wheat stock - capacity)
```

This proves every generated good can read the same shared country-market
capacity record and that the record was produced from the cached country
location pool plus current target-market trade capacity.

## Scenario B - CORE-01 Capacity Enforcement

Run:

```txt
event modeu5_debug.1
```

Select:

```txt
Test add, remove, and decay
```

Expected visible result:

```txt
PASS - Add with allow_over_capacity
PASS - Add with enforced capacity
PASS - Remove stock
PASS - Decay stock
```

Expected `debug.log` line:

```txt
ModeU5 CORE-01 RESULT single_record PASS
```

Then run:

```txt
event modeu5_debug.1
```

Select:

```txt
Test same-market transfers
```

Expected visible result:

```txt
PASS - Same-market transfer
PASS - Invalid same-record transfer rejected
```

Expected `debug.log` line:

```txt
ModeU5 CORE-01 RESULT same_market_transfer PASS
```

Then run:

```txt
event modeu5_debug.1
```

Select:

```txt
Test inter-market transfer
```

Expected visible result:

```txt
PASS - Inter-market transfer
```

Expected `debug.log` line:

```txt
ModeU5 CORE-01 RESULT inter_market_transfer PASS
```

These scenarios prove `modeu5_add_stock` and `modeu5_transfer_stock` still read
capacity correctly after the per-good capacity maps were removed.

## Scenario C - CORE-02 Allocation Uses Shared Capacity

Run:

```txt
event modeu5_debug.1
```

Select:

```txt
Run CORE-02 initialization allocation tests
```

Expected visible result:

```txt
PASS - CORE-02 proportional opening allocation
PASS - CORE-02 over-capacity opening allocation
```

Expected `debug.log` lines:

```txt
ModeU5 CORE-02 RESULT proportional PASS
ModeU5 CORE-02 RESULT over_capacity PASS
ModeU5 CORE-02 RESULT initialization PASS
```

Expected failure absence:

```txt
No ModeU5 deterministic CORE-02 proportional initialization allocation test failed
No ModeU5 deterministic CORE-02 over-capacity initialization allocation test failed
```

This proves CORE-02 still uses country-market capacity as the opening-stock
allocation weight.

## Scenario D - US-00 Stock Admission Path

Run:

```txt
event modeu5_us00_debug.1
```

Select:

```txt
Run US-00 controlled pipeline test
```

Expected `debug.log` lines:

```txt
ModeU5 US-00 DUMP controlled_e2e country=FRA good=wheat ...
ModeU5 US-00 RESULT controlled_e2e PASS
```

Then wait at least two in-game days and run:

```txt
event modeu5_us00_debug.1
```

Select:

```txt
Run US-00 monthly runtime smoke test
```

Expected `debug.log` lines:

```txt
ModeU5 US-00 DUMP monthly_runtime country=FRA good=wheat ...
ModeU5 US-00 RESULT monthly_runtime PASS
```

This proves the live stock-admission path can read shared capacity through the
generated per-good adapter.

## Optional Scenario E - Marketplace Timing Probe

Use only in a disposable save.

Run:

```txt
event modeu5_us02_debug.1
```

Select:

```txt
Probe +10 marketplaces - step 1
```

If result is `PENDING`, wait at least one monthly tick, then run:

```txt
event modeu5_us02_debug.1
```

Select:

```txt
Probe +10 marketplaces - step 2 after monthly tick
```

Expected accepted outcomes:

```txt
ModeU5 US-02 RESULT timing IMMEDIATE_PASS
```

or:

```txt
ModeU5 US-02 RESULT timing PENDING
ModeU5 US-02 RESULT timing MONTHLY_PASS
```

This scenario is not required to prove shared capacity, but it helps diagnose
merchant-capacity refresh cadence.

## Logs To Review

After closing the game, inspect:

```txt
debug.log
error.log
game.log
system.log
```

Blocking ModeU5 failures:

```txt
ModeU5 deterministic US-02 storage-capacity test failed
ModeU5 deterministic CORE-02 proportional initialization allocation test failed
ModeU5 deterministic CORE-02 over-capacity initialization allocation test failed
ModeU5 deterministic US-00 controlled pipeline test failed
ModeU5 deterministic US-00 monthly runtime smoke test failed
Failed to fetch variable for 'modeu5_<good>_stock_cap_by_market'
Unknown effect modeu5_recalculate_saved_country_market_storage_capacities_good_wheat
```

Known tolerated noise:

```txt
Tried to localize with localization disabled
```

Tolerate localization assertions only when all expected `ModeU5 ... DUMP` and
matching `ModeU5 ... RESULT ... PASS` lines are present and no ModeU5
script-system failure appears.

## Validation Comment Template

Post actual results as a PR comment, not in the PR body:

````md
Validation for <commit SHA>

Installed provenance:
- modeu5_core source_branch=perf/storage-capacity-shared-cache
- modeu5_core source_commit=<commit SHA>
- modeu5_core source_dirty=no
- modeu5_core_tests source_commit=<commit SHA>

Scenario:
- Started disposable 1337 campaign as <country>
- Waited <duration>
- Ran Scenario A/B/C/D from PERF_08_SHARED_STORAGE_CAPACITY_RUNBOOK.md

Relevant dump lines:
```txt
ModeU5 US-02 DUMP capacity ...
ModeU5 US-02 RESULT capacity PASS
ModeU5 CORE-01 RESULT single_record PASS
ModeU5 CORE-01 RESULT same_market_transfer PASS
ModeU5 CORE-01 RESULT inter_market_transfer PASS
ModeU5 CORE-02 RESULT proportional PASS
ModeU5 CORE-02 RESULT over_capacity PASS
ModeU5 CORE-02 RESULT initialization PASS
ModeU5 US-00 DUMP controlled_e2e ...
ModeU5 US-00 RESULT controlled_e2e PASS
ModeU5 US-00 DUMP monthly_runtime ...
ModeU5 US-00 RESULT monthly_runtime PASS
```

Log review:
- error.log:
- game.log:
- system.log:
- debug.log:

Decision: PASS / PENDING / FAIL
````

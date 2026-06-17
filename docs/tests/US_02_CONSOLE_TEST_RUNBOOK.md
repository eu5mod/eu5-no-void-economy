# US-02 Console Test Runbook

## Purpose

Validate that country storage capacity is rebuilt from market merchant capacity
and owned-location rank/capital contributions without mutating stock. The test
also verifies the country-level wrapper used by CORE-02 startup before it reads
capacity maps for opening-stock allocation.

## Before launching EU5

```sh
./tools/generate_stock_good_helpers.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Confirm that every installed `MODEU5_SOURCE.txt` points to this repository,
branch, and commit.

In the launcher:

```txt
Enable: No Void Economy / modeu5_core
Enable for this validation run only: No Void Economy Tests / modeu5_core_tests
Do not simultaneously enable the older eu5voideco alias.
The three optional gameplay ModeU5 packages may remain enabled.
```

Start a clean campaign with No Void Economy enabled. FRA must exist.

If `event modeu5_us02_debug.1` reports `not a valid ID`, the test package is
not loaded in the active playset or the game was not restarted after changing
the playset.

## Console procedure

1. Open the console.
2. Run:

```txt
event modeu5_us02_debug.1
```

3. Select `Run US-02 storage-capacity test`.
4. In the result event, confirm:

```txt
PASS - Storage capacity reconciles without mutating stock
```

The `modeu5_test_storage_capacity_passed` text is a result marker, not a
console command.

The result event currently displays a compact fallback dump for FRA's capital
market:

```txt
FRA wheat stock
FRA wheat capacity
FRA wheat available capacity
FRA wheat over-capacity
FRA wheat trade-capacity contribution
FRA wheat location-rank contribution
FRA owned locations in the capital market
FRA iron wrapper capacity
```

These visible values are useful for immediate tester feedback, but they are not
the authoritative artifact. Logs are the source of truth.

## Marketplace timing probe

The timing probe is destructive and should be run only in a disposable test
save. It adds 10 `marketplace` levels to FRA's capital to test whether vanilla
market merchant capacity, and therefore US-02 storage capacity, refreshes
immediately or only after a monthly tick.

Run step 1:

```txt
event modeu5_us02_debug.1
```

Select:

```txt
Probe +10 marketplaces - step 1
```

Expected immediate result is one of:

```txt
PASS - Capacity increased immediately after +10 marketplaces
PENDING - No immediate increase; wait at least one monthly tick and run step 2
```

If the result is `PENDING`, advance at least one monthly tick, then run:

```txt
event modeu5_us02_debug.1
```

Select:

```txt
Probe +10 marketplaces - step 2 after monthly tick
```

Expected delayed result:

```txt
PASS - Capacity increased after monthly tick
```

Step 2 reads the persisted wheat capacity record after the monthly tick. It
must not recalculate capacity inside the test step; otherwise it would mask a
missing monthly dispatcher. Failure means either the monthly capacity refresh
did not run, or the +10 marketplace levels did not increase the observed
trade-capacity component. In that case, inspect the visible timing dump before
changing code:

```txt
Storage capacity before / after building / after monthly tick
Storage capacity immediate and monthly deltas
Trade-capacity component before / after building / after monthly tick
Trade-capacity immediate and monthly deltas
```

## Debug values to inspect

On FRA, inspect the latest `modeu5_debug_last_capacity_*` variables:

```txt
country
market
good
previous_total
total
base
building
foreign
trade
location_rank
stock
available
over_cap
location_count
marketplace_levels
market_warehouse_levels
funduq_levels
caravanserai_levels
fondaco_levels
```

For timing probes, also inspect:

```txt
modeu5_debug_last_monthly_capacity_refresh_stamp
modeu5_debug_last_monthly_capacity_refresh_gate_passed
```

Expected arithmetic:

```txt
total = base + building + foreign
base = trade + location_rank
total > 0
location_rank > 0
location_count > 0
available = max(0, total - stock)
over_cap = max(0, stock - total)
```

The event first runs the country-level capacity wrapper for FRA, then reads
wheat and iron capacity in FRA's capital market, then recalculates wheat
directly for formula diagnostics. It explicitly fails if the recalculated
capacity is zero, because a zero-capacity pass would only prove internal
consistency and would not prove that the US-02 world-state scan is usable by
CORE-02 startup. It does not add, remove, transfer, decay, or rebuild stock.

The test also writes a compact numeric dump to global variables:

```txt
modeu5_debug_us02_dump_fra_wheat_stock
modeu5_debug_us02_dump_fra_wheat_capacity
modeu5_debug_us02_dump_fra_wheat_available
modeu5_debug_us02_dump_fra_wheat_over_cap
modeu5_debug_us02_dump_fra_wheat_trade_capacity
modeu5_debug_us02_dump_fra_wheat_location_rank_capacity
modeu5_debug_us02_dump_fra_wheat_location_count
modeu5_debug_us02_dump_fra_iron_capacity
modeu5_debug_us02_probe_before_capacity
modeu5_debug_us02_probe_after_build_capacity
modeu5_debug_us02_probe_after_month_capacity
modeu5_debug_us02_probe_delta_immediate_capacity
modeu5_debug_us02_probe_delta_month_capacity
modeu5_debug_us02_probe_before_trade
modeu5_debug_us02_probe_after_build_trade
modeu5_debug_us02_probe_after_month_trade
modeu5_debug_us02_probe_delta_immediate_trade
modeu5_debug_us02_probe_delta_month_trade
```

These variables are meant to prove that the pass result is backed by non-zero
world-state capacity data rather than only a boolean marker. The probe variables
also show whether the capacity refresh is immediate or delayed.

## Log review

After closing the game, inspect:

```txt
debug.log
error.log
game.log
system.log
```

Expected:

```txt
ModeU5 US-02 DUMP capacity ...
ModeU5 US-02 RESULT capacity PASS
No new ModeU5 script-system error
No "ModeU5 deterministic US-02 storage-capacity test failed" entry
No stock mutation attributed to the capacity test
```

Logs are the source of truth for validating the run. The result event and
persisted result markers are supporting evidence only. The dynamic `debug_log`
dump may emit the known `Tried to localize with localization disabled`
assertion. That assertion is tolerated only when the expected `ModeU5 US-02
DUMP ...` and `ModeU5 US-02 RESULT ...` lines are present and there is no
script-system error or ModeU5 failure line.

For the marketplace timing probe, expected log lines are:

```txt
ModeU5 US-02 DUMP timing ...
ModeU5 US-02 RESULT timing IMMEDIATE_PASS
```

or, for a delayed refresh:

```txt
ModeU5 US-02 RESULT timing PENDING
ModeU5 US-02 DUMP timing ...
ModeU5 US-02 RESULT timing MONTHLY_PASS
```

## Known limitations

The test validates the current world-state scan and persistence contract. It
does not change location rank or move a capital. The optional timing probe does
create a merchant-capacity source by adding 10 marketplace levels to FRA's
capital, and it should not be used in a normal campaign save. Building and
foreign-building capacity fields are intentionally zero-valued compatibility
fields in the current rule. Automatic recalculation scheduling after every
ownership/rank/trade-capacity change requires separate runtime coverage.

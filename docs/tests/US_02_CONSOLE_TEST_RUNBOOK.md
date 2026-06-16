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

Expected arithmetic:

```txt
total = base + building + foreign
base = trade + location_rank
available = max(0, total - stock)
over_cap = max(0, stock - total)
```

The event first runs the country-level capacity wrapper for FRA, then reads
wheat and iron capacity in FRA's capital market, then recalculates wheat
directly for formula diagnostics. It does not add, remove, transfer, decay, or
rebuild stock.

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
No new ModeU5 script-system error
No "ModeU5 deterministic US-02 storage-capacity test failed" entry
No "Tried to localize with localization disabled" assertion
No stock mutation attributed to the capacity test
```

The result event and the persisted result marker are authoritative; this
console test intentionally emits no PASS `debug.log` line.

## Known limitations

The test validates the current world-state scan and persistence contract. It
does not change location rank, move a capital, or create/destroy a merchant
capacity source. Building and foreign-building capacity fields are intentionally
zero-valued compatibility fields in the current rule. Automatic recalculation
scheduling after every ownership/rank/trade-capacity change requires separate
runtime coverage.

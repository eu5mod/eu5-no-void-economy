# US-02 Console Test Runbook

## Purpose

Validate that country storage capacity is rebuilt from owned locations,
compatible domestic buildings, and compatible foreign buildings without
mutating stock.

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
available = max(0, total - stock)
over_cap = max(0, stock - total)
```

The event recalculates wheat and iron capacity for FRA's capital market. It
does not add, remove, transfer, decay, or rebuild stock.

## Log review

After closing the game, inspect:

```txt
error.log
game.log
system.log
```

Expected:

```txt
No new ModeU5 script-system error
No "ModeU5 deterministic US-02 storage-capacity test failed" entry
No stock mutation attributed to the capacity test
```

## Known limitations

The test validates the current world-state scan and persistence contract. It
does not construct or destroy a building. The provisional capacity
coefficients and automatic recalculation scheduling require separate gameplay
approval and runtime coverage.

# US-01 Console Test Runbook

## Purpose

This test proves that the physical map family implements separate logical
`country x market x good` stock records and that the read-only US-01 API
returns the selected record without mutating it.

## Before starting EU5

Close EU5, then run:

```bash
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

Start a clean 1337 campaign where FRA and ENG exist and their capital markets
are different.

If `event modeu5_us01_debug.1` reports `not a valid ID`, the test package is
not loaded in the active playset or the game was not restarted after changing
the playset.

## Console test

Enter:

```txt
event modeu5_us01_debug.1
```

Select:

```txt
Run US-01 stock-dimension test
```

The result event must display:

```txt
PASS - Country, market, and good stocks are isolated
```

Other rows may display `FAIL / NOT RUN`; the action clears previous markers
and runs only the US-01 test.

## Test data

The test records existing values, then applies these additions through
`modeu5_add_stock` with the explicit test policy:

```txt
FRA x FRA capital market x wheat: +11
FRA x ENG capital market x wheat: +13
FRA x FRA capital market x iron: +17
ENG x FRA capital market x wheat: +19
```

Expected aggregate changes:

```txt
FRA capital market x wheat: +30
ENG capital market x wheat: +13
FRA capital market x iron: +17
```

The test removes exactly those additions through `modeu5_remove_stock` and
validates all three affected market-good aggregates.

## Debug values

After each `modeu5_read_country_stock_record` call, the selected country stores:

```txt
modeu5_debug_last_record_country
modeu5_debug_last_record_market
modeu5_debug_last_record_good
modeu5_debug_last_record_stock
modeu5_debug_last_record_capacity
modeu5_debug_last_record_available_capacity
modeu5_debug_last_record_over_capacity
modeu5_debug_last_record_market_stock
```

## Log review

After closing EU5, inspect:

```txt
Documents/Paradox Interactive/Europa Universalis V/logs/debug.log
Documents/Paradox Interactive/Europa Universalis V/logs/error.log
Documents/Paradox Interactive/Europa Universalis V/logs/game.log
Documents/Paradox Interactive/Europa Universalis V/logs/system.log
```

The US-01 test succeeds when no
`ModeU5 deterministic US-01 country, market, and good isolation test failed`
message, no `Tried to localize with localization disabled` assertion, and no
new ModeU5 script-system error appears. `debug.log` should contain the
corresponding US-01 PASS line.

## Known limitation

This test verifies the US-01 storage dimensions and read API. It does not prove
US-02 live capacity calculation, production attribution from vanilla, or
monthly orchestration.

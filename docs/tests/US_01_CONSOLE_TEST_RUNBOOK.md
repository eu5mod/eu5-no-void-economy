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

Confirm that the installed `MODEU5_SOURCE.txt` names the
`feature/country-stock-model` branch and the intended commit.

Start a clean 1337 campaign where FRA and ENG exist and their capital markets
are different.

## Console test

Enter:

```txt
event modeu5_debug.1
```

Select:

```txt
Test country, market, and good stock isolation
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
Documents/Paradox Interactive/Europa Universalis V/logs/error.log
Documents/Paradox Interactive/Europa Universalis V/logs/game.log
Documents/Paradox Interactive/Europa Universalis V/logs/system.log
```

The US-01 test succeeds when no
`ModeU5 deterministic US-01 country, market, and good isolation test failed`
message or new ModeU5 script-system error appears.

## Known limitation

This test verifies the US-01 storage dimensions and read API. It does not prove
US-02 live capacity calculation, production attribution from vanilla, or
monthly orchestration.

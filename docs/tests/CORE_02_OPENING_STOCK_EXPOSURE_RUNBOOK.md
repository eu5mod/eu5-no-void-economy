# CORE-02 Opening Stock Exposure Runbook

This controlled test verifies TECH-01 `091`. It does not initialize ModeU5
stocks and must not be used as a partial CORE-02 implementation.

## Install

Close EU5, then run:

```bash
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Confirm that `packages/modeu5_core_tests` was installed and that the installed
test package's `MODEU5_SOURCE.txt` identifies:

```txt
branch: spike/core-02-opening-stock-exposure
```

## Scenario

1. Enable No Void Economy and No Void Economy Tests in a dedicated test
   playset.
2. Start a clean 1337 campaign.
3. Let at least two game days pass.
4. Open the console and run:

```txt
event modeu5_core02_probe.1
```

The technical minimum is one complete in-game day because the probe is attached
after `on_game_start` through `delay = { days = 1 }`. The extra day is kept in
the runbook to avoid judging logs while delayed startup work is still settling.

## Expected result

The event must display:

```txt
PASS - Delayed game-start probe executed
PASS - FRA capital market scope resolved
PASS - stockpile_in_market(goods:wheat) returned a value
```

The global numeric variable
`modeu5_core02_probe_opening_wheat_stock` must exist. Zero is a valid opening
value and must not be treated as probe failure.

No `modeu5_<good>_stock_by_market` entry, market cache, schema version, or
initialization-state variable may be created by this probe.

## Log review

Review `error.log`, `game.log`, and `system.log`.

Failure evidence includes:

```txt
Unknown trigger or value for stockpile_in_market(goods:wheat)
Failed to fetch the target good
The delayed probe never executed
The FRA capital market scope did not resolve
```

The rejected syntax `stockpile_in_market:wheat` must not be restored. In the
controlled June 15, 2026 run, EU5 interpreted `wheat` as an event-target link
and then reported `goods stockpile_in_market: field not set`. Vanilla scripts
use the parameterized value form:

```txt
"stockpile_in_market(goods:wheat)"
```

## Controlled result - June 15, 2026

The test installed from commit `7b6474eec355258176c8025ce276f4a7898cf208`
passed on campaign date `1337.4.7`.

The post-test save contained:

```txt
modeu5_core02_probe_started_after_delay = yes
modeu5_core02_probe_market_found = yes
modeu5_core02_probe_opening_wheat_stock = <numeric value>
modeu5_core02_probe_value_read = yes
modeu5_core02_probe_passed = yes
```

`modeu5_core02_probe_failed` was absent. The save contained no ModeU5 stock
map entry, market-stock cache, schema version, initialization state, or
CORE-01 test marker. The current logs contained no ModeU5 script error from
the probe.

TECH-01 `091` is therefore `CONFIRMED`. Keep this runbook as the regression
test for the opening-stock read before changing the CORE-02 implementation.

# CORE-02 Opening Stock Exposure Runbook

This controlled test verifies TECH-01 `091`. It does not initialize ModeU5
stocks and must not be used as a partial CORE-02 implementation.

## Install

Close EU5, then run:

```bash
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Confirm that `MODEU5_SOURCE.txt` identifies:

```txt
branch: spike/core-02-opening-stock-exposure
```

## Scenario

1. Enable No Void Economy.
2. Start a clean 1337 campaign.
3. Let at least two game days pass.
4. Open the console and run:

```txt
event modeu5_core02_probe.1
```

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

Only after the event passes and the logs contain no ModeU5 script error may
TECH-01 `091` become `CONFIRMED` and full CORE-02 implementation begin.

# PERF-05 Reduce Global Market Scans Runbook

## Scope

This runbook validates the active-market scheduling indexes added for Issue #60
PR 4:

```txt
modeu5_<good>_active_markets
modeu5_active_markets_any_good
modeu5_validate_active_stock_consistency
```

The goal is not to remove strict audits. It is to prove that active validation
can repair a known market-good inconsistency without scanning every market in
the world.

## Build And Install

Run from the repository root:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Scenario A - Deterministic Reconciliation Test

Setup:

```txt
Start a disposable campaign where FRA and ENG exist.
Run:

event modeu5_debug.1

Choose "Test US-11 dirty-record reconciliation".
```

Expected visible results:

```txt
PASS - Dirty market-good reconciliation
PASS - Active market-good reconciliation
PASS - Empty reconciliation is a no-op
```

Expected internal behavior:

```txt
The fixture clears active and dirty lists.
The fixture adds wheat stock in FRA's capital market.
The stock write marks modeu5_wheat_active_markets.
The stock write marks modeu5_active_markets_any_good.
Dirty validation repairs the first corruption.
Active validation repairs the second corruption through the active market list.
Empty dirty validation remains a no-op.
```

## Logs To Inspect

```txt
error.log
game.log
system.log
debug.log when deterministic dumps are emitted
```

There should be no ModeU5 script-system error. Localization-disabled
assertions remain tolerated only when the expected PASS markers are visible and
the logs contain no ModeU5 script errors.

## Known Limitations

Active lists are scheduling indexes, not proof that a market still has nonzero
stock or capacity. They may be overinclusive until a future repair/rebuild layer
can characterize safe list-item removal. Strict exhaustive validation remains
available through `modeu5_validate_all_stock_consistency`.

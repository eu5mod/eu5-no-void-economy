# PERF-07 Market-Owned Runtime Pass Runbook

## Scope

This runbook validates the Issue #60 market-owned maintenance layer:

```txt
active market -> rebuilt current-market countries_present_in_market -> active goods
```

It also validates the explicit boundary:

```txt
TECH-01 126 durable per-market cache remains NOT_CONFIRMED.
TECH-01 127 dedicated market-change hook remains NOT_CONFIRMED.
```

## Build And Install

Run from the repository root:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Scenario A - Deterministic Active Validation

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

Expected dump lines:

```txt
ModeU5 US-11 DUMP active_reconciliation type=3 records_checked=1 inconsistencies=1 rebuilds=1 failures=0 market_stock=150.00
ModeU5 PERF-07 DUMP market_owned_runtime active_markets=1 cache_rebuilds=1 active_goods=1 dirty_repairs=0
ModeU5 US-11 RESULT reconciliation PASS
```

The exact counts may be greater than `1` if the campaign already has additional
active markets/goods. The blocking condition is zero active markets, zero cache
rebuilds, or zero active goods while the active reconciliation PASS marker is
expected.

## Logs To Inspect

```txt
error.log
game.log
system.log
debug.log when deterministic dumps are emitted
```

## Known Limitations

This test does not prove a durable per-market country-list cache. It proves the
confirmed fallback: rebuild one current-market work cache, consume it for active
goods, and keep durable storage blocked on TECH-01 126.

This test does not prove a dedicated market-change hook. It relies on explicit
rebuild/repair cadence because TECH-01 127 is still `NOT_CONFIRMED`.

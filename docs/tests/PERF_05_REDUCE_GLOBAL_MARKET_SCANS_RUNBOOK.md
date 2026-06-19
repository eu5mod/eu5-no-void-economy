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

Scope contract:

```txt
monthly_country_pulse already runs once per country.
Monthly runtime tests should be interpreted as current country -> market -> good.
Any one-per-cycle reconciliation invoked from that pulse must reuse the current
pulse country as its controller rather than performing a second country scan.
The seen-market registry records duplicate market encounters, but country-owned
good processing still runs for every country-market tuple.
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
The monthly seen-market registry can report duplicate market encounters without
skipping country-owned processing.
```

Expected dump lines:

```txt
ModeU5 US-11 DUMP dirty_reconciliation records_checked=1 inconsistencies=1 rebuilds=1 failures=0 market_stock=150.00
ModeU5 US-11 DUMP empty_reconciliation records_checked=0 inconsistencies=0 rebuilds=0 failures=0
ModeU5 US-11 DUMP active_reconciliation type=3 records_checked=1 inconsistencies=1 rebuilds=1 failures=0 market_stock=150.00
ModeU5 US-11 RESULT reconciliation PASS
```

## Scenario B - Reconciliation Cadence Gates

Setup:

```txt
Start a disposable initialized campaign.
Run:

event modeu5_debug.1

Choose "Test US-11 reconciliation cadence gates".
```

Expected dump lines:

```txt
ModeU5 US-11 DUMP cadence normal_monthly_stamp=0 debug_monthly_stamp=0 audit_monthly_stamp=1 four_yearly_stamp=1
ModeU5 US-11 RESULT cadence PASS
```

This proves that normal/debug/verbose debug do not trigger automatic monthly
reconciliation, while dedicated audit mode and the four-year pulse remain valid
automatic reconciliation cadences.

When reviewing a monthly runtime smoke test, also inspect:

```txt
modeu5_monthly_markets_seen_new_count
modeu5_monthly_markets_seen_duplicate_count
```

`duplicate_count > 0` is not an error by itself. It means multiple countries
were present in the same market during the country-pulse cycle.

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

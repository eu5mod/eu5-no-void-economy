# CORE-04 Market Entry Runtime Coverage Runbook

## Purpose

Validate explicit old-market to new-market stock persistence for a country that
enters a market without an existing country-market stock/capacity record.

CORE-04 does not create trade, transport, price, or location-level stock records.
It moves stock through `cbp_transfer_stock` from:

```txt
country x old_market x good
to
country x new_market x good
```

using the CORE-03 storage-share principle.

## Command

Run on a disposable campaign after CORE-02 initialization has completed:

```txt
event cbp_core04_debug.1
```

The main revalidation chain also runs this scenario:

```txt
event cbp_revalidate_debug.1
```

After closing EU5, summarize the logs:

```txt
./tools/summarize_test_cbp_logs.sh
```

## Expected Summary Markers

The summary should include:

```txt
ModeU5 TEST ENTERED scenario=core04_market_entry
ModeU5 TEST PASS scenario=core04_market_entry
CORE-04 topology diagnostics: <non-zero>
```

Expected CORE-04 branch diagnostics include:

```txt
ModeU5 CORE-04 MARKET_ENTRY mode=normal result=migrated ...
ModeU5 CORE-04 MARKET_ENTRY result=known_market_oscillation ...
ModeU5 CORE-04 MARKET_ENTRY mode=performance result=promoted_and_migrated ...
ModeU5 CORE-04 MARKET_ENTRY result=blocked reason=cbp_deactivated
```

## What The Probe Covers

- Normal Mode first-entry migration.
- Known-market oscillation with no duplicate stock move.
- Performance Mode promotion before detailed stock mutation.
- Deactivated Mode blocked behavior.
- Aggregate conservation for wheat in the source and target markets.

## Current Boundary

The runtime migration helper requires explicit `old_market` and `new_market`
scopes. The branch also records a last-known market on owned locations at game
start and after monthly country pulses, but the stored scope is not yet used as
an automatic migration source until that retrieval path is validated locally.

Logs are the source of truth for PASS/FAIL review.


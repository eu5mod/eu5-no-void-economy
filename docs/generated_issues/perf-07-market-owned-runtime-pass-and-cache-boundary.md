# PERF-07 - Market-Owned Runtime Pass And Cache Boundary

Labels: technical-foundation, module:core, enhancement

Related issue: https://github.com/eu5mod/eu5-no-void-economy/issues/60

Implements the remaining Issue #60 performance scope that is currently safe to
implement:

```txt
Market-owned runtime pass
Durable per-market country-list cache boundary
Market-change repair fallback cadence
```

## User Story

As a ModeU5 maintainer, I want market-owned maintenance to run once per active
market and reuse the market's rebuilt country work cache across all active goods
so that validation and repair avoid repeated market-location scans.

## Functional objective

Refactor active validation from:

```txt
active market -> active good -> rebuild countries_present_in_market -> validate
```

to:

```txt
active market
  -> rebuild current-market countries_present_in_market once
  -> active goods in that market
  -> validate each active good using the prepared cache
```

This implements a real market-owned maintenance pass while respecting the
current engine-exposure boundary:

```txt
TECH-01 126 remains NOT_CONFIRMED: no durable per-market country-list cache.
TECH-01 127 remains NOT_CONFIRMED: no dedicated market-change on_action.
```

The accepted fallback is explicit rebuild/repair from market locations whenever
market-owned maintenance or dirty cache repair runs.

## Required scopes / values / effects

| Need | Scope | Method | Status | TECH-01 |
|---|---|---|---|---|
| Active market scheduling | global -> market | `modeu5_active_markets_any_good` | CONFIRMED | 129 |
| Current-market country work cache | global -> country | `modeu5_countries_present_in_market` rebuilt from `every_location_in_market` | CONFIRMED | 123, 125 |
| Active-good membership in a market | global -> market | generated `modeu5_<good>_active_markets` | CONFIRMED | 129 |
| Prepared-cache active validation | active market -> cached countries -> active goods | generated prepared-cache validators | CONFIRMED | 132 |
| Durable per-market cache | market/global keyed country list | persistent per-market variable list or dynamic list name | NOT_CONFIRMED | 126 |
| Dedicated market-change hook | location/market event | `on_location_changed_market` or equivalent | NOT_CONFIRMED | 127 |

## Files expected to change

```txt
tools/generate_stock_good_helpers.sh
tools/templates/modeu5_stock_good_adapter.template.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_stock_test_effects.txt
docs/generated_issues/perf-00-performance-optimization-master.md
docs/generated_issues/perf-05-reduce-global-market-scans.md
docs/generated_issues/perf-07-market-owned-runtime-pass-and-cache-boundary.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/PERF_05_REDUCE_GLOBAL_MARKET_SCANS_RUNBOOK.md
docs/tests/PERF_07_MARKET_OWNED_RUNTIME_PASS_RUNBOOK.md
docs/tests/TEST_PLAN.md
```

## Dependencies

- PERF-03 current-market country work cache.
- PERF-05 active market indexes.
- PERF-06 country-pulse scope contract.
- US-11 active validation and deterministic reconciliation tests.

## Implementation rules

- Do not implement a fake durable per-market cache while TECH-01 126 remains
  `NOT_CONFIRMED`.
- Do not implement a fake market-change hook while TECH-01 127 remains
  `NOT_CONFIRMED`.
- Do not skip country-owned monthly work based on market-owned caches.
- Treat `modeu5_countries_present_in_market` as a current-market work cache only.
- Active validation may rebuild the current-market country cache once per active
  market, then reuse it for every active good in that market.
- Dirty validation remains good-specific and may still rebuild the cache for the
  exact dirty market/good path.
- Strict exhaustive validation remains available as a manual/debug tool.

## Acceptance criteria

- Active validation rebuilds `modeu5_countries_present_in_market` once per active
  market before calling generated active-good validators.
- Generated active-good validators use a prepared-cache scan and do not rebuild
  the country cache per good.
- Debug logs expose:

```txt
ModeU5 PERF-07 DUMP market_owned_runtime active_markets=... cache_rebuilds=... active_goods=... dirty_repairs=...
```

- The US-11 deterministic reconciliation test still passes.
- TECH-01 126 and 127 remain unresolved and documented rather than silently
  treated as implemented.

## Manual test scenario

Run:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Then in a disposable campaign:

```txt
event modeu5_debug.1
choose "Test US-11 dirty-record reconciliation"
```

Expected dump lines:

```txt
ModeU5 US-11 DUMP active_reconciliation type=3 records_checked=1 inconsistencies=1 rebuilds=1 failures=0 market_stock=150.00
ModeU5 PERF-07 DUMP market_owned_runtime active_markets>=1 cache_rebuilds>=1 active_goods>=1 dirty_repairs>=0
ModeU5 US-11 RESULT reconciliation PASS
```

## Known limitations

The PR does not implement a durable per-market country-list cache. The current
global `modeu5_countries_present_in_market` list is rebuilt for one market at a
time, then consumed immediately.

The PR does not add a dedicated market-change on_action. Ownership changes keep
marking affected markets dirty, while market reassignment without ownership
change remains covered only by explicit rebuild/repair cadence until an engine
hook is confirmed.

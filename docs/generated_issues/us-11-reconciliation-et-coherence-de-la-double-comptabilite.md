# US-11 — Accountring Reconciliation

Labels: module:core, technical-foundation

## User Story

```txt
US-11 — Accountring Reconciliation
```

As a player, I want country stocks, market aggregates, and recognized economic outcomes to remain consistent after every major operation.

## Functional objective

Orchestrate CORE-01.5 and CORE-01.6 through incremental monthly checks of modified market/good records and one exhaustive yearly safety pass. Schedule each global pass once per calendar cycle and provide deterministic integration tests.

## Runtime position

```txt
Monthly step: 18
Yearly step: 1-2 and after exceptional ownership/market changes
Depends on counters from: all centralized stock operations
Feeds counters to: diagnostics and safe downstream reads
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Iterate countries/markets/goods | none/country/location → country/market/goods | `every_country`, `every_market_in_world`, `every_goods`, owned locations and scope links | CONFIRMED | 001-006 |
| Scope passing | scripted effect | `save_scope_as`, `save_temporary_scope_as`, explicit parameters | CONFIRMED | 008 |
| Country source record | country × market × good | logical `stock` field backed by country-scoped `modeu5_<good>_stock_by_market` maps keyed by market | CONFIRMED | 007, 015 |
| Market aggregate storage | market × good | global per-good `modeu5_<good>_market_stock` map keyed by market | FALLBACK_ACCEPTED | 007, 016 |
| Rebuild aggregate | ModeU5 | `modeu5_rebuild_market_stock_from_country_stocks` | CONFIRMED | 019 |
| Validate consistency | ModeU5 | `modeu5_validate_stock_consistency` | CONFIRMED | 020 |
| Monthly invocation | country | `monthly_country_pulse` at runtime step 18 | CONFIRMED | 011 |
| Yearly invocation | country | `yearly_country_pulse` before annual consumers and after exceptional rebuild triggers | CONFIRMED | 012 |
| Deterministic debug invocation | effect scope | event triggers and logs | CONFIRMED | 013 |
| Dirty market index by good | global variable system → market | one deduplicated `modeu5_<good>_dirty_markets` global variable list per good | CONFIRMED | 111 |
| One global pass per cycle | country pulse → global state | `current_year`, `current_month`, guarded global cycle stamps | CONFIRMED | 112 |

## Files expected to change

```txt
in_game/common/script_values/
in_game/common/scripted_effects/
in_game/common/on_action/
in_game/events/
in_game/localization/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: CORE-01.1 through CORE-01.6, iteration exposure, TECH-01
Blocks: safe monthly/yearly stock cycle and all stock-owning features
Related US: US-01, US-03, US-10, US-00
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Country stock is always the source of truth.
- Rebuild market aggregate from country stocks only.
- Read the `stock` field of each logical country × market × good record through its confirmed physical map and write only the selected market key in the global per-good aggregate map.
- Treat missing source entries as zero and replace the aggregate key by remove/re-add.
- Use generated per-good helpers where the country source map name varies by good.
- Keep one global variable list per good containing the markets modified by a centralized stock operation. This list is only a scheduling index and never a stock source.
- Add a market to its dirty list only when it is not already present.
- Mark source and target markets dirty after any successful add, remove, transfer, decay, or test-only aggregate corruption that may require validation.
- Run monthly reconciliation only for listed market/good tuples, then clear each processed list.
- Run one exhaustive yearly market/good pass as a safety net, then clear all dirty lists.
- Guard monthly and yearly entry points with persistent calendar stamps because country pulses execute once per country.
- Treat `monthly_country_pulse` / `yearly_country_pulse` as the outer country iteration. When reconciliation is called from a country pulse, preselect the current country as `modeu5_reconciliation_controller`; use the global `every_country` controller fallback only for non-country initialization, audit, or debug entry points.
- Keep the monthly seen-market registry separate from reconciliation state. It records markets reached by country pulses and can support future market-owned scheduling, but US-11 still validates explicit dirty/active market-good indexes and never uses the registry as a stock source.
- Fail closed while CORE-02 initialization is incomplete. Manual deterministic tests may invoke the underlying reconciliation effect directly.
- Never repair country stocks from market stock.
- Route production, consumption, transfer, decay, validation, and rebuild through CORE-01.1 through CORE-01.6.
- Keep rebuild and validation transaction logic in CORE-01.5 and CORE-01.6; US-11 owns global iteration, scheduling, and integration diagnostics.
- Correct negative anomalies through the owning centralized operation and log them.
- Report over-cap state without correcting it; CORE-02/CORE-03 may create valid over-cap country stocks.
- Keep any economic adjustment visible and owned by its relevant US.

## US-specific boundary checks

- [ ] Validation does not create, consume, or transfer goods.
- [ ] Rebuild changes only the market aggregate/cache.
- [ ] Rebuild preserves the different physical orientations of country source maps and the market aggregate map.
- [ ] Small and large differences are both corrected; large differences are prominently logged.
- [ ] Repeated mutations of one market/good in a cycle create one dirty-list entry and one monthly validation.
- [ ] An empty dirty index produces a deterministic no-op.
- [ ] Country pulses cannot run the global monthly or yearly pass more than once per calendar cycle.
- [ ] The yearly safety pass validates tuples even when they were not present in a dirty list.

## Acceptance criteria

- [ ] Add/remove/transfer/decay preserve or restore the invariant.
- [ ] Same-market ownership transfer leaves market aggregate unchanged.
- [ ] Inter-market transfer updates both market aggregates correctly.
- [ ] Rebuild fixes a deliberately corrupted market aggregate without changing country stocks.
- [ ] No negative stock persists.
- [ ] Over-cap stock is reported, remains part of the authoritative country sum, and is never repaired by deleting stock.
- [ ] Debug identifies market, good, expected stock, actual stock, difference, and correction.
- [ ] Monthly work scales with modified market/good tuples rather than every country × market × good tuple.
- [ ] Monthly debug reports records checked, inconsistencies, rebuilds, and failures.
- [ ] A second dirty reconciliation with no intervening mutation checks zero records.
- [ ] The yearly exhaustive pass checks every market/good tuple.
- [ ] Monthly/yearly invocation order is deterministic.
- [ ] TECH-01, logs, and full manual test report are updated.

## Manual test scenario

### Setup

```txt
Country A stock 100; Country B stock 50; Market stock deliberately set to 200
Run validation/rebuild for the market/good
Run the dirty reconciliation again without another mutation
```

### Expected result

```txt
Market stock becomes 150
Country stocks remain 100 and 50
Difference and correction are logged
No wealth, consumption, or transfer is created
The dirty list is empty after the first pass
The second pass reports zero records checked
```

## Known limitations

Automatic monthly/yearly reconciliation remains disabled until CORE-02 marks initialization complete. The exhaustive yearly pass is intentionally more expensive than the incremental monthly path. Country-pulse calendar guards make the global pass run once per cycle, while the current pulse country provides the reconciliation controller so the frequent runtime path does not perform a redundant `every_country` controller scan. Runtime ordering and exceptional lifecycle finalizers still require controlled local tests.

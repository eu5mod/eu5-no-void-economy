# PERF-08 — Shared Storage Capacity Cache

Labels: performance, core, us-02, storage-capacity

## User Story

```txt
PERF-08 — Shared storage capacity cache
```

As a maintainer, I want US-02 storage capacity to be computed once per country as a pooled value, then written once per country-market instead of once per country-market-good, so that monthly capacity refreshes do not repeat identical work for every good or scan owned locations once per market.

## Functional objective

Persist one US-02 capacity record per country-market and have every generated per-good stock adapter read that shared capacity record when enforcing stock admission, transfers, initialization allocation, validation, and debug dumps.

The stored country-market value is the current market's own trade-capacity
contribution plus the per-market share of one country-level location pool:

```txt
country_location_pool
= sum(country owned-location rank/capital contribution)

country_market_capacity
= target_market_trade_capacity
  + country_location_pool / count(markets present in country)
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Country-scoped capacity maps keyed by market | country x market | `modeu5_stock_cap_by_market` and breakdown maps | CONFIRMED | 007, 017 |
| Per-good stock adapters read shared capacity | generated adapter | literal shared map names inside generated helpers | CONFIRMED | 104 |
| Country-market scan | country -> market | `every_market_present_in_country` | CONFIRMED | 117 |
| Country market count | country -> market | `every_market_present_in_country` counter | CONFIRMED | 117 |
| Location-rank formula | country -> owned location | US-02 helper scanned once per country pool rebuild | CONFIRMED | 033-035, 115 |

## Files expected to change

```txt
in_game/common/scripted_effects/modeu5_capacity_effects.txt
in_game/common/scripted_effects/modeu5_debug_effects.txt
in_game/common/script_values/modeu5_stock_values.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/
tools/generate_stock_good_helpers.sh
tools/templates/modeu5_stock_good_adapter.template.txt
tools/validate_module_packages.sh
docs/technical/
docs/tests/
```

## Dependencies

```txt
Depends on: US-02, CORE-01 generated adapter model, CORE-02, CORE-03
Related issue: #60 performance optimization track
```

## Implementation rules

- Store capacity once in `modeu5_stock_cap_by_market`.
- Store diagnostic breakdowns once in `modeu5_base_capacity_by_market`, `modeu5_building_capacity_by_market`, and `modeu5_foreign_capacity_by_market`.
- Do not recreate `modeu5_<good>_stock_cap_by_market` or other per-good capacity maps.
- Keep per-good stock and market-stock maps unchanged.
- Keep generated per-good adapters as the only place that reads/writes persistent map identifiers.
- Recalculate country storage capacity once through shared good-neutral capacity effects; do not loop all goods or select a sentinel good for identical capacity.
- Build one country-level location/rank capacity pool, then divide it across markets present in the country.
- Add the target market's own merchant/trade-capacity contribution when writing the country-market capacity key.
- Do not scan owned locations once per market during the saved country refresh.
- Do not scan owned locations during the ordinary monthly saved country refresh.
- Rebuild the cached country location pool at campaign start and through owner/rank/capital hooks.
- Keep building-derived storage out of the active formula until a future approved business rule reintroduces it.

## Acceptance criteria

- [ ] Generated helpers read `modeu5_stock_cap_by_market` for every good.
- [ ] Generated helpers do not contain `modeu5_<good>_stock_cap_by_market`.
- [ ] The country-level capacity refresh no longer dispatches one recalculation per good.
- [ ] The country-level capacity refresh does not call `goods:wheat` or any other sentinel good.
- [ ] Capacity-only writes do not mark any per-good active-market list.
- [ ] The monthly country-level capacity refresh reads the cached country location pool and does not scan owned locations.
- [ ] Campaign start, location-owner change, location-rank change, and capital move rebuild the affected country location pool.
- [ ] US-02 deterministic test dumps and validates `market_trade_capacity + country_location_pool_total / market_count = tested capacity`.
- [ ] US-02 deterministic test still proves wheat and iron read the same capacity.
- [ ] CORE-01 stock tests still enforce capacity through the centralized operators.
- [ ] CORE-02 initialization still allocates opening stock using shared country-market capacity.
- [ ] CORE-03 succession still reads loser/winner shared capacity for transfer ratios.
- [ ] The PR has a commit-specific runtime validation comment before `ai-review:ok` is considered.

## Manual test scenario

```txt
Run docs/tests/PERF_08_SHARED_STORAGE_CAPACITY_RUNBOOK.md.
```

Expected result:

```txt
US-02 proves wheat and iron read the same shared country-market capacity.
US-02 proves the tested capacity equals target market trade capacity plus the country location pool divided by market count.
CORE-01 proves add/transfer capacity enforcement still works.
CORE-02 proves initialization allocation still uses capacity as weight.
US-00 proves live stock-admission paths can read shared capacity.
No script-system errors mention missing per-good capacity maps.
```

## Decision boundaries and validation gates

### Runtime validation gate

No review label may be added until a tester runs the end-to-end protocol in
`docs/tests/PERF_08_SHARED_STORAGE_CAPACITY_RUNBOOK.md` and posts a PR comment
with the tested commit, installed package provenance, exact console options, log
dump lines, and PASS/PENDING/FAIL decision.

### Location-rank scanning boundary

```txt
country -> owned locations
```

The PR removes the old market-filtered location scan from the saved monthly
country refresh. The monthly refresh reads cached country location-pool
variables and rewrites market capacity shares with current market trade
capacity. Owned-location scanning remains only in explicit pool rebuilds:
campaign start, location-owner changes, location-rank changes, capital moves,
and manual/debug full recalculation.

Functional consequence:

```txt
Capacity remains accurate through lifecycle-maintained country-pool rebuilds.
Monthly cost becomes country-market writeback, not country-location,
country-market-location, or country-market-good-location.
```

### Country-level pooled capacity boundary

This PR implements the country-level pooled-location-capacity business rule.
Capacity still persists as a `country x market` record for stock operations, but
the record value combines target market trade capacity with a share of the
country location pool. This means settlement rank in one market can increase the
country's per-market storage share across all markets, while merchant/trade
capacity remains market-specific. That semantic change is intentional for this
PR.

### Zero building-capacity boundary

`building_capacity` and `foreign_capacity` remain zero-valued compatibility
fields. Building-derived capacity is removed from the active formula until a
future approved business rule reintroduces it.

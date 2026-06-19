# PERF-08 — Shared Storage Capacity Cache

Labels: performance, core, us-02, storage-capacity

## User Story

```txt
PERF-08 — Shared storage capacity cache
```

As a maintainer, I want US-02 storage capacity to be computed once per country-market instead of once per country-market-good, so that monthly capacity refreshes do not repeat identical work for every good.

## Functional objective

Persist one US-02 capacity record per country-market and have every generated per-good stock adapter read that shared capacity record when enforcing stock admission, transfers, initialization allocation, validation, and debug dumps.

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Country-scoped capacity maps keyed by market | country x market | `modeu5_stock_cap_by_market` and breakdown maps | CONFIRMED | 007, 017 |
| Per-good stock adapters read shared capacity | generated adapter | literal shared map names inside generated helpers | CONFIRMED | 104 |
| Country-market scan | country -> market | `every_market_present_in_country` | CONFIRMED | 117 |
| Location-rank formula | country -> owned location | US-02 helper | CONFIRMED | 033-035, 115 |

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
- Recalculate country-market capacity once through the generated sentinel dispatcher; do not loop all goods for identical capacity.
- Keep building-derived storage out of the active formula until a future approved business rule reintroduces it.
- Do not silently switch to a single country-level capacity pool divided across markets; that is a business-rule change because it lets locations in one market support stock in another.

## Acceptance criteria

- [ ] Generated helpers read `modeu5_stock_cap_by_market` for every good.
- [ ] Generated helpers do not contain `modeu5_<good>_stock_cap_by_market`.
- [ ] The country-level capacity refresh no longer dispatches one recalculation per good.
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

This PR intentionally keeps the existing location-rank scan:

```txt
country -> market -> owned locations in that market
```

The optimization removes the redundant good dimension from that scan. It does
not introduce dirty location-rank counters because those counters would require
separate lifecycle coverage for rank, ownership, capital, and market changes.
That is a valid future optimization track, but it is outside this PR.

Functional consequence:

```txt
Capacity remains accurate from the current world state.
Monthly cost becomes country-market-location, not country-market-good-location.
```

### Country-level pooled capacity boundary

The rejected country-level pooled-capacity alternative remains deferred. It is
not a mechanical optimization, because it would allow capacity contributed by
one market to support stock in another market. That changes the economic
semantics of local market storage and must be handled as a separate gameplay
design PR if selected later.

### Zero building-capacity boundary

`building_capacity` and `foreign_capacity` remain zero-valued compatibility
fields. Building-derived capacity is removed from the active formula until a
future approved business rule reintroduces it.

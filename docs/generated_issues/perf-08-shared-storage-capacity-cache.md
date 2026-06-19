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

## Manual test scenario

```txt
Start a clean test campaign.
Run event modeu5_us02_debug.1.
Select "Run US-02 storage-capacity test".
Inspect debug.log for the US-02 dump/result lines.
Run event modeu5_debug.1.
Select CORE-01 stock tests that exercise add/transfer capacity enforcement.
```

Expected result:

```txt
ModeU5 US-02 RESULT storage-capacity PASS
Wheat capacity equals iron wrapper capacity for the same country-market.
No script-system errors mention missing per-good capacity maps.
```

## Known limitations

- The location-rank scan still iterates owned locations in the selected market. This PR removes per-good redundancy; it does not yet replace location scans with incremental dirty counters.
- The rejected country-level pooled-capacity alternative remains available for a later design PR if the gameplay rule is explicitly changed.
- `building_capacity` and `foreign_capacity` remain zero-valued compatibility fields.

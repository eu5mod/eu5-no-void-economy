# PERF-09 — Good-Neutral US-02 Capacity Refresh

Labels: performance, core, us-02, technical-foundation

## User Story

```txt
PERF-09 — Good-neutral US-02 capacity refresh
```

As a maintainer, I want US-02 storage-capacity refreshes to compute and persist one country-market capacity record without selecting a generated good helper, so that shared capacity does not bloat per-good active lists or depend on a sentinel good.

## Functional Objective

US-02 capacity is shared state:

```txt
country x market capacity
```

It is not:

```txt
country x market x good capacity
```

The saved refresh path must therefore be:

```txt
country
  -> calculate country location-capacity pool once
  -> every_market_present_in_country
    -> apply market trade capacity + country pool share
    -> write shared capacity maps
```

It must not be:

```txt
country
  -> goods:wheat
  -> every_market_present_in_country
    -> modeu5_recalculate_country_market_capacity_from_prepared_pool_good_wheat
```

## Shared Capacity Maps

The refresh writes only these country-scoped maps keyed by market:

```txt
modeu5_stock_cap_by_market
modeu5_base_capacity_by_market
modeu5_building_capacity_by_market
modeu5_foreign_capacity_by_market
```

Generated per-good adapters still read these maps when a good-specific stock operation needs capacity enforcement or debug values.

## Implementation Rules

- `modeu5_recalculate_saved_country_storage_capacities` must not select `goods:wheat` or any other sentinel good.
- `modeu5_recalculate_saved_country_market_storage_capacities` must call the shared capacity effect, not a generated good adapter.
- Pure capacity refresh must not call `modeu5_load_stock_record_good_<good>`.
- Pure capacity refresh must not call `modeu5_mark_active_market_good_<good>`.
- Active market-good lists represent stock, market aggregate, ledger, dirty, or validation work. Capacity-only presence is not market-good activity.
- Per-good stock adapters may read shared capacity through `modeu5_load_capacity_breakdown`.

## Per-Good Loop Preservation Rule

Keep per-good loops where the state or vanilla exposure is truly per-good:

```txt
country-market-good stock
market-good aggregate stock
add/remove/transfer/decay
US-00 produced / added / rejected / ratio / void wealth / penalty records
US-00 production ingestion
CORE-02 opening stock
active and dirty market-good lists
```

Remove or avoid per-good loops for:

```txt
shared capacity refresh
shared capacity breakdown writes
capacity-only active-list marking
good-neutral generated dispatchers
```

## Acceptance Criteria

- [ ] `modeu5_recalculate_saved_country_storage_capacities` contains no `goods:wheat` or other sentinel good.
- [ ] Generated stock adapters contain no `modeu5_recalculate_country_market_capacity_good_<good>` helpers.
- [ ] Capacity-only refresh writes shared capacity maps and does not mark per-good active lists.
- [ ] US-02 deterministic test still proves wheat and iron read the same capacity.
- [ ] CORE-01 stock tests still enforce shared capacity through centralized stock operators.
- [ ] CORE-02 initialization still uses shared capacity as allocation weight.
- [ ] Main revalidation remains runnable through `event modeu5_revalidate_debug.1`.

## Manual Test Scenario

Preferred end-to-end path:

```txt
event modeu5_revalidate_debug.1
Select "Revalidate main operations"
```

Then summarize logs:

```sh
./tools/summarize_modeu5_test_logs.sh
```

Expected compact result:

```txt
Failed: 0
Blocked: 0
Missing expected scenarios: 0
```

For focused US-02 validation:

```txt
event modeu5_us02_debug.1
Select "Run US-02 storage-capacity test"
```

Expected logs:

```txt
ModeU5 US-02 DUMP capacity country=FRA good=wheat ...
ModeU5 US-02 RESULT capacity PASS
```

The dump must still show that the wheat wrapper and the iron wrapper read the same shared capacity.

## Known Limitations

- This PR removes the sentinel-good capacity dependency. It does not remove legitimate per-good stock, ledger, production, transfer, or initialization loops.
- `traded_in_market:<good>` remains a candidate future gate only. Do not use it in runtime until TECH-01 confirms exact syntax and scope.
- Durable per-market country-list cache and dedicated market-change hooks remain blocked by TECH-01 126 and 127.

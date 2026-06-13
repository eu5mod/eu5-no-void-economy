# US-00.1 — Monthly Production and Stock Rejection Ledger

Labels: `blocked:engine-exposure`

## User Story

```txt
US-00.1 — Monthly Production and Stock Rejection Ledger
```

As a player, I want produced, stocked, and rejected quantities recorded per country, market, and good so the void economy can be measured accurately.

## Functional objective

Read or calculate production at `location × good`, resolve the ledger country and the location's market, then accumulate monthly `produced_quantity`, `actual_added_quantity`, and `rejected_quantity` under the derived `country × market × good` ledger key. Read stock-add outputs rather than recomputing them.

## Runtime position

```txt
Monthly step: 8; reset at step 19
Depends on counters from: location-level production integration and modeu5_add_stock
Feeds counters to: US-00.2, US-00.3, US-00.4
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Production source iteration/context | country/building/location/good | `every_owned_location`, `every_buildings_in_location`, `every_goods`, saved scopes | CONFIRMED | 003, 006, 008, 029 |
| Produced quantity by location and good | country → owned location × good | target-good `goods_output`; `raw_material_output` for the location RGO; aggregate by `location.market` | TO_TEST | 021 |
| Ledger-country attribution | country-rooted cycle → owned location | current country plus `every_owned_location` and location `owner` validation | CONFIRMED | 003, 005, 011, 081 |
| Market attribution | location → market | `market` scope link | CONFIRMED | 004 |
| Added quantity | ModeU5 stock operation | `actual_added_quantity` | CONFIRMED | 022 |
| Rejected quantity | ModeU5 stock operation | `rejected_quantity` | CONFIRMED | 023 |
| Ledger helper | ModeU5 | `modeu5_update_production_rejection_ledger` | CONFIRMED | 024 |
| Monthly ledger lifecycle | ModeU5 | initialize/accumulate/read/reset at runtime step 19 | CONFIRMED | 024, internal |
| Ledger keying/storage primitive | country-scoped per-good map keyed by market | `add_to_variable_map`, <code>variable_map(name&#124;key)</code>, remove/re-add updates, monthly clear | CONFIRMED | 007, 025 |

## Files expected to change

```txt
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: location production/country/location/market exposure, modeu5_add_stock, US-01, TECH-01
Blocks: US-00.2, US-00.3, US-00.4
Related US: EPIC US-00, US-00-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Use `modeu5_update_production_rejection_ledger` for every ledger write.
- Derive the ledger key while iterating the country: `current_country × location.market × good`.
- Sum location output by good; do not require building-level or RGO-level profit reconstruction.
- Verify how location `goods_output` treats foreign-owned buildings and log the selected ownership rule.
- Aggregate multiple producing locations into the same country/market/good entry.
- Initialize or clear monthly entries, update them during each production stock-add transaction, and reset them only at runtime step 19.
- Do not attempt to rebuild produced/added/rejected totals from end-of-month stock snapshots.
- Do not recalculate add/reject results already returned by `modeu5_add_stock`.
- Clamp negative rejected values to zero and log the anomaly.
- Do not reset counters before all monthly consumers finish.
- Never mutate stock from this ledger.

## US-specific boundary checks

- [ ] Tracking remains at `country × market × good`.
- [ ] Production is read at `location × good` granularity and aggregated into the ledger granularity.
- [ ] The controlled test records how foreign-owned building output is attributed.
- [ ] Separate markets and goods cannot overwrite one another.
- [ ] US-00 remains measurement and future correction, not direct Estate punishment.

## Acceptance criteria

- [ ] Produced, added, and rejected totals accumulate correctly through multiple additions.
- [ ] Production from multiple locations owned by the same country in the same market aggregates into one ledger entry.
- [ ] Production from locations in different markets remains in separate ledger entries.
- [ ] A country can hold different ledgers for the same good in two markets.
- [ ] All writes use the centralized ledger helper.
- [ ] Negative and zero inputs are handled and logged safely.
- [ ] Monthly reset occurs after US-00.2, US-00.3, and US-00.4 reads.
- [ ] Debug shows scope, source, quantities, and available capacity when available.
- [ ] TECH-01 and the PR test report are updated.

## Manual test scenario

### Setup

```txt
Country A has production sources in Locations L1/L2 in Market M1 and L3 in Market M2
Include one location containing a foreign-owned building to validate `goods_output` ownership semantics
L1 and L2 produce iron; L3 produces iron; L2 also produces grain
Run location-level production additions with controlled rejection
```

### Expected result

```txt
L1 and L2 iron production aggregates into Country A × M1 × iron
L3 iron production remains in Country A × M2 × iron
L2 grain remains separate from iron
Totals equal modeu5_add_stock outputs
No stock changes occur from ledger updates
Counters reset only after dependent calculations
```

## Known limitations

Location `goods_output`, `raw_material_output`, country/market production totals, and the aggregation path are documented. Exact target-good syntax and foreign-building ownership semantics remain `TO_TEST`; source-level building/RGO output is not required.

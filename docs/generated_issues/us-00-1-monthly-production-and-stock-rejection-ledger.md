# US-00.1 — Monthly Production and Stock Rejection Ledger

Labels: `blocked:engine-exposure`

## User Story

```txt
US-00.1 — Monthly Production and Stock Rejection Ledger
```

As a player, I want produced, stocked, and rejected quantities recorded per country, market, and good so the void economy can be measured accurately.

## Functional objective

Read or calculate production at its source, resolve the country credited with that production and the source location's market, then accumulate monthly `produced_quantity`, `actual_added_quantity`, and `rejected_quantity` under the derived `country × market × good` ledger key. Read stock-add outputs rather than recomputing them.

## Runtime position

```txt
Monthly step: 8; reset at step 23
Depends on counters from: location-level production integration and modeu5_add_stock
Feeds counters to: US-00.2, US-00.3, US-00.4
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Production source iteration/context | country/building/location/good | `every_owned_location`, `every_buildings_in_location`, `every_goods`, saved scopes | CONFIRMED | 003, 006, 008, 029 |
| Produced quantity at source | production source × location × good | `goods_output`, `raw_material_output`, or pre-`modeu5_add_stock` calculation | NOT_CONFIRMED | 021 |
| Producing-country attribution | building/RGO/location → credited country | building owner, location owner, or documented output recipient | NOT_CONFIRMED | 081 |
| Market attribution | location → market | `market` scope link | CONFIRMED | 004 |
| Added quantity | ModeU5 stock operation | `actual_added_quantity` | CONFIRMED | 022 |
| Rejected quantity | ModeU5 stock operation | `rejected_quantity` | CONFIRMED | 023 |
| Ledger helper | ModeU5 | `modeu5_update_production_rejection_ledger` | CONFIRMED | 024 |
| Monthly ledger lifecycle | ModeU5 | initialize/accumulate/read/reset at runtime step 23 | CONFIRMED | 024, internal |
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
Depends on: source production/country/location/market exposure, modeu5_add_stock, US-01, TECH-01
Blocks: US-00.2, US-00.3, US-00.4
Related US: EPIC US-00, US-00-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Use `modeu5_update_production_rejection_ledger` for every ledger write.
- Derive the ledger key from the production source: `producing_country × source_location.market × good`.
- Do not assume `producing_country = location.owner`; verify the country credited with building/RGO/local production.
- Aggregate multiple producing locations into the same country/market/good entry.
- Initialize or clear monthly entries, update them during each production stock-add transaction, and reset them only at runtime step 23.
- Do not attempt to rebuild produced/added/rejected totals from end-of-month stock snapshots.
- Do not recalculate add/reject results already returned by `modeu5_add_stock`.
- Clamp negative rejected values to zero and log the anomaly.
- Do not reset counters before all monthly consumers finish.
- Never mutate stock from this ledger.

## US-specific boundary checks

- [ ] Tracking remains at `country × market × good`.
- [ ] Production may be read at production-source or `location × good` granularity; source granularity is not confused with ledger granularity.
- [ ] The producing country is verified independently from the location owner where foreign production sources can exist.
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
Include one source whose credited country must be distinguished from the location owner if exposure permits
L1 and L2 produce iron; L3 produces iron; L2 also produces grain
Run source-level production additions with controlled rejection
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

Source-level building/RGO quantity and the country credited with that output remain `NOT_CONFIRMED`. Source discovery, market attribution, scope passing, and keyed variable maps are documented. Use only one explicitly accepted production fallback and one country-attribution fallback if required.

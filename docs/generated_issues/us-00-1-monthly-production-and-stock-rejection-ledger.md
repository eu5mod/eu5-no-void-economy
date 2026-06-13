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
| Production source iteration/context | country/source → location → good | production sources, locations, produced goods, explicit scope passing | TO_TEST | 003-006, 008 |
| Produced quantity at source | production source × location × good | local/building/RGO output or pre-`modeu5_add_stock` calculation | TO_TEST | 021 |
| Producing-country attribution | production source → country | production owner, building owner, output recipient, or verified fallback | TO_TEST | 081 |
| Market attribution | production source → location → market | source location and market scope link | TO_TEST | 004 |
| Added quantity | ModeU5 stock operation | `actual_added_quantity` | CONFIRMED | 022 |
| Rejected quantity | ModeU5 stock operation | `rejected_quantity` | CONFIRMED | 023 |
| Ledger helper | ModeU5 | `modeu5_update_production_rejection_ledger` | CONFIRMED | 024 |
| Monthly ledger lifecycle | ModeU5 | initialize/accumulate/read/reset at runtime step 23 | CONFIRMED | 024, internal |
| Ledger keying/storage primitive | country × market × good | variable maps, scoped variables, or generated keys | TO_TEST | 007, 025 |

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

Source-level production quantity, produced-good discovery, producing-country attribution, source-location/market links, and reliable keyed-variable syntax are `TO_TEST`. The monthly ledger lifecycle is a ModeU5 contract, not a vanilla exposure. Use only one explicitly accepted production fallback, one country-attribution fallback, and one keyed-storage fallback if required.

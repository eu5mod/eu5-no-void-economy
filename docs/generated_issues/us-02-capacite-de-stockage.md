# US-02 — Storage capacity

Labels: core, us-02, storage-capacity

## User Story

```txt
US-02 — Storage capacity
```

As a player, I want each country-market stock capacity to reflect the country's trade capacity in that market and the settlement rank of the locations it owns there.

## Functional objective

Calculate configurable country storage capacity per market and good, recalculate it when ownership or trade capacity changes, and expose any over-cap stock without mutating it.

## Runtime position

```txt
Monthly step: 3 when recalculation is needed
Depends on: country/location/market/trade-capacity exposure
Feeds counters to: modeu5_add_stock, US-01, US-10.2
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Owned locations in market | country → location → market | `every_owned_location` plus location `market` | CONFIRMED | 003-004, 033 |
| Location rank | location | `location_rank = location_rank:<rank>` | CONFIRMED | 115 |
| Capital location check | location | `is_capital = yes/no` | CONFIRMED | 115 |
| Country merchant capacity in a market | market(country) | `scope:<market>.merchant_capacity(<country>)` | CONFIRMED | 116 |
| Initial country-market scan | country → market | `every_market_present_in_country` | CONFIRMED | 117 |
| Capacity record fields | country × market × good | logical `capacity`, `base_capacity`, `building_capacity`, and `foreign_capacity` fields | CONFIRMED | 017, internal |
| Confirmed physical storage | country-scoped synchronized map family keyed by market | `modeu5_<good>_stock_cap_by_market` and optional contribution-field maps | CONFIRMED | 007, 017 |

## Variable-map storage pattern

```txt
logical dimensions: country × market × good
logical fields:
  capacity
  base_capacity
  building_capacity
  foreign_capacity

record owner: country
tuple:        market × good
default:      0

confirmed physical total field:
  modeu5_<good>_stock_cap_by_market

physical breakdown fields:
  modeu5_<good>_base_capacity_by_market
  modeu5_<good>_building_capacity_by_market
  modeu5_<good>_foreign_capacity_by_market
```

The total field is authoritative for stock operations. Breakdown fields are
diagnostic inputs that must sum to the total; they are not alternate capacity
sources. `modeu5_recalculate_country_market_capacity` is the only writer of
this logical capacity record.

## Initial contribution configuration

```txt
market merchant capacity: 1 per trade capacity
owned rural settlement:   0.5
owned town:               1
owned city:               2
owned megalopolis:        4
owned capital:            20
```

Location contribution is non-cumulative. A capital megalopolis contributes 20,
not 24. Existing `building_capacity` and `foreign_capacity` fields remain
persisted for compatibility and diagnostics, but their coefficients are zero
until a later approved business rule re-enables building-derived storage.

## Files expected to change

```txt
in_game/common/script_values/
in_game/common/scripted_effects/
in_game/events/
main_menu/localization/english/
tools/templates/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-01, location/market/trade-capacity exposure, TECH-01
Blocks: CORE-02, CORE-03, capacity-aware production and US-10.2
Related US: US-02-UI, CORE-02, CORE-03, US-07
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Store all capacity coefficients in configuration/scripted values.
- Do not mutate stock while merely calculating capacity.
- Do not delete, decay, or transfer stock merely because capacity was recalculated below the current stock.
- Expose over-cap quantity for diagnostics and future explicitly approved handling.
- Treat capacity as an admission bound for ordinary production/trade and as a proportional weight for CORE-02/CORE-03.
- Recalculate predictably after location ownership, location rank, capital, or merchant-capacity changes.
- Use `modeu5_calculate_location_storage_capacity` for the CORE-03 transferred-location numerator; it intentionally captures only the local settlement-rank/capital contribution carried by that location.
- Add market merchant capacity once at the country-market level, not once per location.
- Apply the location contribution in this priority order: capital, megalopolis, city, town, rural settlement.
- Provide a country-level recalculation wrapper that writes all per-good capacity maps for every market present in that country.
- Run the country-level wrapper for every country before CORE-02 reads capacity maps for opening stock allocation.
- Rebuild each affected capacity key from contributions, then replace the old total by remove/re-add.
- Treat a missing capacity entry as zero and do not attempt runtime map-name construction.
- Log each capacity contribution and fallback.

## US-specific boundary checks

- [ ] Capacity loss does not silently delete or create stock.
- [ ] A capital megalopolis contributes 20, not 24.
- [ ] Merchant capacity is counted once for the country-market pair.
- [ ] Fresh initialization calculates country storage capacities before opening-stock allocation.

## Acceptance criteria

- [ ] Base capacity equals market merchant-capacity contribution plus owned-location rank/capital contributions.
- [ ] Country-level recalculation writes capacity for every generated good in markets present in the country.
- [ ] Breakdown maps, when enabled, reconcile exactly with the authoritative total map.
- [ ] Losing a location reduces the rank/capital contribution.
- [ ] Available capacity equals cap minus current stock, bounded at zero.
- [ ] Add-stock operations under `enforce` reject quantities beyond capacity.
- [ ] CORE-02/CORE-03 may use the documented `allow_over_capacity` policy.
- [ ] Over-cap handling is visible and centralized.
- [ ] TECH-01 and manual test evidence are updated.

## Manual test scenario

### Setup

```txt
FRA exists
Use FRA's capital market
Record FRA wheat stock
Run the country-level capacity wrapper for FRA
Read wheat and iron capacity for the same country and market
Recalculate wheat directly for formula diagnostics
```

### Expected result

```txt
Total capacity equals base + domestic building + foreign building contributions
Base capacity equals trade-capacity contribution + location rank/capital contribution
Wheat and iron receive the same capacity from the same world state
Country-level wrapper output matches direct wheat recalculation
The existing wheat stock is unchanged
Available capacity and over-cap are bounded at zero and reconcile with stock
```

## Known limitations

Owned-location, market, location-rank, capital, and merchant-capacity exposure
are documented and reviewed against local vanilla files. Fresh CORE-02
initialization runs the country-level capacity wrapper before stock allocation.
Automatic dirty-key scheduling after every possible vanilla ownership/rank/trade-
capacity change is not part of this PR: lifecycle callers such as CORE-03 invoke
recalculation directly, while monthly/yearly orchestration remains a follow-up.
Building and foreign-building capacity fields are retained as zero-valued
diagnostic fields until a separate business rule approves building-derived
storage.

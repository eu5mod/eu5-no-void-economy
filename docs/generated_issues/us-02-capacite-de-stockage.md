# US-02 — Storage capacity

Labels: none

## User Story

```txt
US-02 — Storage capacity
```

As a player, I want storage capacity to reflect owned locations and relevant commercial, logistic, and compatible foreign buildings.

## Functional objective

Calculate configurable country storage capacity per market and good, recalculate it when ownership/buildings change, and expose any over-cap stock without mutating it.

## Runtime position

```txt
Monthly step: 3 when recalculation is needed
Depends on: country/location/market/building exposure
Feeds counters to: modeu5_add_stock, US-01, US-10.2
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Owned locations in market | country → location → market | `every_owned_location` plus location `market` | CONFIRMED | 003-004, 033 |
| Buildings in location | location → building | `every_buildings_in_location` | CONFIRMED | 034 |
| Foreign compatible buildings owned by the country | country → foreign building → location → market | `every_owned_foreign_building`, building `location`, and location `market` | CONFIRMED | 114 |
| Capacity record fields | country × market × good | logical `capacity`, `base_capacity`, `building_capacity`, and `foreign_capacity` fields | CONFIRMED | 017, internal |
| Confirmed physical storage | country-scoped synchronized map family keyed by market | `modeu5_<good>_stock_cap_by_market` and optional contribution-field maps | CONFIRMED | 007, 017 |
| Building type and level | building | `building_type = building_type:<key>` and `building_level` | CONFIRMED | 034, 114 |

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
owned location:       10
marketplace level:    25
market_warehouse:    200
funduq:              200
caravanserai:        100
foreign fondaco:     100
```

`market_warehouse` and `funduq` mirror the vanilla
`maximum_stockpile_capacity = 200` contribution found in the reviewed building
definitions. The other values are explicit provisional ModeU5 balance choices
kept in `modeu5_stock_values.txt`; they require gameplay approval before this
issue is ready to merge.

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
Depends on: US-01, building/location exposure, TECH-01
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
- Recalculate predictably after location/building changes.
- Use `modeu5_calculate_location_storage_capacity` for the CORE-03 transferred-location numerator; it intentionally excludes foreign buildings owned by another country.
- Attribute a compatible foreign building to its building owner through `every_owned_foreign_building`, not to the owner of its location.
- Initial compatible building inventory is `marketplace`, `market_warehouse`, `funduq`, `caravanserai`, and foreign `fondaco`.
- Scale every building contribution by `building_level`.
- Rebuild each affected capacity key from contributions, then replace the old total by remove/re-add.
- Treat a missing capacity entry as zero and do not attempt runtime map-name construction.
- Log each capacity contribution and fallback.

## US-specific boundary checks

- [ ] Capacity loss does not silently delete or create stock.
- [ ] Foreign buildings contribute only if their exposure and compatibility are confirmed.

## Acceptance criteria

- [ ] Base location and confirmed building contributions sum correctly.
- [ ] Breakdown maps, when enabled, reconcile exactly with the authoritative total map.
- [ ] Losing a location/building reduces capacity.
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
Recalculate wheat capacity, then iron capacity for the same country and market
```

### Expected result

```txt
Total capacity equals base + domestic building + foreign building contributions
Wheat and iron receive the same capacity from the same world state
The existing wheat stock is unchanged
Available capacity and over-cap are bounded at zero and reconcile with stock
```

## Known limitations

Owned-location, market, building, building-owner, and foreign-building
iteration are documented and reviewed against local vanilla files. Automatic
dirty-key scheduling after every possible vanilla building change is not part
of this PR: callers such as CORE-02 and CORE-03 invoke the recalculation
directly, while monthly orchestration remains a follow-up. The provisional
non-vanilla coefficients still require gameplay approval.

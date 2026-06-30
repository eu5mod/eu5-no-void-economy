# US-10.3 — Unsatisfied Demand Tracking

Labels: none

## User Story

```txt
US-10.3 — Unsatisfied Demand Tracking
```

As a player, I want satisfied and unsatisfied demand recorded so shortages can drive demand adaptation, diagnostics, and future effects.

## Functional objective

Centralize request outcome tracking for consumption and inter-market transfer, calculate satisfaction ratios safely, route local Pop results to US-04, and reset counters only after consumers read them.

## Current implementation slice

This PR implements country-market-good monthly outcome tracking for explicit
US-10 requests:

- consumption maps:
  - `modeu5_consumption_<good>_requested_by_market`
  - `modeu5_consumption_<good>_satisfied_by_market`
  - `modeu5_consumption_<good>_unsatisfied_by_market`
- inter-market trade maps:
  - `modeu5_trade_<good>_requested_by_market`
  - `modeu5_trade_<good>_transferred_by_market`
  - `modeu5_trade_<good>_unsatisfied_by_market`

The maps are additive within the current month and do not persist zero values.
Location-good Pop outcome storage also exists for explicit fallback callers.
The live Pop demand caller and US-04 consumption of those counters remain
separate validation/follow-up work.

## Runtime position

```txt
Monthly step: 10 after consumption; also after step 11 transfers
Yearly step: counters read by US-04 before annual reset
Depends on counters from: US-10.1 and US-10.2
Feeds counters to: US-04 and diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Outcome values | current transaction → persistent aggregate | local requested/satisfied/transferred/unsatisfied values persisted only after resolution | CONFIRMED | 077 |
| Pop location × good outcome record | location × good | requested/satisfied/unsatisfied quantities plus US-04 annual satisfaction/shortage fields | CONFIRMED | 007, 040, 077 |
| Estate/country-market outcome record | country × market × good | logical fields backed by static map families per approved consumer class and outcome metric | CONFIRMED | 007, 077 |
| Monthly reset pulse | country | `monthly_country_pulse` after every monthly consumer has read counters | CONFIRMED | 011 |
| Yearly read/reset pulse | country | `yearly_country_pulse` after US-04 has read annual counters | CONFIRMED | 012 |

## Variable-map storage pattern

Pop outcomes used by US-04:

```txt
logical dimensions: location × good
logical demand record:
  requested_quantity
  satisfied_quantity
  unsatisfied_quantity
  satisfied_months
  unsatisfied_months

record owner: location
tuple/key:    goods scope
default:      0

confirmed physical map family:
  modeu5_pop_demand_requested_quantity
  modeu5_pop_demand_satisfied_quantity
  modeu5_pop_demand_unsatisfied_quantity
  modeu5_pop_demand_satisfied_months
  modeu5_pop_demand_unsatisfied_months
```

Country/market logical outcome record:

```txt
logical dimensions: country × market × good
owner scope:        country
key:                market scope
default:            0

confirmed physical map family:
  modeu5_<consumer_class>_<good>_<outcome>_by_market
```

`consumer_class` and `outcome` must resolve to static approved map names. Runtime map-name construction is not assumed.

One request's arithmetic remains local. US-10.3 writes only the monthly/yearly aggregates required by a named consumer.

## Files expected to change

```txt
in_game/common/scripted_effects/
in_game/common/on_action/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-10.1, US-10.2, counter storage, TECH-01
Blocks: US-04 and shortage diagnostics
Related US: US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Never mutate stock.
- For consumption, use actual removed quantity as satisfied.
- For inter-market trade, use actual transferred quantity as satisfied.
- Do not update satisfaction counters when requested quantity is non-positive.
- Reset monthly/annual counters only after relevant consumers read them.
- Keep tracking target and fallback explicit.
- Treat Pop outcomes consumed by US-04 as one logical location × good record.
- Treat broader outcomes as one logical country × market × good record per approved consumer class.
- Back those records with location-scoped maps keyed by goods or country-scoped per-good maps keyed by market until TECH-01 088 is confirmed.
- Treat missing counters as zero and replace existing entries by remove/re-add.
- Do not persist resolver candidates or per-candidate scores in the outcome maps.

## US-specific boundary checks

- [ ] Pop consumption tracks at `location × good` for US-04.
- [ ] Trade satisfaction is transferred/requested, not requested/requested.

## Acceptance criteria

- [ ] Requested equals satisfied plus unsatisfied for valid demands.
- [ ] Zero/non-positive requests do not alter counters.
- [ ] Pop outcomes reach US-04 with location/good scope intact.
- [ ] Pop outcome maps and US-04 annual counters use the same location owner and goods key.
- [ ] Estate and country-market targets remain distinct.
- [ ] Reset ordering preserves all monthly/yearly consumers.
- [ ] Debug shows demand context, all quantities, ratio, and tracking target.

## Manual test scenario

### Setup

```txt
Consumption request 100, actual removal 75
Trade request 80, actual transfer 50
One zero request
```

### Expected result

```txt
Consumption ratio 0.75, unsatisfied 25
Trade ratio 0.625, unsatisfied 30
Zero request changes no satisfaction counters
```

## Known limitations

Multi-dimensional counter storage through scoped variable maps and the monthly/yearly country pulses are documented. Reset ordering remains a ModeU5 dispatcher contract and must be tested with deterministic debug events.

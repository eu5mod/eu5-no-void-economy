# US-02 — Capacité de stockage

Labels: `blocked:engine-exposure`

## User Story

```txt
US-02 — Capacité de stockage
```

As a player, I want storage capacity to reflect owned locations and relevant commercial, logistic, and compatible foreign buildings.

## Functional objective

Calculate configurable country storage capacity per market and good, recalculate it when ownership/buildings change, and expose any stock exceeding a reduced capacity to an explicit loss/decay rule.

## Runtime position

```txt
Monthly step: 3 when recalculation is needed
Depends on: country/location/market/building exposure
Feeds counters to: modeu5_add_stock, US-01, US-10.2
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Owned locations in market | country/location/market | owned-location iterator + market link | TO_TEST | 003-004, 033 |
| Buildings in location | location | building iterator | TO_TEST | 034 |
| Foreign compatible buildings | location | foreign-building iterator | TO_TEST | 035 |
| Capacity variable | ModeU5 | `country_market_good_stock_cap` | CONFIRMED | 017 |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-01, building/location exposure, TECH-01
Blocks: capacity-aware production and US-10.2
Related US: US-02-UI, US-02-AI, US-07
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Store all capacity coefficients in configuration/scripted values.
- Do not mutate stock while merely calculating capacity.
- Handle over-cap stock through one explicit approved rule using centralized effects.
- Recalculate predictably after location/building changes.
- Log each capacity contribution and fallback.

## US-specific boundary checks

- [ ] Capacity loss does not silently delete or create stock.
- [ ] Foreign buildings contribute only if their exposure and compatibility are confirmed.

## Acceptance criteria

- [ ] Base location and confirmed building contributions sum correctly.
- [ ] Losing a location/building reduces capacity.
- [ ] Available capacity equals cap minus current stock, bounded at zero.
- [ ] Add-stock operations reject quantities beyond capacity.
- [ ] Over-cap handling is visible and centralized.
- [ ] TECH-01 and manual test evidence are updated.

## Manual test scenario

### Setup

```txt
Country A owns two locations in Market M
Add one confirmed commercial and one logistic building
Record capacity, then remove one contributor
```

### Expected result

```txt
Capacity equals configured contribution sum
Removal reduces capacity by the exact configured amount
Any over-cap stock follows the documented centralized rule
```

## Known limitations

Owned-location and building iterators are `TO_TEST`. Foreign compatible buildings may be excluded from MVP if no reliable exposure is confirmed.

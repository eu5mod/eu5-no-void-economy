# US-10.1 — Consumption Stock Resolution Within Market

Labels: `blocked:engine-exposure`

## User Story

```txt
US-10.1 — Consumption Stock Resolution Within Market
```

As a player, I want local consumption satisfied only from real stock available in the relevant market.

## Functional objective

Use ordered US-10.0 candidates to remove stock successively until demand is satisfied or valid stock is exhausted, then expose satisfied and unsatisfied quantities.

## Runtime position

```txt
Monthly step: 9
Depends on counters from: demand caller and US-10.0
Feeds counters to: US-10.3
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Ordered candidates | market/country/good | confirmed US-10.0 relation/access/ordering output | CONFIRMED | 067-074 |
| Central removal | ModeU5 | `modeu5_remove_stock` | CONFIRMED | 075 |
| Population/type context | location | `num_pop_type`, `percentage_pop_type_in_location` | CONFIRMED | 038 |
| Local Pop demand quantity by good | location × good | runtime vanilla Pop-demand value | NOT_CONFIRMED | 037 |
| Estate/other consumer demand context | estate/country | reliable vanilla demand caller inputs | NOT_CONFIRMED | local check required |
| Satisfaction output | ModeU5 | requested/satisfied/unsatisfied values | CONFIRMED | 077 |

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
Depends on: US-10.0, modeu5_remove_stock, demand exposure/fallback
Blocks: US-10.3 Pop/estate consumption tracking
Related US: US-04, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Restrict candidates to the same market as the consumer.
- Remove through `modeu5_remove_stock` only.
- Accumulate actual removed quantity as satisfied quantity.
- Stop at full satisfaction or exhausted candidates.
- Create no trade income, cost, capacity use, profit, or reconciliation.

## US-specific boundary checks

- [ ] Foreign stock in the same market remains stock availability resolution, not intra-market trade.
- [ ] Every unsatisfied quantity is handed to US-10.3.

## Acceptance criteria

- [ ] One demand can use multiple ordered stocks.
- [ ] No stock goes negative.
- [ ] Country and market stocks decrease by matching actual quantities.
- [ ] Satisfied plus unsatisfied equals requested quantity.
- [ ] Same-market resolution creates no trade economics.
- [ ] Every mutation uses `modeu5_remove_stock`.
- [ ] Debug shows candidates, order, quantities by candidate, and exclusions.

## Manual test scenario

### Setup

```txt
Demand 100 in Market M
Eligible stocks: Country A 40, Country B 35
One foreign stock excluded by embargo/allow rule
```

### Expected result

```txt
Satisfied 75; unsatisfied 25
A and B stocks are removed in resolver order
Market stock falls 75
No trade cost/income/capacity use is created
```

## Known limitations

Candidate scoring and ordering are documented. Runtime local Pop demand quantity and Estate/other consumer demand context remain `NOT_CONFIRMED`; a simulated demand source requires explicit acceptance and disclosure.

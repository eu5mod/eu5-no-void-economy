# US-10.1 — Consumption Stock Resolution Within Market

Labels: `blocked:engine-exposure`

## User Story

```txt
US-10.1 — Consumption Stock Resolution Within Market
```

As a player, I want local consumption satisfied only from real stock available in the relevant market.

## Functional objective

Use ordered US-10.0 candidates to remove stock successively until demand is satisfied or valid stock is exhausted, then expose satisfied and unsatisfied quantities.

## Current implementation slice

This PR implements the explicit-request MVP for US-10.1 on top of the US-10.0
resolver core:

- callers use `modeu5_resolve_stock_consumption` with `consumer_country`,
  `market`, `good`, and `requested_quantity`;
- the generated per-good adapter rebuilds the current-market country cache,
  scans candidates once for aggregate diagnostics, then mutates stock by
  deterministic priority bucket;
- own stock is consumed before subject/overlord, market-owner, and other
  foreign stock;
- zero/below-threshold stock, at-war candidates, embargoed candidates, and
  disallowed subject/market-owner/foreign buckets are excluded before mutation;
- the implementation removes stock through `modeu5_remove_stock` only;
- satisfied and unsatisfied quantities are exposed and handed to US-10.3;
- no intra-market trade income, logistics cost, or trade-capacity use is created.

Full score-based tie-breaking and per-candidate exclusion diagnostics remain
follow-up work. Runtime vanilla Pop demand quantity remains `NOT_CONFIRMED`, so
the deterministic test uses an explicit ModeU5 request.

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
| Runtime requested Pop demand quantity by good | Pop / location × good | runtime vanilla requested-demand value | NOT_CONFIRMED | 087 |
| Estate/other consumer demand context | estate/country | reliable vanilla demand caller inputs | NOT_CONFIRMED | 086 |
| Satisfaction output | ModeU5 | requested/satisfied/unsatisfied values | CONFIRMED | 077 |
| Transaction state | current effect/event chain | local requested/remaining/satisfied values and saved candidate scopes | CONFIRMED | 008, internal |

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
Depends on: US-10.0, modeu5_remove_stock, demand exposure/fallback
Blocks: US-10.3 Pop/estate consumption tracking
Related US: US-04, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Restrict candidates to the same market as the consumer.
- Remove through `modeu5_remove_stock` only.
- Accumulate actual removed quantity as satisfied quantity.
- Keep one demand's requested, remaining, and satisfied quantities local; persist outcomes only through US-10.3.
- Stop at full satisfaction or exhausted candidates.
- Create no trade income, cost, capacity use, profit, or reconciliation.

## US-specific boundary checks

- [ ] Foreign stock in the same market remains stock availability resolution, not intra-market trade.
- [ ] Every unsatisfied quantity is handed to US-10.3.

## Acceptance criteria

- [x] One demand can use multiple bucket-ordered stocks.
- [ ] No stock goes negative.
- [ ] Country and market stocks decrease by matching actual quantities.
- [ ] Satisfied plus unsatisfied equals requested quantity.
- [ ] Same-market resolution creates no trade economics.
- [ ] Every mutation uses `modeu5_remove_stock`.
- [ ] Debug shows per-candidate order, quantities by candidate, and exclusions.

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

Bucket ordering is implemented for the explicit-request MVP. Runtime local Pop
demand quantity and Estate/other consumer demand context remain
`NOT_CONFIRMED`; a simulated demand source requires explicit acceptance and
disclosure. Full score-based tie-breaking remains follow-up work.

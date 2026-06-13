# US-10.3 — Unsatisfied Demand Tracking

Labels: none

## User Story

```txt
US-10.3 — Unsatisfied Demand Tracking
```

As a player, I want satisfied and unsatisfied demand recorded so shortages can drive demand adaptation, diagnostics, and future effects.

## Functional objective

Centralize request outcome tracking for consumption and inter-market transfer, calculate satisfaction ratios safely, route local Pop results to US-04, and reset counters only after consumers read them.

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
| Outcome values | ModeU5 | requested/satisfied/transferred/unsatisfied | CONFIRMED | 077 |
| Location × good counters | location/good | internal variables | CONFIRMED | 040, 077 |
| Estate/country-market counters | scoped per-good map keyed by market/target | variable-map add/read/remove/clear operations | CONFIRMED | 007 |
| Monthly reset pulse | country | `monthly_country_pulse` after every monthly consumer has read counters | CONFIRMED | 011 |
| Yearly read/reset pulse | country | `yearly_country_pulse` after US-04 has read annual counters | CONFIRMED | 012 |

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
Depends on: US-10.1, US-10.2, counter storage, TECH-01
Blocks: US-04 and shortage diagnostics
Related US: US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Never mutate stock.
- For consumption, use actual removed quantity as satisfied.
- For inter-market trade, use actual transferred quantity as satisfied.
- Do not update satisfaction counters when requested quantity is non-positive.
- Reset monthly/annual counters only after relevant consumers read them.
- Keep tracking target and fallback explicit.

## US-specific boundary checks

- [ ] Pop consumption tracks at `location × good` for US-04.
- [ ] Trade satisfaction is transferred/requested, not requested/requested.

## Acceptance criteria

- [ ] Requested equals satisfied plus unsatisfied for valid demands.
- [ ] Zero/non-positive requests do not alter counters.
- [ ] Pop outcomes reach US-04 with location/good scope intact.
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

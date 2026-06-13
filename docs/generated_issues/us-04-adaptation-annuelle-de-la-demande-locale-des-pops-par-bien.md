# US-04 — Adaptation annuelle de la demande locale des Pops par bien

Labels: `blocked:engine-exposure`

## User Story

```txt
US-04 — Adaptation annuelle de la demande locale des Pops par bien
```

As a player, I want local Pop demand for a good to adapt slowly to a full year of availability or shortage.

## Functional objective

Track Pop consumption satisfaction at `location × good`; apply the local multiplier before US-10 resolution; increase it 1% after 12 satisfied months, decrease it 1% after 12 unsatisfied months, and leave mixed years unchanged.

## Runtime position

```txt
Monthly step: before US-10.1, then read US-10.3 results
Yearly step: 3-5, then reset annual counters
Depends on counters from: US-10.3
Feeds counters to: next year's local Pop demand simulation
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Local Pop demand by good | location × good | vanilla Pop demand | NOT_CONFIRMED | 037 |
| Population/type inputs | location | Pop values/proxy | TO_TEST | 038 |
| Modify vanilla demand | location/good/pop | demand modifier/effect | TO_TEST | 039 |
| Yearly counters | location × good | ModeU5 variables | CONFIRMED | 040 |
| Yearly pulse | global | yearly on_action | TO_TEST | 012 |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/events/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-10.1, US-10.3, yearly pulse, accepted demand fallback, TECH-01
Blocks: US-04-UI
Related US: US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Apply only to Pop consumption, never building/production/construction/army demand.
- Track at `location × good`, not country or global market.
- Apply multiplier before calling `modeu5_resolve_stock_demand`.
- Treat zero requested quantity as neither satisfied nor unsatisfied.
- Use one explicit simulated-demand fallback if approved.
- Reset annual counters only after yearly adjustment.

## US-specific boundary checks

- [ ] Satisfaction threshold defaults to `0.95` and is configurable.
- [ ] Only 12/12 satisfied or 12/12 unsatisfied changes the multiplier.
- [ ] A shortage in one market does not alter another location's multiplier.

## Acceptance criteria

- [ ] Demand passed to US-10 equals base demand times local multiplier.
- [ ] Monthly satisfaction uses actual removed stock from US-10.1.
- [ ] Twelve satisfied months multiply demand by `1.01`.
- [ ] Twelve unsatisfied months multiply demand by `0.99`.
- [ ] Mixed and zero-demand years make no change.
- [ ] Building inputs are unaffected.
- [ ] Debug exposes all required monthly/yearly values and fallback mode.
- [ ] TECH-01 and annual test evidence are updated.

## Manual test scenario

### Setup

```txt
Location L1/iron: 12 months at or above 95% satisfaction
Location L2/iron: 12 months below 95%
Location L3/iron: mixed year
Initial multiplier 1.00
```

### Expected result

```txt
L1 multiplier 1.01; L2 multiplier 0.99; L3 multiplier 1.00
Annual counters reset after adjustment
Other locations/markets and building demand are unchanged
```

## Known limitations

Direct vanilla local Pop demand is `NOT_CONFIRMED`. Gameplay implementation requires one explicitly accepted simulated-demand fallback and must expose that fallback in debug.

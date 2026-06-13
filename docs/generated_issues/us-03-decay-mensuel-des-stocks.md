# US-03 — Decay mensuel des stocks

Labels: none

## User Story

```txt
US-03 — Decay mensuel des stocks
```

As a player, I want stored goods to decay by 1% each month so holding stock has a carrying cost.

## Functional objective

Apply configurable monthly decay to each country stock after consumption/transfers, using `modeu5_decay_stock`, and reduce the market aggregate by exactly the same total.

## Runtime position

```txt
Monthly step: 12
Depends on counters from: stock state after US-10
Feeds counters to: US-11 validation and debug
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Monthly decay invocation | country | `monthly_country_pulse` → shared ModeU5 monthly dispatcher → `modeu5_decay_stock` at step 12 | CONFIRMED | 011, 036 |
| Country/market/good iteration | none/country/location → market/goods | documented iterators, scope links, maps, and saved scopes | CONFIRMED | 001-008 |
| Central decay mutation | ModeU5 | `modeu5_decay_stock` | CONFIRMED | internal |
| Decay arithmetic | scripted effect/value | `change_variable` multiply/min/max operations | CONFIRMED | 026 |

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
Depends on: US-01, centralized stock effects, monthly pulse, TECH-01
Blocks: complete monthly stock cycle
Related US: US-03-UI, US-11
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Apply decay at country-stock level only.
- Route all mutation through `modeu5_decay_stock`.
- Default to `0.01`, configurable.
- Never calculate an independent market-level decay.
- Prevent negative stocks and log before/after values.

## US-specific boundary checks

- [ ] Runtime order is after stock demand/transfers and before US-00 ratios.
- [ ] Market decay equals the sum of country losses exactly.

## Acceptance criteria

- [ ] Every eligible country stock loses 1% in the controlled test.
- [ ] Market stock falls by the sum of country decay.
- [ ] No stock remains negative.
- [ ] Invariant difference is zero after validation.
- [ ] Debug shows rate, before, decayed quantity, after, and mutation effect.
- [ ] TECH-01 and `error.log` results are recorded.

## Manual test scenario

### Setup

```txt
Country A stock 100; Country B stock 100
Market stock 200; monthly decay 0.01
```

### Expected result

```txt
Country A 99; Country B 99; market 198
Total decayed 2; invariant difference 0
```

## Known limitations

Country/market/good iteration, storage, scope passing, decay arithmetic, and `monthly_country_pulse` are documented. Decay must use the shared monthly dispatcher at runtime step 12 rather than defining a second pulse.

# EPIC US-10 — Résolution de la consommation et du trade inter-marchés depuis les stocks disponibles

Labels: `blocked:engine-exposure`

## User Story

```txt
EPIC US-10 — Résolution de la consommation et du trade inter-marchés depuis les stocks disponibles
```

As a player, I want consumption and inter-market exchanges resolved from actual ModeU5 stock so nonexistent goods cannot be consumed or transferred.

## Functional objective

Deliver one common candidate resolver, same-market consumption removal, inter-market stock transfer, unsatisfied-demand tracking, and transparent diagnostics while preserving stock ownership in centralized effects.

## Runtime position

```txt
Monthly step: 9-12
Depends on counters from: US-01 stock/capacity and demand callers
Feeds counters to: US-04, US-06, debug/UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Candidate relations/scoring | country/market/location | opinion, access, war, embargo, subject, market owner | CONFIRMED | 067-073 |
| Deterministic ordering | list/map/typed iterator | ordered iterators with `order_by` | CONFIRMED | 074 |
| Consumption removal | ModeU5 | `modeu5_remove_stock` | CONFIRMED | 075 |
| Inter-market transfer | ModeU5 | `modeu5_transfer_stock` | CONFIRMED | 076 |
| Satisfaction tracking | ModeU5 | internal variables | CONFIRMED | 077 |
| Vanilla local demand context | location × good / estate / country | runtime consumer demand inputs | NOT_CONFIRMED | 037, local check required |
| Vanilla per-trade requested quantity | trade | exposed trade quantity/capacity | NOT_CONFIRMED | 056 |
| Automatic cycle invocation | global | recurring monthly/yearly on_actions | NOT_CONFIRMED | 011-012 |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_triggers/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/events/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-01, US-02, core stock effects, TECH-01
Blocks: US-04, ModeU5 transfer basis for US-06
Related US: US-10.0, US-10.1, US-10.2, US-10.3, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Never mutate stocks directly.
- Use `modeu5_resolve_stock_demand` for shared candidate logic.
- Use `modeu5_remove_stock` for consumption and `modeu5_transfer_stock` for inter-market exchange.
- Do not create trade economics inside one market.
- Keep US-10 transport cost and trade-income reconciliation outside scope.
- Make candidates, exclusions, quantities, and fallbacks visible.

## US-specific boundary checks

- [ ] Same-market resolution creates no trade income, transport cost, trade-capacity use, or trade profit.
- [ ] Inter-market transfer applies only when source and target differ.
- [ ] US-06 receives actual transferred quantity, never unsatisfied demand.

## Acceptance criteria

- [ ] Common candidate selection and exclusion logic is reused.
- [ ] Consumption removes only available stock through centralized effects.
- [ ] Inter-market trade respects seller stock and buyer capacity.
- [ ] Requested, satisfied/transferred, and unsatisfied quantities reconcile.
- [ ] The stock invariant holds after every operation.
- [ ] Debug explains order, score, exclusion, quantity, and handoff.
- [ ] TECH-01 and complete test evidence are updated.

## Manual test scenario

### Setup

```txt
One market with two eligible stocks for consumption
Two distinct markets for a capacity-limited transfer
Include one excluded seller
```

### Expected result

```txt
Consumption removes stock without trade economics
Transfer moves only actual available/capacity-limited quantity
Unsatisfied demand is tracked
US-06 receives only transferred quantity
```

## Known limitations

Relation, market-access, ownership, and ordering exposure is documented. Runtime consumer-demand inputs, per-trade requested quantity, and recurring cycle hooks remain `NOT_CONFIRMED`; each blocked path may use only one explicitly accepted fallback.

# EPIC US-10 — Trade & consumption résolution

Labels: `blocked:engine-exposure`

## User Story

```txt
EPIC US-10 — Trade & consumption résolution
```

As a player, I want consumption and inter-market exchanges resolved from actual ModeU5 stock so nonexistent goods cannot be consumed or transferred.

## Functional objective

Deliver one common candidate resolver, same-market consumption removal, inter-market stock transfer, unsatisfied-demand tracking, and transparent diagnostics while preserving stock ownership in centralized effects.

## Runtime position

```txt
Monthly step: 9-11
Depends on counters from: US-01 stock/capacity and demand callers
Feeds counters to: US-04 and debug/UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Candidate relations/scoring | country/market/location | opinion, access, war, embargo, subject, market owner | CONFIRMED | 067-073 |
| Deterministic ordering | list/map/typed iterator | ordered iterators with `order_by` | CONFIRMED | 074 |
| Consumption removal | ModeU5 | `modeu5_remove_stock` | CONFIRMED | 075 |
| Inter-market transfer | ModeU5 | `modeu5_transfer_stock` | CONFIRMED | 076 |
| Satisfaction tracking | current transaction | local requested/satisfied/transferred/unsatisfied values handed to US-10.3 | CONFIRMED | 077 |
| Persistent outcome records | location × good and country × market × good | US-10.3 logical records backed by synchronized map families | CONFIRMED | 007, 040, 077 |
| Runtime Pop requested-demand input | Pop / location × good | runtime vanilla requested-demand value | NOT_CONFIRMED | 087 |
| Estate/other consumer requested-demand input | estate / country / consumer × good | runtime vanilla consumer-demand value | NOT_CONFIRMED | 086 |
| Vanilla actual/desired trade quantity | trade | script equivalent to GUI actual-moved and desired-shipment accessors | TO_TEST | 056 |
| Automatic cycle invocation | country | `monthly_country_pulse`, `yearly_country_pulse` | CONFIRMED | 011-012 |

## Files expected to change

```txt
in_game/common/script_values/
in_game/common/scripted_triggers/
in_game/common/scripted_effects/
in_game/common/on_action/
in_game/events/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-01, US-02, core stock effects, TECH-01
Blocks: US-04 and complete stock-based demand resolution
Related US: US-10.0, US-10.1, US-10.2, US-10.3, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Never mutate stocks directly.
- Use `modeu5_resolve_stock_demand` for shared candidate logic.
- Use `modeu5_remove_stock` for consumption and `modeu5_transfer_stock` for inter-market exchange.
- Do not create trade economics inside one market.
- Keep US-10 transport cost and trade-income reconciliation outside scope.
- Make candidates, exclusions, quantities, and fallbacks visible.
- Keep resolver/transfer transaction state local and persist only stock mutations plus US-10.3 monthly/yearly outcome aggregates.

## US-specific boundary checks

- [ ] Same-market resolution creates no trade income, transport cost, trade-capacity use, or trade profit.
- [ ] Inter-market transfer applies only when source and target differ.
- [ ] Actual transferred quantity remains distinct from requested and unsatisfied quantities.

## Acceptance criteria

- [ ] Common candidate selection and exclusion logic is reused.
- [ ] Consumption removes only available stock through centralized effects.
- [ ] Inter-market trade respects seller stock and buyer capacity.
- [ ] Requested, satisfied/transferred, and unsatisfied quantities reconcile.
- [ ] The stock invariant holds after every operation.
- [ ] Debug explains order, score, exclusion, and final quantities.
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
Transfer diagnostics record only the actual transferred quantity
```

## Known limitations

Relation, market-access, ownership, ordering, recurring country pulses, and the vanilla GUI trade-quantity accessors are documented. Runtime consumer-demand inputs remain `NOT_CONFIRMED`; gameplay-script access to per-trade actual/desired quantity remains `TO_TEST`.

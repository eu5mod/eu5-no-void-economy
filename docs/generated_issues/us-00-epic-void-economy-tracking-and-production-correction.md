# EPIC US-00 — Void Economy Tracking and Production Correction

Labels: `blocked:engine-exposure`

## User Story

```txt
EPIC US-00 — Void Economy Tracking and Production Correction
```

As a player, I want economic production to create effective ModeU5 value only when goods enter stock, so persistent unstockable production is measured and corrected.

## Functional objective

Deliver the US-00 pipeline: read production at the finest confirmed source level, resolve the country credited with production and the source location's market, read centralized stock-add results, aggregate produced/added/rejected quantities at `country × market × good`, calculate buffered overproduction and void wealth, prepare the next-month production penalty, and expose visible diagnostics. US-00 does not own or directly mutate stock.

## Runtime position

```txt
Monthly step: 8, then 15-17; reset only at step 23
Depends on counters from: modeu5_add_stock
Feeds counters to: US-05.1, debug/UI, future AI signals
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Production source and quantity | source × location × good | local/building/RGO output or pre-stock-add production calculation | TO_TEST | 003-006, 021 |
| Producing-country attribution | production source → country | production owner/recipient or verified fallback | TO_TEST | 081 |
| Market attribution | production source → location → market | source-location and market scope links | TO_TEST | 004, 008 |
| Monthly ledger lifecycle | ModeU5 | accumulate transactions, read at month end, reset at step 23 | CONFIRMED | 024, internal |
| Ledger keying/storage | country × market × good | variable maps, scoped variables, or generated keys | TO_TEST | 007, 025 |
| Good price | market × good | market/average/base price | TO_TEST | 030 |
| Production penalty modifier | location × good | good-specific output modifier | TO_TEST | 027-029 |
| Central stock-add outputs | ModeU5 | `actual_added_quantity`, `rejected_quantity` | CONFIRMED | 022-023 |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/common/modifiers/
in_game/events/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: core stock effects, US-01, US-02, US-11, TECH-01
Blocks: US-05.1 and complete void-economy visibility
Related US: US-00.1, US-00.2, US-00.3, US-00.4, US-00-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Never write directly to either stock variable.
- Read actual add/reject results from centralized stock effects.
- Keep source production granularity separate from the aggregated ledger key.
- Do not equate the producing country with the location owner without confirmed exposure.
- Accumulate the monthly ledger from production stock-add transactions; never infer it from final stock.
- Route every ledger write through `modeu5_update_production_rejection_ledger`.
- Treat void wealth as tracking/proxy data, not a direct monthly Estate-income punishment.
- Keep one approved fallback per missing exposure and make it visible.

## US-specific boundary checks

- [ ] The correction pipeline targets future production, not direct monthly Estate income.
- [ ] The buffer changes the penalty input, not whether rejected value is tracked.
- [ ] Monthly counters reset only after every downstream consumer has read them.

## Acceptance criteria

- [ ] Produced, added, and rejected quantities remain distinct at `country × market × good`.
- [ ] Source-level production is attributed to the correct producing country, market, and good before aggregation.
- [ ] Overproduction, effective ratio, void wealth, and next-month penalty are traceable end to end.
- [ ] US-00 never mutates stock directly.
- [ ] Debug identifies inputs, price source, buffer, modifier mode, fallback, and aggregation.
- [ ] Missing exposure is updated in TECH-01 before gameplay work proceeds.
- [ ] The stock invariant still holds after validation.
- [ ] The PR records actual results, inspected debug output, `error.log`, and limitations.

## Manual test scenario

### Setup

```txt
Country A; Market M; Good iron
Initial stock 80; capacity 100; monthly production 50
Buffer 0.01; price source recorded
```

### Expected result

```txt
Added: 20; rejected: 30
Overproduction ratio: 0.60; effective ratio: 0.59
Void wealth and N+1 penalty are calculated and visible
Country and market stock: 100; invariant difference: 0
No direct Estate-income mutation
```

## Known limitations

All vanilla production, price, location-selection, and modifier exposures remain gated by TECH-01. A theoretical-only penalty is acceptable when no reliable modifier is confirmed.

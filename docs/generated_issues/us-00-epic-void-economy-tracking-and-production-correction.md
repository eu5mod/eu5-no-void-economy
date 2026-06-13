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
| Production source discovery | building/location/good | production iterators, output checks, saved scopes | CONFIRMED | 003-006, 008, 029 |
| Production quantity at source | source × location × good | `goods_output`, `raw_material_output`, or pre-stock-add calculation | NOT_CONFIRMED | 021 |
| Ledger-country attribution | country-rooted cycle; building/location → country | current country scope plus documented `owner` links | CONFIRMED | 005, 011, 081 |
| Market attribution | location → market | `market` scope link and saved scopes | CONFIRMED | 004, 008 |
| Monthly ledger lifecycle | ModeU5 | accumulate transactions, read at month end, reset at step 23 | CONFIRMED | 024, internal |
| Ledger keying/storage | country-scoped per-good map keyed by market | variable-map add/read/remove/clear operations | CONFIRMED | 007, 025 |
| Good price | market × good | `market_price`; fallback `default_price` / `default_market_price` | CONFIRMED | 030 |
| Production penalty modifier names | location × good / location | `local_<good>_output_modifier`, `local_production_efficiency` | CONFIRMED | 027-029 |
| Dynamic location-modifier application | location | `add_location_modifier` with duration, mode, and dynamic size | CONFIRMED | 010 |
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

Source-level production quantity remains blocked. Ledger-country attribution is a ModeU5 country-scope rule, not a claim about vanilla income accounting; temporary location-modifier application is documented but still requires a controlled local test.

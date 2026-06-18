# EPIC US-00 — Void Economy Tracking and Production Correction

Labels: `module:core`

## User Story

```txt
EPIC US-00 — Void Economy Tracking and Production Correction
```

As a player, I want economic production to create effective ModeU5 value only when goods enter stock, so persistent unstockable production is measured and corrected.

## Functional objective

Deliver the US-00 pipeline: read production at `location × good`, aggregate it through the current country and location market, read centralized stock-add results, record produced/added/rejected quantities at `country × market × good`, calculate buffered overproduction and void wealth, prepare the next-month production penalty, and expose visible diagnostics. US-00 does not own or directly mutate stock.

## Current implementation boundary

The US-00 closure PR wires the complete monthly runtime path: apply the previous-month penalty, read live location `goods_output(goods:<good>)`, add stock through the centralized operator, record produced/added/rejected quantities, calculate ratios and void wealth, store the replacement penalty, and expose deterministic dumps. TECH-01 021 / PROBE-021 confirmed the target-good output syntax; generated per-good modifiers provide the applied N+1 production correction.

## Runtime position

```txt
Monthly step: 8, then 13-15; reset only at step 19
Depends on counters from: modeu5_add_stock
Feeds counters to: debug/UI and balancing diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Production source discovery | building/location/good | production iterators, output checks, saved scopes | CONFIRMED | 003-006, 008, 029 |
| Production quantity by location and good | country → owned location × good | target-good `goods_output(goods:<good>)`; `raw_material_output` diagnostics | CONFIRMED | 021 |
| Ledger-country attribution | country-rooted cycle → owned location | current country plus `every_owned_location` and location `owner` validation | CONFIRMED | 003, 005, 011, 081 |
| Market attribution | location → market | `market` scope link and saved scopes | CONFIRMED | 004, 008 |
| Monthly ledger lifecycle | ModeU5 | accumulate transactions, read at month end, reset at step 19 | CONFIRMED | 024, internal |
| Void-economy record | country × market × good | one logical record containing ledger, ratio, valuation, and prepared-penalty fields | CONFIRMED | 024-026, internal |
| Confirmed physical storage | country-scoped synchronized map family keyed by market | one physical map per persistent record field | CONFIRMED | 007, 025 |
| Good price | market × good | `market_price`; fallback `default_price` / `default_market_price` | CONFIRMED | 030 |
| Production penalty modifier names | location × good / location | `local_<good>_output_modifier`, `local_production_efficiency` | CONFIRMED | 027-029 |
| Dynamic location-modifier application | location | `add_location_modifier` with duration, mode, and dynamic size | CONFIRMED | 010 |
| Central stock-add outputs | ModeU5 | `actual_added_quantity`, `rejected_quantity` | CONFIRMED | 022-023 |

## Files expected to change

```txt
in_game/common/script_values/
in_game/common/scripted_effects/
in_game/common/on_action/
in_game/common/modifiers/
in_game/events/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: core stock effects, US-01, US-02, US-11, TECH-01
Blocks: US-10-UI super visibility
Related US: US-00.1, US-00.2, US-00.3, US-00.4, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Never write directly to either stock variable.
- Read actual add/reject results from centralized stock effects.
- Keep source production granularity separate from the aggregated ledger key.
- Do not equate the producing country with the location owner without confirmed exposure.
- Accumulate the monthly ledger from production stock-add transactions; never infer it from final stock.
- Route every ledger write through `modeu5_update_production_rejection_ledger`.
- Treat all US-00 persistent values as fields of one logical country × market × good record.
- Keep the country as physical map owner, market as shared key, and good/field in each static map name until nested record storage is confirmed.
- Keep one-operation quantities local until the ledger helper persists their monthly aggregates.
- Use remove/re-add replacement and explicit zero defaults for all numeric map entries.
- Treat void wealth as tracking/proxy data, not a direct monthly Estate-income punishment.
- Keep one approved fallback per missing exposure and make it visible.
- Fold player-facing US-00 visibility into US-10-UI; this epic owns the debug data, not a separate UI layer.

## US-specific boundary checks

- [ ] The correction pipeline targets future production, not direct monthly Estate income.
- [ ] The buffer changes the penalty input, not whether rejected value is tracked.
- [ ] Monthly counters reset only after every downstream consumer has read them.

## Acceptance criteria

- [ ] Produced, added, and rejected quantities remain distinct at `country × market × good`.
- [ ] All US-00 fields form one logical record and their physical maps share the same owner/key convention and lifecycle.
- [ ] Location-level production is attributed to the current ledger country, location market, and good before aggregation.
- [ ] Overproduction, effective ratio, void wealth, and next-month penalty are traceable end to end.
- [ ] US-00 never mutates stock directly.
- [ ] Debug identifies inputs, price source, buffer, modifier mode, fallback, and aggregation.
- [ ] Missing exposure is updated in TECH-01 before gameplay work proceeds.
- [ ] The stock invariant still holds after validation.
- [ ] The PR body documents the runtime closure and each actual test run is recorded as a PR validation comment with dumps and log review.

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

Location production exposure and exact target-good syntax are confirmed by PROBE-021. Building/RGO source-level reconstruction is not required. The deterministic monthly runtime smoke test covers one representative country/market/good; broader balance validation still requires normal monthly ticks across additional countries and goods.

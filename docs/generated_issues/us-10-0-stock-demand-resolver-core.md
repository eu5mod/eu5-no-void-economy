# US-10.0 — Stock Demand Resolver Core

Labels: none

## User Story

```txt
US-10.0 — Stock Demand Resolver Core
```

As a modder, I want a shared stock-demand resolver so consumption and inter-market trade use one candidate, filtering, scoring, ordering, and debug model.

## Functional objective

Implement `modeu5_resolve_stock_demand` as a non-mutating resolver that accepts demand context, builds eligible candidates, scores and orders them, and returns candidate/exclusion diagnostics.

## Runtime position

```txt
Monthly step: called by steps 9 and 11
Depends on: US-01 stocks and confirmed relation/access exposure
Feeds counters to: US-10.1 and US-10.2
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Buyer opinion of seller | country → country | `opinion = { target = <country> value ... }` | CONFIRMED | 067 |
| Trade advantage | market with country context | `merchant_power_in_market` | CONFIRMED | 068 |
| Market access | location | `market_access` | CONFIRMED | 069 |
| Embargo relations | country → country | `is_embargoed_by`, `is_embargoing` | CONFIRMED | 070 |
| War relation | country → country | `is_at_war_with` | CONFIRMED | 071 |
| Subject relation | country → country | `is_subject_of`, `overlord` | CONFIRMED | 072 |
| Market owner | market → country | `owner` | CONFIRMED | 073 |
| Candidate sorting | list/map/typed iterator | ordered iterators with `order_by` | CONFIRMED | 074 |
| Resolver transaction state | current effect/event chain | local variables, saved scopes, and ordered iterator state | CONFIRMED | 008, 074, internal |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_triggers/
in_game/common/scripted_effects/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-01, TECH-01
Blocks: US-10.1 and US-10.2
Related US: US-10.3, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Accept required demand fields and type-specific optional fields.
- Apply hard eligibility filters before scoring.
- Keep coefficients and allow-flags configurable.
- Return candidates, scores, exclusions, reasons, and total available stock.
- Keep candidate lists, scores, exclusions, and remaining quantity local to the resolver call.
- Do not create persistent candidate maps unless a separate debug-snapshot requirement is approved.
- Do not remove/transfer stock or create trade economics.
- Omit unconfirmed scoring components rather than inventing values.

## US-specific boundary checks

- [ ] War and embargo settings are eligibility filters, not score penalties.
- [ ] Wrong good/market, no access, and below-threshold stocks are excluded.
- [ ] Mutation belongs only to US-10.1/US-10.2.

## Acceptance criteria

- [ ] Consumption and inter-market callers can use the same resolver.
- [ ] Invalid candidates are excluded before scoring.
- [ ] Valid candidates are deterministically ordered.
- [ ] Configured own/subject/market-owner/opinion/trade weights are applied only when confirmed.
- [ ] Resolver output is non-mutating.
- [ ] Debug explains every selected or excluded candidate.

## Manual test scenario

### Setup

```txt
Buyer with own, subject, market-owner, foreign, at-war, embargoed, empty, and wrong-market stocks
Run with restrictive allow flags
```

### Expected result

```txt
Only eligible correct-market/good stocks are ordered
Hard-excluded stocks show exact reasons
No stock changes during resolver execution
```

## Known limitations

All required relation, access, ownership, and deterministic ordering primitives are documented. Runtime tests must still validate argument syntax, score direction, and stable tie-breaking.

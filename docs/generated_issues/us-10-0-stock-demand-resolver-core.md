# US-10.0 — Stock Demand Resolver Core

Labels: `blocked:engine-exposure`

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
| Buyer opinion of seller | country → country | opinion value | TO_TEST | 067 |
| Trade advantage | country/market | merchant/trade advantage | TO_TEST | 068 |
| Market access | country/market | access trigger/value | TO_TEST | 069 |
| Embargo/war relations | country → country | embargo/war triggers | TO_TEST | 070-071 |
| Subject/market owner | country/market | relation/scope links | TO_TEST | 072-073 |
| Candidate sorting | script/effect | ordered iterator/sort | TO_TEST | 074 |

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
- Accept required demand fields and type-specific optional fields.
- Apply hard eligibility filters before scoring.
- Keep coefficients and allow-flags configurable.
- Return candidates, scores, exclusions, reasons, and total available stock.
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

All vanilla scoring/relation/access and ordered-sort candidates are `TO_TEST`. Approved fallbacks must omit unavailable dimensions or use deterministic buckets, not fabricate data.

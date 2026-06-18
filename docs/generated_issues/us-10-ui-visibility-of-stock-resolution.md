# US-10-UI — Visibility of Stock, Demand, and Void-Economy Resolution

Labels: none

## User Story

```txt
US-10-UI — Visibility of Stock, Demand, and Void-Economy Resolution
```

As a player or modder, I want to understand where production entered stock, where it was rejected, which stocks fulfilled demand, which candidates were excluded, and why any quantity remained unsatisfied.

## Functional objective

Provide mandatory debug for the full visible stock lifecycle: US-00 production admission and void-economy outcomes, US-10 resolver inputs, ordered candidates, scores, exclusions, quantities per candidate, final demand outcomes, and the consumption/inter-market distinction. A custom ModeU5 panel is optional; deterministic debug events and logs are sufficient for MVP.

## Runtime position

```txt
Monthly step: read after US-00.1/US-00.2/US-00.3/US-00.4 and US-10.1/US-10.2/US-10.3
Depends on counters from: EPIC US-00 and US-10.0 through US-10.3
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| US-00 production admission record | country × market × good | direct reads of produced/added/rejected maps and runtime debug dump fields | CONFIRMED | 021-025 |
| US-00 void-economy record | country × market × good | ratio, effective ratio, void wealth, price source, and penalty fields | CONFIRMED | 025-030 |
| US-00 production modifier diagnostics | country × location × market × good | affected location count and modifier application mode | CONFIRMED | 010, 027-029 |
| Resolver/outcome records | demand/country/market/location/good | current transaction diagnostics plus direct reads of US-10.3 outcome maps | CONFIRMED | 007, 040, 067-077 |
| Debug event and logs | effect scope | event triggers and `debug_log` | CONFIRMED | 013 |
| Localization/tooltips | UI | `custom_tooltip`, modifier descriptions, localization keys | CONFIRMED | 014 |
| Optional custom panel | UI | ModeU5 window | OUT_OF_SCOPE | N/A |

## Files expected to change

```txt
in_game/events/
in_game/localization/
in_game/common/modifiers/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: EPIC US-00, US-10.0, US-10.1, US-10.2, US-10.3, TECH-01
Blocks: transparent stock lifecycle visibility
Related US: US-00-UI, US-04-UI, US-05-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and project debug conventions.
- Debug is mandatory; custom GUI is optional.
- Include the folded US-00-UI requirements: produced, added, rejected, ratio, buffer, void wealth, good price/source, previous/new penalty, affected locations, and modifier mode.
- Show demand type, scope, requested/satisfied/unsatisfied, candidates, scores, quantities, and exclusions.
- Explain that same-market consumption is not trade.
- Explain that logistics costs and trade-income adjustments are outside the surviving MVP story set.
- Keep display read-only.
- Do not create a second authoritative resolver/outcome map for UI. Read US-10.3 aggregates and current transaction diagnostics directly.

## US-specific boundary checks

- [ ] Consumption display shows no transport/trade economics.
- [ ] Production admission display shows no direct Estate-income punishment.
- [ ] Void-economy display distinguishes tracked value, previous penalty application, and next-month prepared penalty.
- [ ] Inter-market display shows source, target, capacity, and actual transfer.
- [ ] Exclusion reasons are human-readable and stable.

## Acceptance criteria

- [ ] Demand type and all quantity outcomes are visible.
- [ ] Produced, added, rejected, ratio, void wealth, and production-penalty diagnostics are visible.
- [ ] Stocks used, order, score, and quantity per candidate are visible.
- [ ] Excluded candidates and reasons are visible.
- [ ] Same-market versus inter-market behavior is explicit.
- [ ] Requested, transferred, and unsatisfied quantities are separately visible for transfers.
- [ ] No logistics or trade-income adjustment is hidden in this display layer.

## Manual test scenario

### Setup

```txt
Run one US-00 monthly runtime smoke test, one multi-stock consumption, and one capacity-limited inter-market transfer
Include at-war, embargoed, empty, and wrong-market candidates where exposed
```

### Expected result

```txt
US-00 shows produced/added/rejected, void wealth, price source, previous/new penalty, and modifier mode
Each demand shows ordered usage and exclusions
Consumption is labeled non-trade
Transfer shows actual quantity and states that logistics/trade-income adjustments are out of scope
```

## Known limitations

MVP may rely on deterministic debug events. A full custom stock-resolution panel is outside scope unless explicitly requested.

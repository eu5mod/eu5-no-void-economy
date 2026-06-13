# US-10-UI — Visibility of Stock Resolution

Labels: none

## User Story

```txt
US-10-UI — Visibility of Stock Resolution
```

As a player or modder, I want to understand which stocks fulfilled a demand, which were excluded, and why any quantity remained unsatisfied.

## Functional objective

Provide mandatory debug for resolver inputs, ordered candidates, scores, exclusions, quantities per candidate, final outcomes, and the consumption/inter-market distinction; optionally expose a ModeU5 panel.

## Runtime position

```txt
Monthly step: read after US-10.1/US-10.2/US-10.3
Depends on counters from: US-10.0 through US-10.3
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Resolver/outcome records | demand/country/market/good | US-10 internal outputs using confirmed resolver primitives | CONFIRMED | 067-077 |
| Debug event and logs | effect scope | event triggers and `debug_log` | CONFIRMED | 013 |
| Localization/tooltips | UI | `custom_tooltip`, modifier descriptions, localization keys | CONFIRMED | 014 |
| Optional custom panel | UI | ModeU5 window | OUT_OF_SCOPE | N/A |

## Files expected to change

```txt
in_game/events/
in_game/localization/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-10.0, US-10.1, US-10.2, US-10.3, TECH-01
Blocks: transparent stock resolution
Related US: US-04-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and project debug conventions.
- Debug is mandatory; custom GUI is optional.
- Show demand type, scope, requested/satisfied/unsatisfied, candidates, scores, quantities, and exclusions.
- Explain that same-market consumption is not trade.
- Explain that logistics costs and trade-income adjustments are outside the surviving MVP story set.
- Keep display read-only.

## US-specific boundary checks

- [ ] Consumption display shows no transport/trade economics.
- [ ] Inter-market display shows source, target, capacity, and actual transfer.
- [ ] Exclusion reasons are human-readable and stable.

## Acceptance criteria

- [ ] Demand type and all quantity outcomes are visible.
- [ ] Stocks used, order, score, and quantity per candidate are visible.
- [ ] Excluded candidates and reasons are visible.
- [ ] Same-market versus inter-market behavior is explicit.
- [ ] Requested, transferred, and unsatisfied quantities are separately visible for transfers.
- [ ] No logistics or trade-income adjustment is hidden in this display layer.

## Manual test scenario

### Setup

```txt
Run one multi-stock consumption and one capacity-limited inter-market transfer
Include at-war, embargoed, empty, and wrong-market candidates where exposed
```

### Expected result

```txt
Each demand shows ordered usage and exclusions
Consumption is labeled non-trade
Transfer shows actual quantity and states that logistics/trade-income adjustments are out of scope
```

## Known limitations

MVP may rely on deterministic debug events. A full custom stock-resolution panel is outside scope unless explicitly requested.

# US-01-UI — Country stocks UI

Labels: none

## User Story

```txt
US-01-UI — Visibilité des stocks nationaux
```

As a player, I want to see how much of each good a country holds in each market and how close that stock is to saturation.

## Functional objective

Expose country, market, good, current stock, capacity, available capacity, and fill ratio through mandatory debug and optional UI.

## Runtime position

```txt
Monthly step: read after stock operations and validation
Depends on counters from: US-01 and US-02
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Stock/capacity values | ModeU5 | US-01 variables | CONFIRMED | 015-018 |
| Debug event and logs | effect scope | event triggers and `debug_log` | CONFIRMED | 013 |
| Localization/tooltips | UI | `custom_tooltip`, modifier descriptions, localization keys | CONFIRMED | 014 |
| Optional stock panel | UI | custom ModeU5 UI | OUT_OF_SCOPE | N/A |

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
Depends on: US-01, US-02, TECH-01
Blocks: visible stock diagnostics
Related US: US-02-UI, US-03-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and project debug conventions.
- Keep UI read-only with respect to stock.
- Show empty, partial, and saturated states unambiguously.
- Display the exact country/market/good scope.
- Keep custom GUI outside MVP unless separately approved.

## US-specific boundary checks

- [ ] Visibility never bypasses centralized stock effects.
- [ ] Fill ratio is calculated from the same stock and capacity scopes.

## Acceptance criteria

- [ ] Current stock, cap, available capacity, and fill ratio are readable.
- [ ] A player can identify saturation before future production is rejected.
- [ ] Values for two markets are not conflated.
- [ ] Debug identifies the exact scope and invariant difference.
- [ ] No hidden stock mutation occurs.

## Manual test scenario

### Setup

```txt
Create empty, half-full, and full country stocks in separate market/good records
Open the supported debug display
```

### Expected result

```txt
Each record shows the correct stock, cap, available capacity, and fill ratio
The full stock is clearly marked as saturated
```

## Known limitations

MVP can use documented debug events, logs, and localization hooks. A custom stock panel remains outside the approved MVP.

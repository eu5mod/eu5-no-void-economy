# US-03-UI — Visibilité du decay mensuel

Labels: none

## User Story

```txt
US-03-UI — Visibilité du decay mensuel
```

As a player, I want to see monthly stock losses so decay does not look arbitrary.

## Functional objective

Expose stock before decay, rate, lost quantity, stock after decay, and an annualized estimate per country, market, and good.

## Runtime position

```txt
Monthly step: read immediately after step 12
Depends on counters from: US-03
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Decay transaction values | ModeU5 | US-03 debug outputs | CONFIRMED | internal |
| Debug event/localization | event/UI | event triggers, logs, tooltips, and localization keys | CONFIRMED | 013-014 |
| Optional custom panel | UI | custom ModeU5 UI | OUT_OF_SCOPE | N/A |

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
Depends on: US-03, TECH-01
Blocks: visible decay diagnosis
Related US: US-01-UI, US-02-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and project debug conventions.
- Keep display logic read-only.
- Show exact scope and mutation effect used.
- Label annualized loss as an estimate.
- Do not require custom GUI for MVP.

## US-specific boundary checks

- [ ] Displayed market loss equals summed country losses.
- [ ] UI does not run a second decay calculation that mutates stock.

## Acceptance criteria

- [ ] Before, rate, loss, after, and annualized estimate are readable.
- [ ] Country/market/good scope is explicit.
- [ ] The invariant result is visible in debug.
- [ ] Values match the centralized decay transaction.

## Manual test scenario

### Setup

```txt
Run decay on a stock of 100 at 1%
Inspect the supported debug display
```

### Expected result

```txt
Before 100; rate 1%; loss 1; after 99
Annualized estimate is clearly non-authoritative
```

## Known limitations

MVP may be debug-only using documented event, log, tooltip, and localization hooks. A custom live panel remains outside scope.

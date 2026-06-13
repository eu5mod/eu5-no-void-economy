# US-09-UI — Visibilité du bonus de Production Efficiency

Labels: `blocked:engine-exposure`

## User Story

```txt
US-09-UI — Visibilité du bonus de Production Efficiency
```

As a player, I want to see that ModeU5 grants a global +5% Production Efficiency compensation and why.

## Functional objective

Expose the modifier value, ModeU5 compensation reason, affected countries, and affected production through confirmed modifier/tooltips or debug.

## Runtime position

```txt
Monthly step: visible while US-09 modifier is active
Depends on counters from: US-09
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Visible country/global modifier | country/UI | confirmed production modifier | TO_TEST | 009, 066 |
| Localization/tooltips | UI | localization files | TO_TEST | 014 |

## Files expected to change

```txt
in_game/common/modifiers/
in_game/localization/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-09, TECH-01
Blocks: visible compensation
Related US: US-00-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Label the bonus as ModeU5 economic compensation.
- Keep display read-only.
- Distinguish it from vanilla national and technology modifiers.

## US-specific boundary checks

- [ ] Displayed value is exactly +5%.
- [ ] Tooltip does not imply immunity to stock constraints.

## Acceptance criteria

- [ ] The active bonus and reason are visible.
- [ ] Affected scope is identifiable.
- [ ] The value matches the applied modifier.
- [ ] No conflicting localization or hidden bonus exists.

## Manual test scenario

### Setup

```txt
Inspect an eligible country's production modifiers with US-09 active
```

### Expected result

```txt
A distinct ModeU5 +5% compensation entry is visible
Its source is not confused with vanilla bonuses
```

## Known limitations

Modifier and tooltip exposure remain `TO_TEST`; debug visibility is the fallback if native modifier UI is insufficient.

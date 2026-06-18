# US-09-UI — Production Efficiency de +5 % bonus UI

Labels: `module:economy`

## User Story

```txt
US-09-UI — Visibilité du bonus de Production Efficiency
```

As a player, I want to see that ModeU5 grants a global +5% Production Efficiency compensation and why.

## Functional objective

Expose the modifier value, ModeU5 compensation reason, affected countries, and affected production through confirmed modifier/tooltips or debug.

## Module / availability

```txt
Package: Rebalance Economy
Activation: optional companion package
Behavior when absent:
  show no ModeU5 +5% compensation modifier or tooltip
  optional general diagnostics may report "Rebalance Economy not loaded"
```

## Runtime position

```txt
Monthly step: visible while US-09 modifier is active
Depends on counters from: US-09
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Visible country modifier | country/UI | `add_country_modifier` using `global_production_efficiency` and a localized description | CONFIRMED | 009, 066 |
| Localization/tooltips | UI | modifier `desc`, `custom_tooltip`, localization keys | CONFIRMED | 014 |

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
Related US: US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/MODULE_OPTION_MODEL.md`.
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

The production modifier, application effect, modifier description, tooltip, and localization hooks are documented. Runtime testing must confirm the final modifier presentation; debug visibility remains the fallback.

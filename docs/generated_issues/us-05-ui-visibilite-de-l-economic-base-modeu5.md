# US-05-UI — Economic Base definition UI

Labels: `blocked:engine-exposure`

## User Story

```txt
US-05-UI — Visibilité de l’Economic Base ModeU5
```

As a player, I want to understand why ModeU5 Stability and Government Power costs differ from vanilla.

## Functional objective

Show the Wealth input, Trade Income input, resulting ModeU5 Economic Base, and which two slider calculations use the replacement formula.

## Runtime position

```txt
Monthly step: read after steps 16-17
Depends on counters from: US-05
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Total wealth output | country | script/UI exposure equivalent to `Country.GetTotalWealth` | TO_TEST | 043 |
| Monthly trade-income output | country | `monthly_trade_income` | CONFIRMED | 042 |
| Economic Base replacement status/output | country/slider | US-05 formula inputs, result, and affected-call-site diagnostics | TO_TEST | 044 |
| Localization/tooltips | UI | `custom_tooltip`, modifier descriptions, localization keys | CONFIRMED | 014 |
| Modifier/debug event path | country/UI | `add_country_modifier`, event triggers, logs | CONFIRMED | 009, 013 |

## Files expected to change

```txt
in_game/common/modifiers/
in_game/events/
in_game/localization/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-05, TECH-01
Blocks: transparent Economic Base replacement
Related US: US-00-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Keep display logic read-only.
- Identify the direct replacement formula and whether its call site is active.
- Show only affected sliders.
- Clearly label optional void-wealth exclusion.

## US-specific boundary checks

- [ ] The player can see Wealth + Trade Income replacing Tax Base.
- [ ] Other slider costs are not presented as ModeU5-modified.

## Acceptance criteria

- [ ] Wealth, Trade Income, and the resulting Economic Base are readable.
- [ ] The affected slider call sites and optional void-wealth impact are readable.
- [ ] The UI does not claim reconciliation is active.
- [ ] Values match the US-05 direct-formula calculation.

## Manual test scenario

### Setup

```txt
Run one country with known Wealth and Trade Income
Inspect the Economic Base debug output and both affected sliders
```

### Expected result

```txt
The replacement formula and its inputs are fully explainable
Unaffected sliders do not claim to use the ModeU5 Economic Base
```

## Known limitations

The event, logging, and localization hooks are documented. Total Wealth is exposed to vanilla GUI, but its gameplay-script equivalent and the Economic Base replacement call site remain `TO_TEST`. Reconciliation display is out of scope.

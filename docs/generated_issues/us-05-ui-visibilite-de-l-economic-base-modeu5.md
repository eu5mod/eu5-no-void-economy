# US-05-UI — Visibilité de l’Economic Base ModeU5

Labels: `blocked:engine-exposure`

## User Story

```txt
US-05-UI — Visibilité de l’Economic Base ModeU5
```

As a player, I want to understand why ModeU5 Stability and Government Power costs differ from vanilla.

## Functional objective

Show vanilla cost, ModeU5 target cost, reconciliation, effective cost, and optional void-wealth correction for each affected slider.

## Runtime position

```txt
Monthly step: read after steps 19-21
Depends on counters from: US-05 and optionally US-05.1
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Slider cost outputs | country/slider | US-05 values | TO_TEST | 041-045 |
| Localization/tooltips | UI | localization files | TO_TEST | 014 |
| Visible modifier/debug event | country/UI | modifier/event | TO_TEST | 009, 013 |

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
Depends on: US-05; optionally US-05.1; TECH-01
Blocks: transparent slider reconciliation
Related US: US-00-UI, US-06-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and no-hidden-reconciliation debug rules.
- Keep display logic read-only.
- Identify direct, monthly reconciliation, and debug-only modes.
- Show only affected sliders.
- Clearly label optional void-wealth exclusion.

## US-specific boundary checks

- [ ] The player can see Wealth + Trade Income replacing Tax Base.
- [ ] Other slider costs are not presented as ModeU5-modified.

## Acceptance criteria

- [ ] Vanilla, target, reconciliation, and effective costs are readable.
- [ ] Correction mode and void-wealth impact are readable when enabled.
- [ ] No economic correction occurs invisibly.
- [ ] Values match US-05/US-05.1 calculations.

## Manual test scenario

### Setup

```txt
Run one country in direct/debug mode and one controlled reconciliation case
Inspect both affected sliders
```

### Expected result

```txt
The cost path and net effective value are fully explainable
Unaffected sliders show no ModeU5 reconciliation
```

## Known limitations

Native slider tooltip integration is `TO_TEST`; a visible country modifier or debug report is an acceptable single fallback.

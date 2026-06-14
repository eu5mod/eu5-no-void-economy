# US-04-UI — Pop demand visibility

Labels: `blocked:engine-exposure`

## User Story

```txt
US-04-UI — Pop demand visibility
```

As a player, I want to understand why local demand for a good is increasing, decreasing, or staying stable.

## Functional objective

Expose base demand, multiplier, simulated demand, satisfaction quantities/ratio, annual counters, threshold, and expected annual change for each location and good.

## Runtime position

```txt
Monthly/yearly step: read after US-10.3 and after annual US-04 adjustment
Depends on counters from: US-04 and US-10.3
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Local demand/counters | location × good | US-04 variables | CONFIRMED | 040 |
| Unmet-need signal/fallback | country × market × good | US-04 shortage signal or US-10.3 unsatisfied Pop-demand outcome | NOT_CONFIRMED | 037 |
| Debug/localized display | event/UI | event triggers, logs, tooltips, and localization keys | CONFIRMED | 013-014 |

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
Depends on: US-04, US-10.3, TECH-01
Blocks: transparent local-demand adaptation
Related US: US-10-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and project debug conventions.
- Keep the display read-only.
- Label the demand source and any simulated fallback.
- Separate location/good records.
- Do not imply that building demand is affected.

## US-specific boundary checks

- [ ] Expected annual change follows only the 12/12 rules.
- [ ] Zero-demand months are visibly neutral.

## Acceptance criteria

- [ ] All specified demand, satisfaction, counter, and multiplier values are readable.
- [ ] The player can distinguish rising, falling, and stable outcomes.
- [ ] The source/fallback for base demand is visible.
- [ ] Building demand is not presented as part of this system.

## Manual test scenario

### Setup

```txt
Inspect one satisfied, one unsatisfied, and one mixed location/good record
```

### Expected result

```txt
The display predicts +1%, -1%, and no change respectively
Counters and satisfaction ratios match US-04 inputs
```

## Known limitations

MVP may expose these values through debug only. Any direct demand or UI exposure remains gated by TECH-01.

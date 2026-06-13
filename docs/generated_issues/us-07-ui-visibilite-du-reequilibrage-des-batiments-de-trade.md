# US-07-UI — Visibilité du rééquilibrage des bâtiments de trade

Labels: `blocked:engine-exposure`

## User Story

```txt
US-07-UI — Visibilité du rééquilibrage des bâtiments de trade
```

As a player, I want trade-building tooltips to explain ModeU5 balance changes.

## Functional objective

Display building name, verified vanilla and ModeU5 power values, changed operating cost, and storage capacity where applicable.

## Runtime position

```txt
Static UI/localization
Depends on counters from: US-07 and US-02
Feeds counters to: player understanding
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Changed building values | static building files | US-07 overrides | TO_TEST | 063 |
| Tooltip/localization hooks | UI | building localization/tooltips | TO_TEST | 014 |
| Storage contribution | ModeU5/building | US-02 configured value | TO_TEST | 034-035 |

## Files expected to change

```txt
in_game/localization/
in_game/common/building_*/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-07, US-02, TECH-01
Blocks: visible trade-building rebalance
Related US: US-02-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Display only confirmed, applied changes.
- Keep tooltip values synchronized with static overrides/configuration.
- Do not hide storage or operating-cost effects.

## US-specific boundary checks

- [ ] Vanilla comparisons use verified source values.
- [ ] No tooltip claims an unimplemented storage contribution.

## Acceptance criteria

- [ ] Modified buildings have coherent, localized tooltips.
- [ ] Power, cost, and storage values match gameplay files.
- [ ] Unmodified buildings are not presented as rebalanced.
- [ ] No new localization or script errors appear.

## Manual test scenario

### Setup

```txt
Inspect each modified trade building in the construction/building UI
```

### Expected result

```txt
Displayed ModeU5 effects match the confirmed static definitions
Storage contribution is shown only where implemented
```

## Known limitations

Tooltip hooks and exact static fields remain `TO_TEST`. Debug/documentation may supplement UI where vanilla tooltips cannot be extended safely.

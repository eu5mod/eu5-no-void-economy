# US-08-UI — Visibilité du prix fixe des RGO et bâtiments

Labels: `blocked:engine-exposure`

## User Story

```txt
US-08-UI — Visibilité du prix fixe des RGO et bâtiments
```

As a player, I want RGO and building prices to clearly show the fixed base and any standard modifiers.

## Functional objective

Expose base price 50, standard modifiers, final displayed price, and removal of dynamic 1.2 effects where the UI permits.

## Runtime position

```txt
Static UI/localization
Depends on counters from: US-08 static definitions
Feeds counters to: player understanding
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Fixed base/dynamic rule status | static files | US-08 values | TO_TEST | 064-065 |
| Price tooltip | UI | vanilla building/RGO tooltip | TO_TEST | 014 |

## Files expected to change

```txt
in_game/localization/
in_game/common/building_*/
in_game/common/rgo_*/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-08, TECH-01
Blocks: visible fixed-price behavior
Related US: US-07-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Keep displayed base and final price synchronized with static files.
- Do not claim dynamic rules are disabled until verified.
- Preserve standard modifier visibility.

## US-specific boundary checks

- [ ] Tooltips distinguish base price from final modified price.
- [ ] No unexplained 1.2 dynamic component remains.

## Acceptance criteria

- [ ] Base 50 is visible or unambiguously documented.
- [ ] Standard modifiers explain final price.
- [ ] Displayed cost matches gameplay cost.
- [ ] Tooltips do not contradict US-08.

## Manual test scenario

### Setup

```txt
Inspect representative in-scope entries under multiple standard modifiers
```

### Expected result

```txt
The base remains 50
Only listed standard modifiers explain final price
```

## Known limitations

Native price tooltip extension remains `TO_TEST`; documentation/debug may supplement the vanilla UI if necessary.

# US-08-UI — RGO & building price realignement UI

Labels: `blocked:engine-exposure`, `module:economy`

## User Story

```txt
US-08-UI — RGO & building price realignement UI
```

As a player, I want RGO and building prices to clearly show the fixed base and any standard modifiers.

## Functional objective

Expose base price 50, standard modifiers, final displayed price, and removal of dynamic 1.2 effects where the UI permits.

## Module / availability

```txt
Package: ModeU5 Economy Rebalance
Activation: optional companion package
Behavior when absent:
  install no US-08-specific price tooltip/localization override
  do not claim that vanilla prices use the ModeU5 base
```

## Runtime position

```txt
Static UI/localization
Depends on counters from: US-08 static definitions
Feeds counters to: player understanding
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Building base/dynamic rules | building type static definition | documented US-08 building price fields | CONFIRMED | 065 |
| RGO base/dynamic rules | RGO/static economy files | documented RGO price fields | NOT_CONFIRMED | 082 |
| Native price tooltip binding | UI | vanilla building/RGO price breakdown | TO_TEST | 085 |
| Localization hooks | UI | building and goods localization keys | CONFIRMED | 014 |

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
- Follow `docs/technical/MODULE_OPTION_MODEL.md`.
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

Building price rules and localization hooks are documented. RGO pricing remains `NOT_CONFIRMED`; native building/RGO price-breakdown tooltip binding remains `TO_TEST`. Documentation/debug may supplement the vanilla UI.

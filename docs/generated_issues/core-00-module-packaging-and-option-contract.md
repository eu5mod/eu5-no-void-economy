# CORE-00 - Module packaging and option contract

Labels: module:core

## User Story

```txt
CORE-00 - Module packaging and option contract
```

As a ModeU5 player, I want one required stock/void-economy core and clearly separated optional rebalance modules so I can choose balance changes without disabling the accounting system that defines the mod.

## Functional objective

Package ModeU5 as:

```txt
ModeU5 Core - Stock-Constrained Economy (required)
ModeU5 Economy Rebalance (optional)
ModeU5 Trade Rebalance (optional)
ModeU5 War Rebalance (optional)
```

Enforce package dependencies, expose the loaded package/version set in debug, and ensure an absent optional package applies no runtime behavior, static override, modifier, or misleading UI.

## Module / availability

```txt
Package: ModeU5 Core
Activation: required and always active when ModeU5 is loaded
Behavior when absent: companion packages fail closed and report the missing dependency
```

## Runtime position

```txt
Launcher/load order: select package set before campaign load
Start-game: validate package/version contract before CORE-02 initialization
Monthly/yearly: no recurring packaging mutation
Depends on counters from: none
Feeds counters to: startup guard and debug
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Separate package descriptors | launcher/mod load | one descriptor and content root per package | CONFIRMED | internal |
| Enforce companion dependency in launcher/playset metadata | launcher/mod descriptor | dependency field or equivalent supported by EU5 launcher | TO_TEST | 103 |
| Custom game-rule definitions | main menu | `main_menu/common/game_rules` | CONFIRMED | 100 |
| Read an active game-rule setting | global script context | `has_game_rule = <setting>` | CONFIRMED | 101 |
| Conditionally gate static building/RGO numeric overrides | static definition | game-rule-dependent static value | NOT_CONFIRMED | 102 |
| Package/version diagnostics | global startup/debug | package-owned marker/version contract | CONFIRMED | internal |

## Persistent storage / variable-map contract

Package metadata is scalar/version configuration, not multidimensional gameplay state.

```txt
logical fields:
  modeu5_core_package_version
  modeu5_economy_package_version, when loaded
  modeu5_trade_package_version, when loaded
  modeu5_war_package_version, when loaded
owner: global startup/debug context
write owner: each package's startup marker
readers: CORE-00 validation and debug
reset lifecycle: never reset during a campaign
```

## Files expected to change

```txt
descriptor.mod or package-specific descriptors
main_menu/common/game_rules/
main_menu/localization/
in_game/common/scripted_triggers/
in_game/common/scripted_effects/
in_game/events/
in_game/localization/
docs/technical/MODULE_OPTION_MODEL.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/TEST_PLAN.md
```

## Dependencies

```txt
Depends on: TECH-01 100-103 and package-layout decision
Blocks: implementation of US-04, US-05, US-07, US-08, US-09, US-13
Related US: every optional module story
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and `docs/technical/MODULE_OPTION_MODEL.md`.
- Do not expose the required Core as a disableable toggle.
- Use companion-package presence as the source of truth for US-07/US-08 static overrides.
- Do not pretend an optional static override is disabled merely by hiding its UI.
- Do not add package checks inside centralized Core stock effects.
- Keep package selection fixed for the campaign unless an explicit migration is implemented.
- Validate matching package versions before optional scripted behavior runs.
- Do not claim startup script can undo a static companion override already loaded without Core.
- Treat companion-without-Core as an unsupported playset until launcher dependency enforcement is confirmed.
- Keep game rules optional and subordinate to package activation.

## CORE-specific boundary checks

- [ ] Core has no supported disabled state.
- [ ] Economy Rebalance absence leaves US-04/05/08/09 inactive.
- [ ] Trade Rebalance absence leaves vanilla US-07 building values untouched.
- [ ] War Rebalance absence leaves vanilla conquest behavior untouched.
- [ ] Missing or mismatched Core is blocked by the launcher when TECH-01 `103` is confirmed, or otherwise produces a prominent unsupported-playset diagnostic.
- [ ] Multiplayer package/version mismatch is visible before gameplay.

## Acceptance criteria

- [ ] The launcher can select Core alone.
- [ ] Each optional companion declares or documents the required matching Core package.
- [ ] Core alone loads without optional modifiers or static overrides.
- [ ] Each optional package activates only its documented US set.
- [ ] Removing an optional package before a new test campaign restores the corresponding vanilla behavior.
- [ ] Startup debug lists all detected ModeU5 package versions.
- [ ] No optional UI claims an inactive feature is enabled.
- [ ] TECH-01 and package-combination tests are updated.

## Manual test scenario

### Setup

Test four clean campaigns:

```txt
1. Core only
2. Core + Economy Rebalance
3. Core + Trade Rebalance
4. Core + War Rebalance
```

### Expected result

```txt
Core stock/void-economy behavior exists in all four campaigns
US-04/05/08/09 behavior exists only in campaign 2
US-07 behavior exists only in campaign 3
US-13 behavior exists only in campaign 4
Startup debug reports the exact package set
No missing-dependency or stale optional effect is present
```

## Known limitations

EU5 custom game rules and `has_game_rule` are confirmed from local vanilla files. Conditional runtime replacement of arbitrary static building/RGO numeric fields is not confirmed, so package separation is required for US-07 and US-08. Automatic launcher dependency enforcement remains `TO_TEST`.

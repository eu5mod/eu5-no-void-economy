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
No Void Economy (required)
Rebalance Economy (optional; included in the recommended playset)
Rebalance Estate Power (optional; included in the recommended playset)
Rebalance Early Blobbing (optional; included in the recommended playset)
```

Publish and document the recommended full-suite playset, enforce package dependencies when launcher exposure permits, expose the loaded package/version set in debug, and ensure a deliberately removed companion applies no runtime behavior, static override, modifier, or misleading UI.

## Module / availability

```txt
Package: No Void Economy
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
| Display package lifecycle warning | launcher/mod metadata | `short_description` rendered in available-mod and selected-playset tooltips | CONFIRMED | 104 |

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
.metadata/metadata.json
descriptor.mod or package-specific descriptors
packages/modeu5_economy_rebalance/
packages/modeu5_trade_rebalance/
packages/modeu5_war_rebalance/
main_menu/common/game_rules/
main_menu/localization/
in_game/common/on_action/
in_game/common/scripted_triggers/
in_game/common/scripted_effects/
in_game/events/
tools/install_local_packages.sh
tools/validate_module_packages.sh
docs/technical/MODULE_OPTION_MODEL.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/TEST_PLAN.md
```

## Dependencies

```txt
Depends on: TECH-01 100-104 and package-layout decision
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
- State that lifecycle rule in every package's mod-manager/playset description.
- Treat the warning as user guidance, not technical enforcement.
- Validate matching package versions before optional scripted behavior runs.
- Do not claim startup script can undo a static companion override already loaded without Core.
- Treat companion-without-Core as an unsupported playset until launcher dependency enforcement is confirmed.
- Keep game rules subordinate to package activation.
- Use the built-in Game Rules screen only for script-safe pre-campaign settings.
- Keep launcher selection as the activation mechanism for optional packages.
- Make the full four-package suite the default/recommended launcher playset.
- Publish the four source package roots as sibling launcher mods.
- Record the installed source branch and commit for local development.
- Never manufacture a companion package marker from Core when its files are absent.
- Do not expose a Core gameplay toggle, an in-game configuration panel, or a fresh-stock reseed action.

## CORE-specific boundary checks

- [ ] Core has no supported disabled state.
- [ ] The default/recommended playset selects all four packages.
- [ ] Rebalance Economy absence leaves US-04/05/08/09 inactive.
- [ ] Rebalance Estate Power absence leaves vanilla US-07 building values untouched.
- [ ] Rebalance Early Blobbing absence leaves vanilla conquest behavior untouched.
- [ ] Missing or mismatched Core is blocked by the launcher when TECH-01 `103` is confirmed, or otherwise produces a prominent unsupported-playset diagnostic.
- [ ] Multiplayer package/version mismatch is visible before gameplay.
- [ ] Game rules cannot change the loaded package set.
- [ ] No custom in-game configuration panel is installed.
- [ ] Every package tooltip says to select the package before campaign start and keep the package set unchanged for that save.

## Acceptance criteria

- [ ] The launcher can select Core alone.
- [ ] The launcher exposes Core, Economy, Trade, and War as four distinct entries after local package installation.
- [ ] A standard ModeU5 installation or documented playset enables all modules by default.
- [ ] Every locally installed package identifies its source branch and commit.
- [ ] Each optional companion declares or documents the required matching Core package.
- [ ] Core alone loads without optional modifiers or static overrides.
- [ ] Each optional package activates only its documented US set.
- [ ] Removing an optional package before a new test campaign restores the corresponding vanilla behavior.
- [ ] Startup debug lists all detected ModeU5 package versions.
- [ ] No optional UI claims an inactive feature is enabled.
- [ ] The ModeU5 debug game rule offers Off, Basic, and Verbose before campaign start.
- [ ] The selected debug rule initializes `modeu5_debug_level` without mutating stock or package state.
- [ ] Fresh stock seeding is absent from all configuration surfaces.
- [ ] The lifecycle warning is visible from both the available-mod list and the selected playset.
- [ ] TECH-01 and package-combination tests are updated.

## Manual test scenario

### Setup

Test the default playset, then four reduced clean campaigns:

```txt
1. Default full suite
2. Core only
3. Core + Rebalance Economy
4. Core + Rebalance Estate Power
5. Core + Rebalance Early Blobbing
```

### Expected result

```txt
All documented modules are active in the default full-suite campaign
Core stock/void-economy behavior exists in all five campaigns
US-04/05/08/09 behavior exists in campaigns 1 and 3
US-07 behavior exists in campaigns 1 and 4
US-13 behavior exists in campaigns 1 and 5
Startup debug reports the exact package set
No missing-dependency or stale optional effect is present
Package descriptions warn that changing the package set for an existing save is unsupported
The built-in Game Rules screen exposes the ModeU5 debug setting
No custom in-game configuration panel is present
```

## Known limitations

EU5 custom game rules and `has_game_rule` are confirmed from local vanilla files. Conditional runtime replacement of arbitrary static building/RGO numeric fields is not confirmed, so package separation is required for US-07 and US-08. Package lifecycle warnings are visible but cannot prevent a user from changing a playset. Automatic launcher dependency enforcement remains `TO_TEST`.

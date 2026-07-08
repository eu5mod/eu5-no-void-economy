# US-CMF-01 — CMF Optionality Placeholders

## User story

As a player, I want the No Void Economy mod to expose its future Community Balance Options in a clear configuration surface, so that I can understand the roadmap and see which options are not available yet without assuming they already affect gameplay.

As a mod developer, I want those options to be represented by stable identifiers now, so future implementation work can safely attach behaviour to each option without renaming user-facing entries later.

## Functional objective

Install the first CMF-compatible optionality layer for No Void Economy by exposing the Community Balance Options from the README as disabled roadmap placeholders.

The MVP must **not** implement the gameplay effects of those options yet. It only creates the pre-campaign visibility layer.

## Options covered

| Option | Label | MVP state | Future target |
|---:|---|---|---|
| 100 | Goods decay | Disabled / roadmap | Countries lose 1% of stored goods monthly |
| 101 | Improved production bonus | Disabled / roadmap | Production bonus per building level becomes 1.5% instead of 1% |
| 200 | No average control penalty | Disabled / roadmap | Remove Average Control Penalty on research speed |
| 300 | Fixed RGO prices | Disabled / roadmap | RGO prices do not scale with market good price |
| 301 | Fixed maintenance price | Disabled / roadmap | Maintenance price does not increase with time |
| 400 | Mercenary nerf | Disabled / roadmap | Adjust mercenary maintenance, prestige cost and/or gathering speed |
| 401 | Adjusted rebel threshold | Disabled / roadmap | Adjust rebel threshold |
| 402 | Shorter wars and War Exhaustion rework | Disabled / roadmap | Rework war exhaustion and shorten wars |
| 500 | Independentist war start | Disabled / roadmap | Independentists do not start the war; initial owner receives a temporary CB |
| 501 | Autonomous Province subject | Disabled / roadmap | Add a new subject type grantable to rebels under specific conditions |
| 502 | Resource persistence | Disabled / roadmap | Annexed subjects transfer ducats, debt, army and navy |

## Implementation scope

Add:

```txt
main_menu/common/game_rules/modeu5_optionality_rules.txt
main_menu/localization/english/modeu5_optionality_rules_l_english.yml
```

The game-rule file must define one rule per option. For this MVP, each rule has only one available setting:

```txt
modeu5_option_<id>_off
```

The localisation must make clear that the setting is:

```txt
Disabled (Roadmap)
```

and that the option is:

```txt
Not yet implemented
```

## Non-goals

This story does not implement:

- stock decay;
- production bonus changes;
- average control penalty changes;
- RGO price overrides;
- maintenance price overrides;
- mercenary rebalance;
- rebel threshold changes;
- war exhaustion gameplay changes;
- independentist CB behaviour;
- autonomous province subject behaviour;
- annexation resource persistence.

This story also does not introduce a custom in-game configuration panel. The configuration surface remains the game-rule / CMF-compatible pre-campaign setup surface.

## Rules and constraints

- Core must not be exposed as a disableable option.
- These options must not claim to be active.
- These options must not mutate stock variables.
- These options must not apply static overrides.
- These options must not change gameplay until a dedicated implementation story is approved.
- Future stories may attach behaviour to the stable `modeu5_option_<id>` identifiers.
- If an option later requires static overrides, the package/module boundary must remain the source of truth.

## Acceptance criteria

- [ ] `modeu5_optionality_rules.txt` exists under `main_menu/common/game_rules/`.
- [ ] `modeu5_optionality_rules_l_english.yml` exists under `main_menu/localization/english/`.
- [ ] Options 100, 101, 200, 300, 301, 400, 401, 402, 500, 501 and 502 are represented.
- [ ] Each option defaults to `off`.
- [ ] Each option has only an off/roadmap setting in this MVP.
- [ ] Each option localisation explicitly indicates that it is disabled or not yet implemented.
- [ ] The feature has no gameplay effect.
- [ ] No stock mutation is introduced.
- [ ] No static economic or military override is introduced.
- [ ] The game starts normally with the options present.

## Manual test plan

1. Install the mod locally.
2. Start EU5 and open the new-game setup flow.
3. Open the game rules screen.
4. Confirm that the ModeU5/NVE roadmap options are visible.
5. Confirm that each option is disabled or only has an off/roadmap state.
6. Start a campaign.
7. Confirm there is no gameplay effect from the placeholder options.
8. Confirm no additional runtime errors are introduced by the game-rule or localisation files.

## Future work

Each option should receive a dedicated implementation story before becoming active. Future implementation PRs should replace the disabled-only placeholder with a validated activation path only when the required engine endpoints are confirmed.

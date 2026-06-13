# #001 — Bootstrap mod structure

## Objective

Create the initial repository and EU5 mod folder structure without implementing gameplay logic.

## Scope

This issue creates only the skeleton required for future implementation and documentation governance.

The bootstrap must reflect the revised ModeU5 specification:

```txt
double accounting of country and market stocks
centralized mutation effects
normative monthly/yearly runtime order
US-00 void-economy ledger and production correction
US-10 stock demand resolution
US-05 direct Economic Base replacement
mandatory TECH-01 exposure tracking
mandatory debug/test conventions
```

## Files / folders to create

```txt
modeu5_country_stocks/
├── descriptor.mod
├── .metadata/
│   └── metadata.json
├── README.md
├── CLAUDE.md
├── AGENTS.md
├── docs/
│   ├── issues/
│   │   ├── 001_bootstrap_mod_structure.md
│   │   ├── 002_add_claude_agents.md
│   │   ├── 003_engine_exposure_matrix.md
│   │   └── 004_test_plan_debug_conventions.md
│   ├── templates/
│   │   ├── github_issue_template.md
│   │   └── pull_request_template.md
│   ├── technical/
│   │   ├── TECH-01_engine_exposure_matrix.md
│   │   └── DEBUG_CONVENTIONS.md
│   └── tests/
│       └── TEST_PLAN.md
├── in_game/
│   ├── common/
│   │   ├── scripted_values/
│   │   ├── scripted_triggers/
│   │   ├── scripted_effects/
│   │   ├── modifiers/
│   │   └── on_actions/
│   ├── events/
│   └── localization/
└── tools/
```

## Acceptance criteria

- [ ] Repository structure exists.
- [ ] `descriptor.mod` exists.
- [ ] `.metadata/metadata.json` exists.
- [ ] Documentation folders exist.
- [ ] Templates exist.
- [ ] No gameplay logic is implemented.
- [ ] The mod can be copied into the local EU5 mod folder.
- [ ] The mod appears in the launcher or fails only with a documented metadata/path issue.
- [ ] README states the central stock invariant and centralized mutation rule.
- [ ] README states that runtime order is normative and implementation order is only a delivery roadmap.

## Manual test

1. Copy `modeu5_country_stocks` to the EU5 local mod folder.
2. Enable the mod in the launcher.
3. Launch the game.
4. Check `error.log`, `game.log`, and `system.log`.

## Expected result

```txt
The mod is detected.
The game starts.
No blocking script errors are introduced.
No gameplay logic is executed.
```

## Out of scope

```txt
stock logic
monthly cycle
void economy tracking
US-10 demand resolver
US-05 Economic Base implementation
UI/debug events
balance changes
AI behavior
```

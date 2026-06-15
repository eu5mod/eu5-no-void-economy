# #001 — Bootstrap mod structure

## Objective

Historical bootstrap contract for the repository and EU5 package structure. The
current repository now contains gameplay code, so this issue documents the
required foundation rather than the present implementation status.

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
eu5voideco/
├── descriptor.mod
├── .metadata/
│   └── metadata.json
├── .github/
│   └── ISSUE_TEMPLATE/
│       ├── github_issue_template.md
│       └── pull_request_template.md
├── README.md
├── CLAUDE.md
├── AGENTS.md
├── docs/
│   ├── issues/
│   │   ├── 001_bootstrap_mod_structure.md
│   │   ├── 002_add_claude_agents.md
│   │   ├── 003_engine_exposure_matrix.md
│   │   └── 004_test_plan_debug_conventions.md
│   ├── technical/
│   │   ├── TECH-01_engine_exposure_matrix.md
│   │   └── DEBUG_CONVENTIONS.md
│   └── tests/
│       └── TEST_PLAN.md
├── in_game/
│   ├── common/
│   │   ├── script_values/
│   │   ├── scripted_triggers/
│   │   ├── scripted_effects/
│   │   ├── modifiers/
│   │   └── on_action/
│   ├── events/
│   └── localization/
├── packages/
│   ├── modeu5_economy_rebalance/
│   ├── modeu5_trade_rebalance/
│   └── modeu5_war_rebalance/
└── tools/
```

## Acceptance criteria

- [ ] Repository structure exists.
- [ ] `descriptor.mod` exists.
- [ ] `.metadata/metadata.json` exists.
- [ ] Documentation folders exist.
- [ ] Templates exist.
- [ ] The bootstrap commit itself introduces no gameplay logic.
- [ ] The mod can be copied into the local EU5 mod folder.
- [ ] The mod appears in the launcher or fails only with a documented metadata/path issue.
- [ ] README states the central stock invariant and centralized mutation rule.
- [ ] README states that runtime order is normative and implementation order is only a delivery roadmap.

## Manual test

1. Run `./tools/install_local_packages.sh`.
2. Run `./tools/install_local_packages.sh --check`.
3. Verify `MODEU5_SOURCE.txt` and that no stale duplicate shadows
   `modeu5_core`.
4. Enable the intended packages in the launcher.
5. Launch the game.
6. Check `error.log`, `game.log`, and `system.log`.

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

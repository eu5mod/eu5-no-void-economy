# US-13 — CB Rebalancing

Labels: `blocked:engine-exposure`, `module:war`

## User Story

```txt
US-13 — CB Rebalancing
```

As a player, I want early conquest to cost more for non-horde countries while hordes retain vanilla conquest behavior.

## Functional objective

Provide age-specific conquest CB/wargoal variants for non-hordes: add `0.40` in Ages I-II, add `0.20` in Age III, and use vanilla cost from Age IV onward. Horde countries always use vanilla variants.

## Module / availability

```txt
Package: Rebalance Early Blobbing
Activation: optional companion package
Behavior when absent:
  install or select no ModeU5 conquest-cost variant
  preserve vanilla CB/wargoal behavior
```

## Runtime position

```txt
CB/wargoal selection at availability/use time
Depends on: attacker government classification, current age, static conquer_cost field
Feeds counters to: conquest cost calculation
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Non-horde check | attacker country | `NOT = { government_type = government_type:steppe_horde }` | CONFIRMED | 078 |
| Current age | current script context | `current_age` | CONFIRMED | 079 |
| Conquest CB/wargoal cost | static CB/wargoal files | `conquer_cost` or equivalent override | CONFIRMED | 080 |
| Age/government variant selection | country/CB | confirmed `current_age` and `steppe_horde` check plus static cost hook | NOT_CONFIRMED | 080 |

## Files expected to change

```txt
in_game/common/casus_belli/
in_game/common/wargoals/
in_game/common/scripted_triggers/
in_game/localization/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: local vanilla CB/wargoal files and TECH-01 confirmation
Blocks: none in core stock MVP
Related US: none
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/MODULE_OPTION_MODEL.md`.
- Do not assume `conquer_cost` is dynamically mutable.
- Prefer explicit static variants selected by confirmed age and horde checks.
- Apply fixed additions, not an additional multiplier.
- Keep horde and Age IV+ behavior vanilla.
- Do not implement until TECH-01 080 confirms the conquest-cost override.

## US-specific boundary checks

- [ ] Ages I-II non-horde cost is vanilla plus `0.40`.
- [ ] Age III non-horde cost is vanilla plus `0.20`.
- [ ] Age IV+ and all horde costs remain vanilla.
- [ ] No stock/economic systems are coupled to this rule.

## Acceptance criteria

- [ ] Confirmed non-horde and age checks select the correct variant.
- [ ] Horde countries always retain vanilla conquest CB/wargoal cost.
- [ ] Non-horde additions match the target age bands.
- [ ] No extra multiplier is applied.
- [ ] Localization distinguishes ModeU5 variants where needed.
- [ ] Vanilla CB/wargoal files outside the approved conquest set remain unchanged.
- [ ] TECH-01 and controlled tests cover every age/horde combination.

## Manual test scenario

### Setup

```txt
One horde and one non-horde attacker
Test representative conquest in Ages I, II, III, and IV
Record vanilla and ModeU5 conquer_cost
```

### Expected result

```txt
Non-horde: +0.40, +0.40, +0.20, +0.00 by age
Horde: +0.00 in every age
Correct CB/wargoal variant and trigger path are visible in debug
```

## Known limitations

`current_age` and the exact vanilla `government_type = government_type:steppe_horde` check are confirmed. The static conquest-cost override remains `NOT_CONFIRMED`, so US-13 remains excluded from implementation.

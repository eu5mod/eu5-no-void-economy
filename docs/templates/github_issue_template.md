# GitHub Issue Template — ModeU5 User Story

## User Story

```txt
US-XX — Title
```

## Functional objective

Describe what the feature must do in gameplay terms.

## Runtime position

```txt
Monthly step:
Yearly step:
Depends on counters from:
Feeds counters to:
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| | | | TO_TEST | |

Status values:

```txt
CONFIRMED
NOT_CONFIRMED
FALLBACK_ACCEPTED
OUT_OF_SCOPE
TO_TEST
```

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_triggers/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/common/modifiers/
in_game/events/
in_game/localization/
docs/technical/
docs/tests/
```

## Dependencies

```txt
Depends on:
Blocks:
Related US:
```

## Implementation rules

- Do not mutate stock variables directly.
- Use centralized stock effects only.
- Add debug output.
- Update TECH-01 if any vanilla exposure is tested.
- Do not widen MVP.
- Do not apply silent reconciliation.
- Do not implement more than one fallback path without approval.

## US-specific boundary checks

- [ ] If US-00: tracks void economy and future production correction, not direct monthly Estate income punishment.
- [ ] If US-10.1: consumption inside one market remains stock resolution, not intra-market trade.
- [ ] If US-10.2: applies only when `source_market != target_market`.
- [ ] If US-06: cost uses `transferred_quantity` when available and never unsatisfied demand.
- [ ] If US-05: only Stability and Court/Government Power are affected.
- [ ] If US-05.1: feature is optional/MVP+ and must be visibly documented.

## Acceptance criteria

- [ ] Feature works in a controlled manual test.
- [ ] Debug output shows expected values.
- [ ] No negative stocks persist.
- [ ] Market stock equals sum of country stocks after validation.
- [ ] Reconciliation, if any, is visible in debug/UI/modifier/tooltip.
- [ ] Missing exposure, if any, is recorded in TECH-01.
- [ ] `error.log` has no new blocking error.
- [ ] Documentation updated.

## Manual test scenario

### Setup

```txt
Country:
Market:
Good:
Initial stock:
Capacity:
Production or demand:
Trade source market:
Trade target market:
Relevant config parameters:
```

### Expected result

```txt
Expected country stock:
Expected market stock:
Expected added quantity:
Expected rejected quantity:
Expected satisfied quantity:
Expected unsatisfied quantity:
Expected transferred quantity:
Expected reconciliation if any:
Expected debug output:
```

## Known limitations

Document any fallback, unconfirmed engine exposure, debug-only behavior, or theoretical-only modifier.

# GitHub Issue Template — ModeU5 User Story

## User Story

```txt
US-XX — Title
```

## Functional objective

Describe what the feature must do in gameplay terms.

## Module / availability

```txt
Package: No Void Economy | Rebalance Economy | Rebalance Estate Power | Rebalance Early Blobbing
Activation: required | optional companion package
Behavior when absent:
```

Follow `docs/technical/MODULE_OPTION_MODEL.md`. Optional stories must define a true no-effect state when their package is absent.

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

## Persistent storage / variable-map contract

Complete this section when the story owns durable multidimensional state. Otherwise state why the values remain scalar, static, or transaction-local.

```txt
logical dimensions:
logical record and fields:
owner scope:
tuple/key:
confirmed physical map family:
physical value type:
default value:
write owner:
readers:
reset/rebuild lifecycle:
```

Rules:

- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Treat related fields as one logical record even when current engine exposure requires several synchronized physical maps.
- Do not claim one native variable-map value contains inline fields or another map unless TECH-01 `088` is confirmed.
- Do not assume runtime map-name construction.
- Distinguish the logical record owner from the confirmed physical map owner.
- Use a global per-good map keyed by market for the market aggregate.
- Use generated per-good adapters with complete literal map identifiers.
- Replace existing map entries by read, remove, and re-add.
- Keep one-operation arithmetic, candidate state, and saved scopes transaction-local.
- Do not duplicate source-of-truth state for UI/debug.

## Files expected to change

```txt
in_game/common/script_values/
in_game/common/scripted_triggers/
in_game/common/scripted_effects/
in_game/common/on_action/
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
- Do not apply silent economic adjustments.
- Do not implement more than one fallback path without approval.
- Use `min = <lower bound>` and `max = <upper bound>` with EU5's
  bound-oriented semantics.
- Keep expected business-rule rejections in debug/results, not `error.log`.

## US-specific boundary checks

- [ ] If US-00: tracks void economy and future production correction, not direct monthly Estate income punishment.
- [ ] If US-10.1: consumption inside one market remains stock resolution, not intra-market trade.
- [ ] If US-10.2: applies only when `source_market != target_market`.
- [ ] If US-10.2: requested, transferred, and unsatisfied quantities remain distinct.
- [ ] If US-05: only Stability and legitimacy-producing Court/Government Power are affected.
- [ ] If US-05: direct formula replacement is used; no reconciliation fallback is introduced.

## Acceptance criteria

- [ ] Feature works in a controlled manual test.
- [ ] Debug output shows expected values.
- [ ] No negative stocks persist.
- [ ] Market stock equals sum of country stocks after validation.
- [ ] Any economic adjustment is visible in debug/UI/modifier/tooltip.
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
Expected economic adjustment if any:
Expected debug output:
```

## Known limitations

Document any fallback, unconfirmed engine exposure, debug-only behavior, or theoretical-only modifier.

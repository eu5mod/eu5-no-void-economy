# #004 — Add test plan and debug conventions

## Objective

Create the testing and debug conventions that every future PR must follow.

The documents must reflect the surviving specification, including US-00 ledger/penalty, US-10 stock demand resolution, US-05 direct Economic Base replacement, and the no-hidden-adjustment rule.

## Files to create

```txt
docs/tests/TEST_PLAN.md
docs/technical/DEBUG_CONVENTIONS.md
```

## Test plan must include

```txt
manual test scenario template
error.log / game.log / system.log review requirement
core stock invariant tests
same-market transfer test
inter-market transfer test
decay test
rebuild safety test
generated-adapter literal-identifier validation
unset deterministic result-marker test
local install provenance and stale-duplicate check
US-00 void economy tracking tests
US-00 monthly reset ordering test
multi-market country test
US-10 consumption resolution tests
US-10 candidate exclusion tests
US-10 inter-market capacity test
US-04 demand adaptation tests
US-05 direct Economic Base test
static balance tests
US-13 exposure-gated test
PR test report template
```

## Debug conventions must include

```txt
debug naming convention
debug levels
mandatory debug per stock mutation
mandatory debug for US-00
mandatory debug for US-04
mandatory debug for US-05
mandatory debug for US-10
fallback debug
economic-adjustment visibility rule
error policy
stock inconsistency policy
unconfirmed modifier/effect policy
```

## Acceptance criteria

- [ ] TEST_PLAN exists.
- [ ] DEBUG_CONVENTIONS exists.
- [ ] Test plan includes stock accounting tests for add/remove/transfer/decay/rebuild.
- [ ] Test plan includes US-00 overproduction tests.
- [ ] Test plan includes multi-market country test.
- [ ] Test plan includes US-10 consumption and inter-market transfer tests.
- [ ] Test plan includes the US-05 direct Economic Base test.
- [ ] Debug conventions include required stock mutation debug fields.
- [ ] Debug conventions include US-10 candidate/exclusion debug.
- [ ] Debug conventions include US-05 Wealth source and formula-hook debug.
- [ ] Debug conventions include fallback reporting.
- [ ] Debug conventions prohibit hidden economic adjustments.
- [ ] Expected business-rule rejections are distinguished from failed
      assertions and engine errors.
- [ ] Deterministic result UI uses marker presence rather than numeric
      comparison against an unset variable.

## Manual review checklist

- [ ] Can a future agent know how to validate a PR?
- [ ] Can a future agent know what to print in debug?
- [ ] Does the test plan cover the invariant `market_good_stock = sum(country_market_good_stock)`?
- [ ] Does the test plan cover `country × market × good` void tracking?
- [ ] Does the test plan prevent same-market consumption from being treated as trade?
- [ ] Does the test plan keep requested, transferred, and unsatisfied quantities distinct?
- [ ] Does the debug convention make fallbacks and economic adjustments visible?

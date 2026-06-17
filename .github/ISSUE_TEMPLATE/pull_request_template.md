# Pull Request Template — ModeU5

## Objective

Describe the testable layer implemented by this PR.

```txt
Example: core stock mutation effects
Example: US-00.1 production rejection ledger
Example: US-10.0 stock demand resolver core
```

## Related issue(s)

```txt
Closes #
Related #
```

## Runtime position

Where does this PR sit in the ModeU5 runtime sequence?

```txt
Monthly step:
Yearly step:
Not a runtime feature:
```

## Files changed

```txt

```

## Engine exposure

- [ ] TECH-01 updated if any vanilla scope/value/effect/modifier/on_action/static field was tested.
- [ ] No dependency on `TO_TEST` or `NOT_CONFIRMED` exposure remains without an accepted fallback.
- [ ] Any fallback is visible in debug.
- [ ] Only one fallback path is implemented for each missing exposure.
- [ ] Loaded data paths use confirmed EU5 names such as `common/script_values/`.

## Generated adapters

- [ ] Generated stock adapters were regenerated when their template or goods list changed.
- [ ] Generated output is idempotent and was not hand-edited.
- [ ] Every physical map identifier is literal and contains no remaining `$`.
- [ ] Stock arithmetic and business rules remain in shared scripted effects, not the shell generator.

## Stock mutation rule

- [ ] No direct stock variable mutation outside centralized stock effects.
- [ ] `modeu5_add_stock` used where relevant.
- [ ] `modeu5_remove_stock` used where relevant.
- [ ] `modeu5_transfer_stock` used where relevant.
- [ ] `modeu5_decay_stock` used where relevant.
- [ ] `modeu5_validate_stock_consistency` or rebuild path used where relevant.

## Runtime boundary checks

- [ ] US-00 does not directly punish monthly Estate income.
- [ ] US-10 same-market consumption does not create trade income, transport cost, or trade capacity usage.
- [ ] US-10.2 records requested, transferred, and unsatisfied quantities separately.
- [ ] US-05 affects only Stability and Court/Government Power unless explicitly approved.
- [ ] US-05 uses direct formula replacement and does not introduce a reconciliation fallback.

## Debug

- [ ] Debug output added.
- [ ] Fallback debug added if fallback is used.
- [ ] Adjustment debug added if any economic correction is applied.
- [ ] `error.log`, `game.log`, and `system.log` reviewed.
- [ ] Expected business-rule rejections do not create engine/error diagnostics.
- [ ] Deterministic result events use marker presence checks for possibly unset variables.

## Test plan

### Scenario

### Expected result

### Debug output to inspect

### Logs to inspect

```txt
error.log
game.log
system.log
debug.log when the feature emits deterministic dumps
```

### TECH-01 entries updated

### Known limitations

### Fallbacks used

### Local install provenance to verify

```txt
MODEU5_SOURCE.txt checked:
Duplicate/stale mod entry checked:
Installed branch/commit:
```

## Validation comments

- [ ] Actual test results are posted as PR comments, not edited into this PR body.
- [ ] Each test-result comment names the tested commit SHA and installed package provenance.
- [ ] Each test-result comment includes the exact console command/event or scenario run.
- [ ] Each deterministic test-result comment includes the relevant dump lines from the logs.
- [ ] Each retest after a new commit is added as a new PR comment, preserving the previous result history.

## MVP boundary check

- [ ] Does not implement full building-level profit reconstruction.
- [ ] Does not implement RGO-level profit reconstruction.
- [ ] Does not implement advanced AI economic planner.
- [ ] Does not replace vanilla markets.
- [ ] Does not implement intra-market trade profit simulation.
- [ ] Does not implement multiple competing fallbacks for one missing exposure.

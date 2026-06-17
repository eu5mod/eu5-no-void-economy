# US-14 — Autonomous Rebel Status Demands

Labels: `blocked:engine-exposure`, `module:war`, `enhancement`

blocked:engine-exposure

## User Story

```txt
US-14 — Autonomous Rebel Status Demands
```

As an overlord, I want eligible rebel-controlled continuous regions to demand autonomous subject status instead of full independence, so internal unrest can produce constrained self-government without automatically destroying sovereignty.

## Functional objective

When a rebel movement would normally demand or enforce independence, ModeU5 may replace that outcome with an autonomous subject outcome if all eligibility checks pass.

Eligible rebels may request:

```txt
before 1637: autonomous_territory
from 1637 onward: autonomous_province
```

The affected territory must be released as one continuous autonomous subject under the original overlord. Disconnected rebel pockets are not granted autonomous status by this rule.

Autonomous subjects remain under the sovereignty of their overlord, have no independent foreign policy, and receive internal self-government and local privileges from their subject type definition.

## Module / availability

```txt
Package: Rebalance Early Blobbing
Activation: optional companion package
Behavior when absent:
  vanilla rebel independence demands and enforcement remain unchanged
  no autonomous rebel-demand replacement is installed or selected
```

Follow `docs/technical/MODULE_OPTION_MODEL.md`. This story belongs to the war/early-blobbing companion and must not be implemented in Core.

## Runtime position

```txt
Monthly step: none
Yearly step: none
Depends on counters from: vanilla rebel movement progress/support and rebel-controlled territory
Feeds counters to: none
```

Runtime hook point:

```txt
rebel demand generation / rebel enforcement resolution
```

CORE-03 remains responsible for stock succession after any resulting location ownership change. US-14 must not create a parallel stock-transfer path.

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Intercept or replace a rebel independence demand | rebel movement / demand context | rebel-demand definition, rebel enforcement hook, or on_action | TO_TEST | 118 |
| Read rebel support as a share of rebellion threshold | rebel movement | support/progress value divided by threshold; require `>= 0.90` | TO_TEST | 119 |
| Identify rebel-controlled territory | rebel movement → locations | iterator over locations controlled by the movement | TO_TEST | 120 |
| Majority religion condition in rebel-controlled territory | rebel territory / religion | majority religion of controlled locations or Pops | TO_TEST | 121 |
| Overlord tolerance of Heathen Belief above threshold `X` | overlord country / religion policy | tolerance value for Heathen Belief; business threshold `X` | TO_TEST | 122 |
| Majority culture and tolerated-culture condition | rebel territory / overlord country | majority culture in controlled territory plus culture acceptance/tolerated trigger | TO_TEST | 123 |
| Overlord power-rank condition for EU5 1.3.0+ | overlord country | Regional Power or Great Power trigger/value | TO_TEST | 124 |
| Territorial continuity with overlord capital | rebel-controlled locations / capital / pathing | continuous land/path graph from rebel territory to overlord capital | TO_TEST | 125 |
| Release a continuous rebel region as a subject instead of an independent country | rebel outcome / country creation | release/create country and attach to overlord with subject type | TO_TEST | 126 |
| Autonomous subject type keys | subject type database | `subject_type:autonomous_territory`, `subject_type:autonomous_province` | TO_TEST | 127 |
| Autonomous subject behavior | subject type database | no independent foreign policy, internal self-government, local privileges | TO_TEST | 128 |

## Persistent storage / variable-map contract

This story does not own durable ModeU5 multidimensional state.

```txt
logical dimensions: none
logical record and fields: none
owner scope: none
tuple/key: none
confirmed physical map family: none
physical value type: none
default value: none
write owner: none
readers: none
reset/rebuild lifecycle: none
```

Any implementation should use transaction-local variables and saved scopes while resolving one rebel demand. Persistent debug markers may be added only for deterministic test events, not as gameplay state.

## Files expected to change

```txt
packages/modeu5_war_rebalance/in_game/common/rebel_types/
packages/modeu5_war_rebalance/in_game/common/rebel_demands/
packages/modeu5_war_rebalance/in_game/common/subject_types/
packages/modeu5_war_rebalance/in_game/common/scripted_triggers/
packages/modeu5_war_rebalance/in_game/common/scripted_effects/
packages/modeu5_war_rebalance/in_game/common/on_action/
packages/modeu5_war_rebalance/in_game/events/
packages/modeu5_war_rebalance/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

Exact paths remain subject to TECH-01 exposure. Do not create all listed paths mechanically if the confirmed hook belongs elsewhere.

## Dependencies

```txt
Depends on: TECH-01 118-128
Blocks: autonomous rebel-demand implementation
Related US: US-13, CORE-03
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/MODULE_OPTION_MODEL.md`.
- Implement only in the Rebalance Early Blobbing / war companion package.
- Keep the Core package behavior unchanged when the war companion is absent.
- Do not mutate stock variables directly.
- Do not introduce a second CORE-03 stock-succession dispatcher; location ownership changes must flow through the confirmed CORE-03 owner-change path.
- Do not replace full independence unless every eligibility condition is confirmed and passes.
- Treat `X` as a business parameter to define before implementation; do not hardcode an invented tolerance threshold.
- Use `autonomous_territory` before 1637 and `autonomous_province` from 1637 onward unless a later design decision changes the date boundary.
- Apply the Regional Power / Great Power requirement only when the EU5 1.3.0+ exposure is confirmed; otherwise keep the story blocked.
- Refuse autonomous status to disconnected pockets. If continuity cannot be proven, fail closed to vanilla behavior or a debug-only report.
- Keep expected business-rule rejection in debug/results, not `error.log`.
- Update TECH-01 when every rebel, subject, power-rank, and continuity endpoint is tested.

## US-specific boundary checks

- [ ] Rebel support/progress is at least `90%` of the rebellion threshold.
- [ ] Either the religion/tolerance branch or the culture/tolerated branch passes.
- [ ] The overlord is a Regional Power or Great Power in EU5 1.3.0+.
- [ ] The autonomous territory is continuous with the capital.
- [ ] Disconnected pockets are not granted autonomous status by this rule.
- [ ] The outcome remains an overlord subject, not full independence.
- [ ] Autonomous subjects have no independent foreign policy.

## Acceptance criteria

- [ ] Controlled test creates one eligible rebel movement.
- [ ] Debug output shows rebel support, threshold, religion branch result, culture branch result, overlord power rank, continuity result, selected subject type, and outcome.
- [ ] Eligible pre-1637 rebels create an `autonomous_territory` subject.
- [ ] Eligible 1637+ rebels create an `autonomous_province` subject.
- [ ] Ineligible rebels keep vanilla behavior or show an explicit debug-only rejection.
- [ ] Disconnected pockets are excluded or rejected according to the confirmed continuity model.
- [ ] CORE-03 stock succession handles any location ownership changes without a duplicate transfer path.
- [ ] Missing exposure, if any, is recorded in TECH-01.
- [ ] `error.log` has no new blocking ModeU5 error.
- [ ] Documentation and manual tests are updated.

## Manual test scenario

### Setup

```txt
Country: one Regional Power or Great Power overlord
Rebel movement: controlled test movement with >= 90% rebellion threshold support
Rebel-controlled territory: one continuous region connected to the overlord capital
Religion branch: majority religion plus Heathen Belief tolerance > X
Culture branch: majority culture plus tolerated culture
Date case A: before 1637
Date case B: 1637 or later
Relevant config parameters: X, 90% threshold, EU5 version gate
```

### Expected result

```txt
Expected pre-1637 outcome: continuous autonomous_territory subject under overlord
Expected 1637+ outcome: continuous autonomous_province subject under overlord
Expected rejected-pocket outcome: no autonomous status for disconnected pockets
Expected debug output:
  rebel support / threshold
  religion majority and tolerance value
  culture majority and tolerated-culture result
  overlord power rank
  continuity result
  chosen subject type
  final subject creation result
```

## Known limitations

- All rebel-demand and rebel-enforcement hooks are `TO_TEST`.
- The exact script exposure for rebel support, rebellion threshold, and rebel-controlled territory is unknown.
- The exact script exposure for majority religion/culture over rebel-controlled locations is unknown.
- The exact trigger/value for Heathen Belief tolerance and culture tolerated status is unknown.
- The Regional Power / Great Power condition is explicitly limited to EU5 1.3.0+ and still needs a confirmed runtime/static endpoint.
- The continuity/pathing endpoint for refusing pockets is unknown.
- The subject type keys `autonomous_territory` and `autonomous_province` are provided by design/spec but must be confirmed against the target EU5 version or local subject-type files before implementation.

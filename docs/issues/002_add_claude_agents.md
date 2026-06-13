# #002 — Add CLAUDE.md / AGENTS.md

## Objective

Add agent instructions that prevent uncontrolled implementation, invented scope links, direct stock variable mutation, hidden economic reconciliation, and accidental MVP widening.

## Files to create

```txt
CLAUDE.md
AGENTS.md
```

## Required content

The agent instructions must include:

```txt
project goal
central invariant
country stock as source of truth
market stock as aggregate/cache
centralized stock mutation rule
documentation-first rule
engine exposure matrix rule
normative monthly runtime order
normative yearly runtime order
implementation roadmap
current canonical US-00
current canonical US-10
current canonical US-06
US-05 / US-05.1 boundary
MVP boundaries
debug requirement
testing rule
Git / PR rule
blocked-work procedure
```

## Non-negotiable rules

The files must explicitly state:

```txt
No US may directly mutate stock variables.
All stock mutations must go through centralized scripted effects.
No vanilla scope/value/effect/modifier may be assumed without verification.
TECH-01 must be updated when exposure is tested.
Runtime order is normative.
Implementation order is only a delivery roadmap.
US-00 is void tracking plus future production correction, not direct monthly Estate income punishment.
US-10 same-market consumption is stock resolution, not intra-market trade.
US-06 uses trade/import/export scopes when exposed and monthly reconciliation by default.
US-06 must not calculate cost on unsatisfied demand.
US-05.1 is optional/MVP+ unless needed to avoid double penalty.
When blocked, propose one fallback only.
```

## Acceptance criteria

- [ ] `CLAUDE.md` exists.
- [ ] `AGENTS.md` exists.
- [ ] Both documents mention the stock invariant.
- [ ] Both documents mention centralized mutation effects.
- [ ] Both documents mention TECH-01.
- [ ] Both documents distinguish runtime order from implementation order.
- [ ] Both documents mention the canonical US-00 pipeline.
- [ ] Both documents mention the US-10 no-intra-market-trade rule.
- [ ] Both documents mention US-06 trade/import/export inspection and monthly reconciliation.
- [ ] Both documents instruct the agent to stop when blocked.

## Manual review checklist

- [ ] Does the document prevent scope invention?
- [ ] Does it prevent implementation beyond MVP?
- [ ] Does it force debug/test output?
- [ ] Does it identify US-00 as void tracking + production correction, not direct monthly punishment?
- [ ] Does it prevent same-market consumption from becoming pseudo-trade?
- [ ] Does it prevent hidden transport-cost or slider reconciliation?

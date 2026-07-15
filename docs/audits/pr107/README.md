# PR107 Audit — US-17 / US-20 trade reconciliation workflow state

> **Classification:** historical PR checkpoint. It preserves US-17/US-20
> evidence but does not define the current global runtime. See
> [`docs/architecture/RUNTIME_FLOW.md`](../../architecture/RUNTIME_FLOW.md).

## Purpose

This folder is the historical workflow checkpoint for PR #107:

```txt
US-17 / US-20: Maintenance and buy/sell efficiency in Q8.7 route loop
```

The goal is to preserve the state of the master PR as an audit artifact, even though PR #107 does not have a formal stack of sub-PRs.

This follows the Q8 audit discipline:

```txt
- keep inherited historical documents intact;
- create a PR-owned source of truth for current workflow state;
- distinguish implemented, validated, rerun-required, expected-blocked, and out-of-scope surfaces;
- make the next workflow decision explicit.
```

## Historical source context

Read these first:

| Source | Why it matters |
| --- | --- |
| `docs/audits/q8/README.md` | Defines the audit-folder pattern and the rule that an implementation track owns its current Q-docs instead of rewriting inherited history. |
| `docs/audits/q8/archives/Q5_flux_logique_global.md` | Preserves the Q8.7-era monthly workflow evidence; `RUNTIME_FLOW.md` now defines live ordering. |
| `docs/generated_issues/us-17-trade-reconciliation.md` | US-17 issue/specification surface. |
| `docs/generated_issues/us-20-trade-maintenance-goods-reconciliation.md` | US-20 issue/specification surface. |
| `docs/tests/TEST-US-20-trade-maintenance-goods-reconciliation.md` | Runtime validation protocol and US20 four-case probe status. |
| `docs/technical/TECH-01_engine_exposure_matrix.md` | Engine-exposure boundary, especially unresolved trade-profit / country-income display-accounting surfaces. |

## PR107-owned documents

```txt
docs/audits/pr107/archives/Q5_workflow_state.md
```

## Rule for this folder

This checkpoint is closed and archived. Do not update its Q5 to represent new
runtime behavior. Update `RUNTIME_FLOW.md`, the feature specification, and a
new dated proof record when a follow-up changes one of these surfaces:

```txt
- execution order;
- loop ownership;
- US17/US20 implementation status;
- validation status;
- blocker status;
- merge/non-merge decision;
- out-of-scope boundary.
```

Do **not** rewrite Q8, PR126, or TECH-01 historical documents just to reflect PR107 state. Link to them and record the PR107 delta here.

## Completion definition

This audit checkpoint is complete when it records:

```txt
- inherited baseline;
- current PR107 workflow state;
- implemented surfaces;
- validated surfaces;
- rerun-required surfaces;
- expected-blocked surfaces;
- out-of-scope/follow-up surfaces;
- merge decision checklist.
```

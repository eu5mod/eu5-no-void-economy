# Q8 Audit — optimisation implementation source of truth

Source request: create a new master PR after #126 merged into `main`, similar to PR #126, starting with an audit that leads to Q8 implementation.

This folder promotes the Q8 findings from the PR126 audit into their own implementation track. The PR should begin as documentation and audit only. Runtime code PRs should be stacked later, one testable optimisation layer at a time.

## Relationship to PR126

PR126 established the current post-refactor baseline:

```txt
country pulse preparation
+ promoted-market local branch through the current market-center ownership workaround
+ country trade-owner pass
+ validation / reconciliation
```

Q8 must not reopen PR126's baseline unless a measured probe proves a safer and cheaper replacement. Q8 implementation work should preserve the PR126 contracts while reducing repeated monthly work and clarifying ownership boundaries.

## Source documents from PR126

Read these first:

| Source | Why it matters |
|---|---|
| `docs/audits/pr126/Q5_flux_logique_global.md` | Current monthly ordering and target workflow |
| `docs/audits/pr126/Q5.1_current_global_flow.md` | Post-PR144/Q4.1/PR7.1 live-flow checkpoint and guarded-dispatch diagram |
| `docs/audits/pr126/Q8_future_optimisations.md` | Original F1–F7 future optimisation list |
| `docs/audits/pr126/Q8_F9_location_cache_rolling_verification.md` | Location-derived dirty-set and rolling verification idea |
| `docs/audits/pr126/Q8_F9_TECH01_storage_compatibility.md` | Storage constraints and narrowing of F9 |
| `docs/audits/pr126/Q8_F9C_market_sliced_verifier.md` | Market-sliced verifier probe and Performance Mode variant |
| `docs/technical/PERSISTENT_STATE_AUDIT.md` | Persistent map/list classification rules |
| `docs/technical/TECH-01_engine_exposure_matrix.md` | Confirmed and unconfirmed engine exposure |

Q5.x flow clarifications belong with Q5, not with the Q8 future-optimisation findings. If a Q5.2 checkpoint is added later, place it as a Q5 subsection or immediate follow-up to Q5.1 before the Q8 documents in this reading order.

## Q8-owned audit methodology

Q8 follows the same methodology as PR126, but with a different objective: optimize the post-PR126 runtime shape rather than establish the original refactor baseline.

The Q8 audit owns its own Q1–Q5 documents under this folder:

```txt
docs/audits/q8/Q1_architecture_fichiers.md
docs/audits/q8/Q2_systeme_cache.md
docs/audits/q8/Q3_redondances_code.md
docs/audits/q8/Q4_boucles_performance.md
docs/audits/q8/Q5_flux_logique_global.md
```

Stacked Q8 PRs should update the affected Q8 Q-docs directly. They should not mutate the inherited PR126 Q1–Q5 documents unless the change intentionally corrects historical PR126 documentation.

## Q8 target outcome

The target is not one large runtime rewrite. The target is an ordered optimisation programme:

```txt
1. Audit current main after PR126.
2. Classify Q8 findings into safe implementation layers.
3. Add probes before live behaviour changes.
4. Convert only proven probes into runtime changes.
5. Keep each implementation PR small, reversible, and independently validated.
```

## Priority map

| Track | Summary | Starting status | First action |
|---|---|---|---|
| Q8.0 | Post-PR126 baseline audit | Required | Document current hot-path contracts and counters |
| Q8.1 / F3 | Remove or gate temporary PR7.1 profiling counters | Likely safe after validation | Audit unconditional hot-path metric writes |
| Q8.2 / F2 | Verify US-10 aggregate pending-request gating | Audit first | Trace request bucket flow before adding a gate |
| Q8.3 / F1 | Capacity pool stamping | Candidate optimisation | Identify country-wide capacity-pool recalculation surfaces |
| Q8.4 / F4 | Split legacy guarded helpers from body helpers | Candidate optimisation | Inventory generated helper callers and guards |
| Q8.5 / F5/F9a | Dirty-set architecture for market/country caches | Promising | Probe owner-change dirtying and derived-cache consumers |
| Q8.6 / F9c | Market-sliced verifier | Probe only | Prove deterministic candidate-market slicing and dirty-market skip |
| Q8.7 / F7 | Native global market-local pass | High-impact, high-risk | Confirm `every_market_in_world` monthly/global execution before implementation |

## Non-negotiable guardrails

```txt
1. No stock mutation outside central stock operators.
2. No market-scope variable dependency unless TECH-01 confirms it.
3. No runtime-built map names or helper names.
4. No broad monthly world scan unless the audit proves it replaces more work than it adds.
5. No verifier may mutate stock.
6. No Q8 implementation may weaken the two-pass invariant: all US-00 admission facts before US-10 same-market consumption.
7. Performance Mode must verify candidate/promoted/relevant markets, not the whole world, unless the PR is explicitly a debug-only world-coverage probe.
8. Each new cache must define owner, rebuild/write trigger, reset policy, and persistent-state audit classification.
9. Each implementation PR must include a deterministic debug event or log evidence.
```

## Completion definition for this master PR

This master PR is complete when it provides:

```txt
- a Q8 audit source of truth;
- a split implementation backlog;
- explicit non-goals and guardrails;
- agent instructions for stacked PRs;
- no live runtime behaviour change unless separately requested and validated.
```

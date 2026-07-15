# Audit Documentation Catalog

Audit documents preserve investigation evidence, probe results, and the state
of a particular PR or optimization track. They are historical or
feature-scoped. The only normative global runtime diagram is
[`docs/architecture/RUNTIME_FLOW.md`](../architecture/RUNTIME_FLOW.md).

This catalog covers all 54 audit documents that existed when the global index
was introduced. `tools/validate_audit_catalog.py` keeps it exhaustive as the
repository evolves.

## Classification

| Status | Meaning |
|---|---|
| Feature reference | Current detail for one feature only; never a global runtime authority. |
| Historical baseline | State or design captured for a completed PR/refactor. |
| Proof record | Probe, runtime result, or validation evidence retained for traceability. |
| Superseded | Replaced by a named newer document. |
| Archive | Deliberately retained rejected or older investigation material. |

## PR107: US-17 and US-20

| Document | Status | Current authority |
|---|---|---|
| [README](./pr107/README.md) | Historical baseline | This catalog and `RUNTIME_FLOW.md` |
| [Q5 workflow state](./pr107/archives/Q5_workflow_state.md) | Historical baseline | `RUNTIME_FLOW.md`; feature contracts remain in US-17/US-20 specifications |

## PR126: architecture refactor baseline

All PR126 diagrams describe the refactor baseline or a proposal at that point
in time. `RUNTIME_FLOW.md` supersedes them for the live global order.

| Document | Status | Current authority |
|---|---|---|
| [README](./pr126/README.md) | Historical baseline | `RUNTIME_FLOW.md` |
| [Agent refactor instructions](./pr126/AGENT_REFACTOR_INSTRUCTIONS.md) | Historical baseline | `AGENTS.md` |
| [PR6.1 runtime fix notes](./pr126/PR6_1_RUNTIME_FIX_NOTES.md) | Proof record | Current runtime and tests |
| [PR7.1 active-good root cause](./pr126/PR7.1_ACTIVE_GOOD_ROOT_CAUSE.md) | Proof record | Current generated dispatchers |
| [PR7.1 review checklist](./pr126/PR7.1_REVIEW_CHECKLIST.md) | Proof record | Current generator validators |
| [Q1 file architecture](./pr126/Q1_architecture_fichiers.md) | Historical baseline | Current repository plus technical contracts |
| [Q2 cache system](./pr126/Q2_systeme_cache.md) | Historical baseline | `PERSISTENT_STATE_AUDIT.md` and storage contracts |
| [Q3 redundancy](./pr126/Q3_redondances_code.md) | Historical baseline | Current generator model |
| [Q4 loops and performance](./pr126/Q4_boucles_performance.md) | Historical baseline | `RUNTIME_FLOW.md` |
| [Q4.1 factorization conclusions](./pr126/Q4.1_factorisation_intermediate_conclusions.md) | Historical baseline | `RUNTIME_FLOW.md` |
| [Q5 global logical flow](./pr126/archives/Q5_flux_logique_global.md) | Superseded | `RUNTIME_FLOW.md` |
| [Q5.1 current global flow](./pr126/archives/Q5.1_current_global_flow.md) | Superseded | `RUNTIME_FLOW.md` |
| [Q5.2 active-good root cause](./pr126/archives/Q5.2_active_good_root_cause.md) | Proof record | Current generated dispatchers and validators |
| [Q6 functional description](./pr126/Q6_description_fonctionnelle.md) | Historical baseline | Current specifications and `AGENTS.md` |
| [Q8 future optimizations](./pr126/Q8_future_optimisations.md) | Historical baseline | Q8 audit track |
| [Q8/F9 rolling location cache](./pr126/Q8_F9_location_cache_rolling_verification.md) | Proof record | Current cache implementation and Q8 records |
| [Q8/F9 TECH-01 compatibility](./pr126/Q8_F9_TECH01_storage_compatibility.md) | Proof record | `TECH-01_engine_exposure_matrix.md` |
| [Q8/F9c market-sliced verifier](./pr126/Q8_F9C_market_sliced_verifier.md) | Proof record | Current Q8 verifier implementation |
| [Q8.7 Q1-Q5 impact](./pr126/Q8.7_Q1_Q5_impact.md) | Proof record | `RUNTIME_FLOW.md` |

## PR176: stock operators

| Document | Status | Current authority |
|---|---|---|
| [Stock operator contract and penalty position](./pr176/stock_operator_contract_and_penalty_position.md) | Feature reference | Central stock operators, `AGENTS.md`, and static validators |

## PR69: US-04 probes

Q5 v3 is the current feature-level US-04 record. It does not replace the global
runtime document.

| Document | Status | Current authority |
|---|---|---|
| [README](./pr69/README.md) | Feature reference | Q5 v3 for US-04; `RUNTIME_FLOW.md` globally |
| [Q5 v3](./pr69/Q5_flux_logique_global.v3.md) | Feature reference | This document for US-04 only |
| [Q11 read-probe design](./pr69/us04_q11_pop_demand_read_probe_design_2026-07-12.md) | Proof record | Q5 v3 and TECH-01 |
| [Q11 read-probe runtime](./pr69/us04_q11_pop_demand_read_runtime_2026-07-12.md) | Proof record | Q5 v3 and TECH-01 |
| [Archived Q5 v2](./pr69/archives/Q5_flux_logique_global.v2.md) | Superseded | Q5 v3 |
| [Runtime validation 2026-07-11](./pr69/archives/runtime_validation_2026-07-11.md) | Archive | Q5 v3 |
| [US-04 status 2026-07-11](./pr69/archives/us04_current_status_2026-07-11.md) | Archive | Q5 v3 |
| [Final probe lessons and pivot](./pr69/archives/us04_final_probe_lessons_and_reconciliation_pivot_2026-07-11.md) | Archive | Q5 v3 |
| [Injection matrix result](./pr69/archives/us04_injection_matrix_runtime_result_2026-07-11.md) | Archive | Q5 v3 |
| [Injection candidate 1](./pr69/archives/us04_injection_probe_candidate_1_2026-07-11.md) | Archive | Q5 v3 |
| [Observed-current alternative](./pr69/archives/us04_observed_current_demand_alternative.md) | Archive | Q5 v3 |
| [Q10 replacement lifecycle runtime](./pr69/archives/us04_q10_q10b_q10c_replacement_lifecycle_runtime_2026-07-11.md) | Archive | Q5 v3 |
| [Q7/Q8 observed-current runtime](./pr69/archives/us04_q7_q8_and_observed_current_runtime_2026-07-11.md) | Archive | Q5 v3 |
| [Q9 replace-pop-demand runtime](./pr69/archives/us04_q9_replace_pop_demand_runtime_2026-07-11.md) | Archive | Q5 v3 |

Invalid-syntax probe fixtures under
`pr69/archives/goods_demand_invalid_syntax/` are evidence files, not Markdown
documentation and not loadable package content.

## Q8: optimization track

Q8 records the proof stack that produced the current Q8.7 switch.
`RUNTIME_FLOW.md` describes the resulting live orchestration.

| Document | Status | Current authority |
|---|---|---|
| [README](./q8/README.md) | Historical baseline | `RUNTIME_FLOW.md` |
| [Agent instructions](./q8/AGENT_Q8_INSTRUCTIONS.md) | Historical baseline | `AGENTS.md` |
| [Q1 file architecture](./q8/Q1_architecture_fichiers.md) | Historical baseline | Current repository and technical contracts |
| [Q2 cache system](./q8/Q2_systeme_cache.md) | Historical baseline | Current persistent-state documentation |
| [Q3 redundancy](./q8/Q3_redondances_code.md) | Historical baseline | Current generator model |
| [Q4 loops and performance](./q8/Q4_boucles_performance.md) | Historical baseline | `RUNTIME_FLOW.md` |
| [Q5 global logical flow](./q8/archives/Q5_flux_logique_global.md) | Superseded | `RUNTIME_FLOW.md` |
| [Q8.0 baseline audit](./q8/Q8_0_POST_PR126_BASELINE_AUDIT.md) | Historical baseline | Current runtime and this catalog |
| [Q8.0 baseline results](./q8/Q8_0_POST_PR126_BASELINE_RESULTS.md) | Proof record | Current runtime tests |
| [Q8.1/Q8.3 implementation](./q8/Q8_1_Q8_3_IMPLEMENTATION.md) | Proof record | Current implementation |
| [Q8.2-Q8.7 probe clearance](./q8/Q8_2_Q8_4_Q8_5_Q8_6_Q8_7_PROBE_CLEARANCE.md) | Proof record | Current implementation and tests |
| [Q8.2/Q8.5 implementation](./q8/Q8_2_Q8_5_IMPLEMENTATION.md) | Proof record | Current implementation |
| [Q8.6 implementation](./q8/Q8_6_IMPLEMENTATION.md) | Proof record | Current verifier implementation |
| [Q8.7 global pass proof](./q8/Q8_7_GLOBAL_MARKET_LOCAL_PASS_PROOF.md) | Proof record | `RUNTIME_FLOW.md` |
| [Q8.7 live owner switch](./q8/Q8_7_LIVE_GLOBAL_MARKET_OWNER_SWITCH.md) | Proof record | `RUNTIME_FLOW.md` |
| [Q8.7 Performance work shape](./q8/Q8_7_PERFORMANCE_MARKET_OWNER_WORKSHAPE_PROOF.md) | Proof record | Current Performance-mode tests |
| [Q8/F9 TECH-01](./q8/Q8_F9_TECH01.md) | Proof record | `TECH-01_engine_exposure_matrix.md` |
| [Q8 implementation backlog](./q8/Q8_IMPLEMENTATION_BACKLOG.md) | Historical baseline | Current issues and implementation |

## Maintenance rule

- Global runtime diagrams belong only in `docs/architecture/RUNTIME_FLOW.md`.
- Every Markdown file below `docs/audits/`, except this catalog, must appear
  exactly once as a Markdown link in this file.
- New audit documents must state whether they are historical, proposed,
  feature-specific, superseded, or archived.
- Do not rewrite old evidence to look current. Classify it and point to its
  replacement.

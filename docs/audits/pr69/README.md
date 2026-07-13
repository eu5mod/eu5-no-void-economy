# PR #69 audit index

## Source Of Truth

Read this first:

```txt
Q5_flux_logique_global.v3.md
```

Q5 v3 consolidates the probing history and is the current source of truth for
US-04:

```txt
Annual coefficient layer:       implemented
Vanilla pop_demand mutation:    rejected for production
Monthly stock reconciliation:   blocked pending TECH-01 149/150
Estate charge:                  confirmed endpoint, not used until exact location Estate demand is confirmed
```

## Historical Evidence

These files remain useful, but they are archives. If they disagree with Q5 v3,
Q5 v3 wins.

```txt
archives/Q5_flux_logique_global.v2.md
archives/runtime_validation_2026-07-11.md
archives/us04_current_status_2026-07-11.md
archives/us04_injection_probe_candidate_1_2026-07-11.md
archives/us04_injection_matrix_runtime_result_2026-07-11.md
archives/us04_q7_q8_and_observed_current_runtime_2026-07-11.md
archives/us04_q9_replace_pop_demand_runtime_2026-07-11.md
archives/us04_q10_q10b_q10c_replacement_lifecycle_runtime_2026-07-11.md
archives/us04_observed_current_demand_alternative.md
archives/us04_final_probe_lessons_and_reconciliation_pivot_2026-07-11.md
```

Archived invalid-syntax `goods_demand` probe definitions are preserved outside
all loadable packages:

```txt
docs/audits/pr69/archives/goods_demand_invalid_syntax/
```

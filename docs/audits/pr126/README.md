# PR #126 Audit — historical refactor baseline

> **Classification:** historical architecture baseline. Its Q1-Q8 reports
> explain the refactor and proposed ownership split; they are no longer the
> current global runtime source of truth. See
> [`docs/architecture/RUNTIME_FLOW.md`](../../architecture/RUNTIME_FLOW.md).

Source request: GitHub PR #126, “Developement balance”.

This folder is the preserved context for the PR126 stacked refactor. The Q1-Q6
reports remain canonical evidence for that historical change, while Q8 records
the optimization ideas that followed it.

## Reading order for an agent

| Step | Report | Use it to |
|---|---|---|
| 1 | [Q1 — File architecture](./Q1_architecture_fichiers.md) | Choose the owning file before changing code |
| 2 | [Q2 — Cache system](./Q2_systeme_cache.md) | Identify source, derived cache, work cache, ledger, or debug state |
| 3 | [Q3 — Code redundancy](./Q3_redondances_code.md) | Distinguish acceptable generated repetition from duplication to refactor |
| 4 | [Q4 — Loops and performance](./Q4_boucles_performance.md) | Evaluate scan cost and the promoted-market target |
| 5 | [Q5 — Global logical flow](./Q5_flux_logique_global.md) | Understand the PR126-era workflow and target workflow |
| 6 | [Q6 — Functional description](./Q6_description_fonctionnelle.md) | Translate business rules into code guardrails |
| 7 | [Q8 — Future optimisations](./Q8_future_optimisations.md) | Track follow-up performance findings without widening the active PR |
| 8 | [Q8/F9 — Rolling location cache](./Q8_F9_location_cache_rolling_verification.md) | Evaluate the location owner/market cache, rolling verification, and Q4 win estimate |
| 9 | [Q8/F9 — TECH-01 storage compatibility](./Q8_F9_TECH01_storage_compatibility.md) | Constrain F9 against variable-map storage limits, early-exit limits, and dirty-set-first design |
| 10 | [Q8/F9c — Market-sliced verifier](./Q8_F9C_market_sliced_verifier.md) | Evaluate deterministic market slicing, candidate-list slicing, count probes, and Performance Mode viability |
| 11 | [Q8.7 — Q1 to Q5 impact](./Q8.7_Q1_Q5_impact.md) | Read the Q8.7/F7 shadow-comparison consequences for Q1–Q5 before switching live runtime |
| 12 | [AGENT instructions](./AGENT_REFACTOR_INSTRUCTIONS.md) | Start the refactor PR stack |

## Global executive summary

The mod is structured around real domains: `stock`, `capacity`, `void economy`, `demand resolver`, `performance`, `configuration`, `debug`, `tools`, and `templates`. The foundation is healthy, but the release risk remains the accumulation of broad monthly flows and convention-synchronized caches.

Since `developement-balance` was resynchronized with the #119/#130/#131 stack, the recommendations below must reuse the existing contracts: performance/promotion boundaries, US-10 UI, canonical goods registry, templates, and generator validators. An agent must not recreate a parallel model.

The PR126 monthly target is ownership-split: country pulse prepares country-owned work, the promoted-market local branch runs once per promoted market, and the country-scope trade pass handles only trades assigned to the current country.

## Release-risk summary table

| Priority | Issue | Release impact | Affected files | Recommended action | Effort |
|---|---|---|---|---|---|
| P0 | Runtime scripts rely on many convention-synchronized maps | Silent divergence is possible if a helper bypasses central operators | `cbp_stock_effects.txt`, `VARIABLE_MAP_STORAGE_MODEL.md` | Add an automated check for direct writes outside helpers | M |
| P0 | The monthly workflow is still broad-flow rather than promoted-market driven | US-00, US-10, validation, and debug may rescan or rebuild their own world | `cbp_stock_effects.txt`, `cbp_void_economy_effects.txt`, `cbp_stock_demand_resolver_effects.txt` | Introduce the promoted-market dispatcher progressively in test-only mode, then compare modes | L |
| P1 | Additive scheduling caches have no confirmed element-level removal | Over-validation or increasing cost after long campaigns | `cbp_performance_effects.txt`, generated adapters | Document owner, rebuild trigger, and reset policy for each cache | S |
| P1 | US-00 reasoning mixes ingestion facts and finalization/carryover | Risk of recalculating a penalty from post-consumption/post-decay stock | `cbp_void_economy_effects.txt`, generated adapters | Freeze produced/added/rejected/ratio inputs before US-10, decay, and reconciliation | M |
| P1 | CMM configuration, runtime gates, and package markers are scattered | Contributor confusion and false runtime-toggle assumptions | `main_menu`, `cbp_configuration_effects.txt`, `cbp_cmm_runtime_effects.txt` | Maintain a single configuration index | S |
| P2 | Several probes contain long and similar scenarios | Costly maintenance when contracts change | `packages/cbp_core_tests/...` | Factor dump conventions, not business scenarios | M |
| P2 | Historical optional package names are less aligned with the current contract | Playset confusion before release | `packages/*/descriptor.mod`, `MODULE_OPTION_MODEL.md` | Rename only if compatible; otherwise document the alias | M |

## Non-negotiable contracts for the PR126 stack

```txt
1. Do not mutate stocks outside the central operators.
2. Do not rebuild country stock from market stock.
3. Do not use runtime-built map names.
4. Do not add a private goods list inside a generator.
5. Do not add a cache without owner, rebuild trigger, reset policy, and audit classification.
6. Do not use every_trade outside its TECH-01 confirmed country scope, and do not use every_market_center in gameplay without TECH-01 confirmation or an accepted fallback.
7. Do not treat every_market_promoted as a native engine iterator.
8. Do not run promoted-market local mutations once per country present; use a once-per-promoted-market dispatcher or deterministic owner guard.
9. Do not recompute the month's US-00 facts after consumption, transfer, decay, validation, or reconciliation.
```

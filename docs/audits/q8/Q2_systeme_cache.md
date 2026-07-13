# Q2 — Q8 cache system and ownership

## Purpose

Q8 optimises the post-PR126 runtime by narrowing repeated work. That requires a clear distinction between source state, derived caches, work caches, debug/profile metrics, and normal-runtime reusable scalar facts.

This document is the Q8-owned cache standard. Stacked Q8 PRs must update it when they introduce or materially change cache ownership, rebuild triggers, reset policy, or source-vs-cache classification.

## Current cache classes relevant to Q8

| Family / state | Owner | Class | Source of truth? | Q8 rule |
|---|---|---|---:|---|
| `cbp_<good>_stock_by_market` | country | authoritative stock map | Yes | Never write outside central stock operators / generated adapter surface. |
| `cbp_<good>_market_stock` | global | derived market-good aggregate | No | Rebuild/validate from country stock; never treat as country source. |
| `cbp_stock_cap_by_market` | country | country-market capacity record | Yes for stock admission cap | Refresh before stock admission; market-specific contribution must stay current. |
| `cbp_base_capacity_by_market` / breakdown maps | country | explanation/debug breakdown | No | Keep with capacity refresh; do not drive business independently. |
| `cbp_countries_present_in_market` | global | rebuilt work cache | No | Rebuild for current promoted/target market; not durable per-market storage. |
| `cbp_market_country_cache_dirty_markets` | global | dirty scheduling list | No | Scheduling only; Q8.5 repairs affected work-cache consumers but does not create durable per-market storage. |
| `cbp_market_sliced_verifier_candidate_markets` | global | debug/audit verifier candidate list | No | Q8.6 scheduling only; built from dirty/promoted market lists, cleared each verifier run. |
| `cbp_market_sliced_verifier_*` counters | global | debug/audit verifier counters | No | Diagnostic only; must not drive stock mutation. |
| `cbp_promoted_markets_this_cycle` | global | current-cycle work list | No | Current-cycle scheduling only; separate from detailed promotion readiness. |
| `cbp_detailed_accounting_promoted_markets` | global | readiness / promotion work cache | No stock truth | Must not bypass business readiness checks. |
| `cbp_performance_relevant_markets` | global | Performance Mode relevance work list | No | Rebuilt by relevance preparation; may be consumed by future market-local owner, but must not become stock truth. |
| `cbp_pr71_*` counters | global | debug/profile metrics | No | Metrics only; normal runtime should not pay per-good metric writes unless enabled. |

## Cache design questions for stacked Q8 PRs

Every new Q8 cache or scalar work state must answer:

```txt
1. Who owns it? country, global, current promoted market helper, generated adapter, debug/probe.
2. What class is it? source, derived cache, work cache, monthly ledger, debug/profile metric, scalar reusable fact.
3. What triggers a rebuild or write?
4. What invalidates it?
5. What reads it?
6. Can it influence business logic, or is it scheduling/diagnostic only?
7. Does tools/audit_cbp_persistent_state.sh need to classify it?
```

## Q8.0 baseline decision

Q8.0 adds no new runtime cache.

It classifies the likely Q8 cache-impacting tracks:

```txt
Q8.1 — metric/counter gating, no business cache change.
Q8.3 — likely normal-runtime scalar country capacity-pool cache.
Q8.5 — dirty-set/cache producer-consumer probe before new cache model.
Q8.6 — debug-only verifier work lists, probe-only until proven.
```

## Q8.1 update — PR7.1 metric gating

Q8.1 keeps PR7.1 counters classified as debug/profile metrics:

```txt
cbp_pr71_us00_goods_considered
cbp_pr71_us00_goods_processed
cbp_pr71_us00_goods_produced_gate_hits
cbp_pr71_us00_goods_previous_state_hits
cbp_pr71_us10_goods_considered
cbp_pr71_us10_pending_request_hits
cbp_pr71_us10_requests_processed
```

Ownership and lifecycle:

```txt
owner: global debug/profile metric surface
trigger: cbp_pr71_metrics_enabled_trigger
enabled in: debug capture or audit runtime
normal runtime: no per-good metric writes
business source: no
```

The business guards remain active even when metrics are disabled.

## Q8.3 update — country capacity-pool scalar cache

Q8.3 introduces reusable country-scope scalar cache facts:

```txt
cbp_capacity_pool_monthly_stamp
cbp_capacity_pool_cached_location_rank_capacity
cbp_capacity_pool_cached_location_count
cbp_capacity_pool_cached_market_count
cbp_capacity_pool_cached_base
cbp_capacity_pool_cached_total
cbp_capacity_pool_cached_location_rank_per_market
```

Classification:

```txt
class: scalar derived/work cache
owner: country scope
source of truth: no
business source: no
rebuild trigger: first public country capacity-pool calculation in a given month, or after invalidation
invalidation: cbp_rebuild_country_location_capacity_pool -> cbp_clear_country_storage_capacity_pool_cache
reader: cbp_apply_country_storage_capacity_pool_to_current_market
```

Important distinction:

```txt
The cached scalar pool facts do not replace country-market capacity maps.
cbp_stock_cap_by_market and capacity breakdown maps remain the country-market capacity records read by stock admission and UI/debug.
```

## Q8.5 probe update — dirty cache lifecycle

PR #150 adds a test-package dirty-cache lifecycle probe:

```txt
cbp_q8_probe_dirty_cache_lifecycle
```

The probe marks the capital market dirty, runs the existing dirty repair consumer, and checks that the repair count is greater than zero.

It confirms the current writer/consumer surface can be exercised:

```txt
cbp_mark_market_country_cache_dirty
cbp_repair_dirty_market_country_caches
cbp_market_country_cache_dirty_markets
```

It does not add a new dirty cache model and does not mutate stock.

## Q8.2 / Q8.5 implementation update

Q8.2 is deferred.

Rejected runtime cache shape:

```txt
cbp_pr71_us10_country_market_has_pending_request
```

Reason:

```txt
A temporary aggregate country-market pending flag requires an all-goods pre-scan.
If most country-market pairs have at least one pending request, that pre-scan adds work before the existing per-good pending dispatcher.
```

Preferred later cache/scheduler shape:

```txt
request writer -> sparse pending country-market or country-market-good list
monthly US-10 -> iterate sparse pending work list -> clear after processing
```

Q8.5 adds the guarded dirty repair consumer:

```txt
cbp_repair_dirty_market_country_caches_if_needed
```

Boundary:

```txt
cbp_countries_present_in_market remains a rebuilt current-market work cache.
cbp_market_country_cache_dirty_markets remains scheduling state only.
Q8.5 does not confirm durable per-market country-list storage.
```

## Q8.6 implementation update

Q8.6 adds bounded verifier scheduling state:

```txt
cbp_market_sliced_verifier_candidate_markets
cbp_market_sliced_verifier_candidates_built
cbp_market_sliced_verifier_candidates_checked
cbp_market_sliced_verifier_candidates_passed
cbp_market_sliced_verifier_candidates_failed
cbp_market_sliced_verifier_last_run_skipped
cbp_market_sliced_verifier_last_run_empty
cbp_market_sliced_verifier_last_run_failed
cbp_market_sliced_verifier_last_run_passed
```

Classification:

```txt
owner: global verifier/debug surface
class: verifier candidate list and diagnostic counters
source of truth: no
business source: no
write trigger: cbp_run_market_sliced_verifier_candidates
reader: debug/audit inspection only
```

The verifier uses candidate markets from:

```txt
cbp_market_country_cache_dirty_markets
cbp_promoted_markets_this_cycle
```

It may rebuild `cbp_countries_present_in_market` for each candidate market to verify the market-country work-cache path. It does not mutate stock, does not repair stock, and does not clear dirty scheduling lists.

## Q8.7 proof-stack update

Q8.7 adds no new production cache. It exercises existing work/relevance surfaces from the test package and clarifies the business meaning of one existing production cache surface.

The proof stack now classifies the following diagnostic state as probe-only:

```txt
test_cbp_q8_7_global_market_seen_markets
test_cbp_q8_7_shadow_comparison_center_markets
test_cbp_q8_7_shadow_comparison_global_markets
test_cbp_q8_7_perf_relevant_cache_rebuild_count
test_cbp_q8_7_perf_relevant_country_count
test_cbp_q8_7_perf_relevant_human_country_count
test_cbp_q8_7_perf_relevant_ai_country_count
test_cbp_q8_7_current_owner_cache_rebuild_count
test_cbp_q8_7_candidate_global_cache_rebuild_count
test_cbp_q8_7_noop_current_* counters
test_cbp_q8_7_noop_global_* counters
```

Classification:

```txt
owner: test-package Q8.7 probe surface
class: diagnostic lists/counters
source of truth: no
business source: no
write trigger: explicit debug event only
reader: debug/audit inspection only
persistent-state audit: no, because these are test-package runtime probes
```

The production-relevant surfaces exercised by #160 are:

```txt
cbp_performance_relevant_markets
cbp_countries_present_in_market
cbp_detailed_accounting_promoted_markets
```

Cache interpretation:

```txt
cbp_performance_relevant_markets:
  class: Performance Mode relevance work list
  source of truth: no stock truth
  owner: relevance preparation
  future reader: candidate global market-local pass
  business meaning: market-level Performance Mode detailed boundary

cbp_countries_present_in_market:
  class: rebuilt current-market work cache
  source of truth: no
  owner: current market-local helper
  future owner candidate: global market-local pass

cbp_detailed_accounting_promoted_markets:
  class: promotion/readiness work list
  source of truth: no stock truth
  owner: promotion gate
  reader: stock mutation / market runtime gate checks
```

Spec boundary recorded by #160:

```txt
Performance Mode detailed processing is scoped by human-relevant markets.
It is not a human-country-only cache filter.
AI-controlled countries present inside a relevant market remain part of the market-country work-cache surface.
```

No durable `market -> countries_present_in_market` cache is introduced. No stock-source map is changed.
# Q2 — Q8 cache system and ownership

## Purpose

Q8 optimises the post-PR126 runtime by narrowing repeated work. That requires a clear distinction between source state, derived caches, work caches, debug/profile metrics, and normal-runtime reusable scalar facts.

This document is the Q8-owned cache standard. Stacked Q8 PRs must update it when they introduce or materially change cache ownership, rebuild triggers, reset policy, or source-vs-cache classification.

## Current cache classes relevant to Q8

| Family / state | Owner | Class | Source of truth? | Q8 rule |
|---|---|---|---:|---|
| `modeu5_<good>_stock_by_market` | country | authoritative stock map | Yes | Never write outside central stock operators / generated adapter surface. |
| `modeu5_<good>_market_stock` | global | derived market-good aggregate | No | Rebuild/validate from country stock; never treat as country source. |
| `modeu5_stock_cap_by_market` | country | country-market capacity record | Yes for stock admission cap | Refresh before stock admission; market-specific contribution must stay current. |
| `modeu5_base_capacity_by_market` / breakdown maps | country | explanation/debug breakdown | No | Keep with capacity refresh; do not drive business independently. |
| `modeu5_countries_present_in_market` | global | rebuilt work cache | No | Rebuild for current promoted/target market; not durable per-market storage. |
| `modeu5_market_country_cache_dirty_markets` | global | dirty scheduling list | No | Scheduling only; Q8.5 repairs affected work-cache consumers but does not create durable per-market storage. |
| `modeu5_promoted_markets_this_cycle` | global | current-cycle work list | No | Current-cycle scheduling only; separate from detailed promotion readiness. |
| `modeu5_detailed_accounting_promoted_markets` | global | readiness / promotion work cache | No stock truth | Must not bypass business readiness checks. |
| `modeu5_pr71_*` counters | global | debug/profile metrics | No | Metrics only; normal runtime should not pay per-good metric writes unless enabled. |

## Cache design questions for stacked Q8 PRs

Every new Q8 cache or scalar work state must answer:

```txt
1. Who owns it? country, global, current promoted market helper, generated adapter, debug/probe.
2. What class is it? source, derived cache, work cache, monthly ledger, debug/profile metric, scalar reusable fact.
3. What triggers a rebuild or write?
4. What invalidates it?
5. What reads it?
6. Can it influence business logic, or is it scheduling/diagnostic only?
7. Does tools/audit_modeu5_persistent_state.sh need to classify it?
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
modeu5_pr71_us00_goods_considered
modeu5_pr71_us00_goods_processed
modeu5_pr71_us00_goods_produced_gate_hits
modeu5_pr71_us00_goods_previous_state_hits
modeu5_pr71_us10_goods_considered
modeu5_pr71_us10_pending_request_hits
modeu5_pr71_us10_requests_processed
```

Ownership and lifecycle:

```txt
owner: global debug/profile metric surface
trigger: modeu5_pr71_metrics_enabled_trigger
enabled in: debug capture or audit runtime
normal runtime: no per-good metric writes
business source: no
```

The business guards remain active even when metrics are disabled.

## Q8.3 update — country capacity-pool scalar cache

Q8.3 introduces reusable country-scope scalar cache facts:

```txt
modeu5_capacity_pool_monthly_stamp
modeu5_capacity_pool_cached_location_rank_capacity
modeu5_capacity_pool_cached_location_count
modeu5_capacity_pool_cached_market_count
modeu5_capacity_pool_cached_base
modeu5_capacity_pool_cached_total
modeu5_capacity_pool_cached_location_rank_per_market
```

Classification:

```txt
class: scalar derived/work cache
owner: country scope
source of truth: no
business source: no
rebuild trigger: first public country capacity-pool calculation in a given month, or after invalidation
invalidation: modeu5_rebuild_country_location_capacity_pool -> modeu5_clear_country_storage_capacity_pool_cache
reader: modeu5_apply_country_storage_capacity_pool_to_current_market
```

Important distinction:

```txt
The cached scalar pool facts do not replace country-market capacity maps.
modeu5_stock_cap_by_market and capacity breakdown maps remain the country-market capacity records read by stock admission and UI/debug.
```

## Q8.5 probe update — dirty cache lifecycle

PR #150 adds a test-package dirty-cache lifecycle probe:

```txt
modeu5_q8_probe_dirty_cache_lifecycle
```

The probe marks the capital market dirty, runs the existing dirty repair consumer, and checks that the repair count is greater than zero.

It confirms the current writer/consumer surface can be exercised:

```txt
modeu5_mark_market_country_cache_dirty
modeu5_repair_dirty_market_country_caches
modeu5_market_country_cache_dirty_markets
```

It does not add a new dirty cache model and does not mutate stock.

## Q8.2 / Q8.5 implementation update

Q8.2 is deferred.

Rejected runtime cache shape:

```txt
modeu5_pr71_us10_country_market_has_pending_request
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
modeu5_repair_dirty_market_country_caches_if_needed
```

Boundary:

```txt
modeu5_countries_present_in_market remains a rebuilt current-market work cache.
modeu5_market_country_cache_dirty_markets remains scheduling state only.
Q8.5 does not confirm durable per-market country-list storage.
```

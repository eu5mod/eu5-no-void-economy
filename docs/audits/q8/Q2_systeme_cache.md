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
| `modeu5_market_country_cache_dirty_markets` | global | dirty scheduling list | No | Scheduling only; Q8.5 should probe producers/consumers before expanding. |
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

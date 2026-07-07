# Q5 — Q8 global logical flow

## Purpose

Q8 refactoring must preserve the post-PR126 business order while reducing duplicated work. This document is the Q8-owned flow standard.

The inherited PR126 Q5 and Q5.1 documents remain source context. They must not be rewritten by Q8 implementation PRs. Q8 owns this document for flow changes made by the optimisation/refactoring stack.

## Current Q8.7 live flow

Q8.7 moves the live market-local owner from the market-center workaround to a once-per-month global market pass.

```txt
monthly_country_pulse
  -> modeu5_run_monthly_stock_cycle_q8_7_owner_switch
     -> readiness / runtime-mode gates
     -> performance and relevance preparation
     -> current-country capacity refresh
     -> monthly seen-market registry
     -> human-relevant full-ledger preparation
     -> Q8.7 global market-local cycle, once per month
          -> every_market_in_world
          -> market runtime accounting mode
          -> detailed markets:
               -> market country cache
               -> country-market capacity refresh
               -> US-00 active-good dispatch
               -> US-10 pending-request dispatch
          -> fallback / blocked markets:
               -> diagnostics only, no ModeU5 stock mutation
     -> country trade-owner cycle
     -> optional audit reconciliation
```

The old market-center owner remains available as a fallback only:

```txt
modeu5_q8_7_live_global_market_owner_disabled
```

When this variable is present, the wrapper falls back to:

```txt
modeu5_run_monthly_promoted_market_local_cycle
  -> every_market_center_in_country
```

## Q8 ordering invariants

```txt
1. Capacity must be prepared before stock admission.
2. US-00 admission facts must be frozen before US-10 consumes same-market stock.
3. US-10 same-market consumption remains non-trade local work.
4. Inter-market vanilla trade remains country-owned and owner-gated.
5. Validation/reconciliation must not compensate for duplicated orchestration.
6. Probes/verifiers must not mutate stock.
7. Q8.7 global market-local ownership may replace the market-center workaround only with a once-per-month guard.
8. Performance Mode relevance is market-level; it must not exclude AI countries that are present inside a human-relevant market.
```

## Flow ownership table

| Phase | Owner | Current surface | Q8 rule |
|---|---|---|---|
| Runtime readiness | country pulse | `modeu5_run_monthly_stock_cycle_q8_7_owner_switch` / `modeu5_run_monthly_stock_cycle` | fail closed when runtime not ready. |
| Country prep | country | capacity/relevance/monthly registries | may prepare caches, not repeat market-local mutation for each country. |
| Runtime mode / accounting gate | central configuration surface | `modeu5_prepare_market_runtime_accounting_mode`, `modeu5_promote_market_to_detailed_accounting` | centralise Normal/Performance/Deactivated policy and promotion readiness. |
| Promoted-market local | Q8.7 global market owner | `modeu5_run_monthly_q8_7_global_market_local_cycle_once` -> `every_market_in_world` | process each market-local mutation surface once per month. |
| Fallback local owner | market-center country | `modeu5_run_monthly_promoted_market_local_cycle` -> `every_market_center_in_country` | rollback/comparison only; same business branch internals. |
| US-00 | present country inside detailed market | PR7.1 active-good dispatch | run before US-10 for all present-country admission facts. |
| US-10 local | present country inside detailed market | PR7.1 pending-request dispatch | same-market consumption only; keep after US-00. Q8.2 sparse pending index remains deferred. |
| Q8.6 verifier | debug/audit verifier surface | `modeu5_run_market_sliced_verifier_candidates` | bounded candidate-market verification only; no stock mutation or repair. |
| Trade | country | country-owned trade pass | inter-market only; owner-gated; no direct stock writes. |
| Validation | audit/debug/reconciliation surface | optional monthly/audit helpers | bounded, diagnostic, or repair after divergence. |

## Mermaid flow — current Q8.7 owner

```mermaid
flowchart TB
    %% Q8-owned Q5 flow after the live Q8.7 owner switch.
    %% Loop nesting is semantic: it defines who owns mutation.

    subgraph COUNTRY["Loop: monthly_country_pulse / current country"]
        direction TB
        A["monthly_country_pulse"] --> B["modeu5_run_monthly_stock_cycle_q8_7_owner_switch"]
        B --> SW{"fallback variable present?<br/>modeu5_q8_7_live_global_market_owner_disabled"}
        SW -->|yes| OLD["fallback owner:<br/>modeu5_run_monthly_promoted_market_local_cycle"]
        SW -->|no| C["modeu5_run_monthly_stock_cycle"]

        C --> READY{"runtime ready?"}
        READY -->|no| CLOSED["fail closed / diagnostics only"]
        READY -->|yes| P0["prepare performance human-relevant markets"]
        P0 --> P1["refresh current-country capacities"]
        P1 --> P2["prepare monthly market-seen registry"]
        P2 --> P3["prepare human-relevant full-ledger markets"]
        P3 --> G0["modeu5_run_monthly_q8_7_global_market_local_cycle_once"]

        subgraph COUNTRY_PREP["Country-owned preparation"]
            direction TB
            P1 --> CP0["every_market_present_in_country"]
            CP0 --> CP1["recalculate country-market capacity"]
            CP1 --> CP2["store capacity/cache records"]
        end

        G0 --> STAMP{"global market-local pass<br/>already run this month?"}
        STAMP -->|yes| SKIP["record Q8.7 skip counter"]
        STAMP -->|no| WORLD["every_market_in_world"]

        subgraph GLOBAL_OWNER["Market-local owner: one global market pass per month"]
            direction TB
            WORLD --> M0["save market scope"]
            M0 --> M1["modeu5_prepare_market_runtime_accounting_mode"]
            M1 --> M2{"market runtime mode"}
            M2 -->|detailed| LOCAL["modeu5_run_promoted_market_live_local_branch_market_all_goods"]
            M2 -->|vanilla fallback| MF["record fallback<br/>no ModeU5 stock mutation"]
            M2 -->|blocked| MB["record blocked"]
        end

        subgraph LOCAL_DETAIL["Detailed market-local branch"]
            direction TB
            LOCAL --> L0["rebuild countries_present_in_market once"]
            L0 --> L1["for each present country:<br/>refresh country-market capacity"]
            L1 --> L2["for each present country:<br/>US-00 active-good dispatcher"]
            L2 --> L3{"active good / previous state?"}
            L3 -->|yes| L4["heavy US-00 generated helper"]
            L3 -. no .-> L5["skip heavy US-00 helper"]
            L4 --> L6["US-00 facts frozen"]
            L5 --> L6
            L6 --> L7["for each present country:<br/>US-10 pending-good dispatcher"]
            L7 --> L8{"pending same-market request?"}
            L8 -->|yes| L9["heavy US-10 generated helper"]
            L8 -. no .-> L10["skip heavy US-10 helper"]
            L9 --> L11["same-market consumption processed"]
            L10 --> L11
            L11 --> L12["record local market processed"]
        end

        OLD --> TRADE0
        SKIP --> TRADE0
        L12 --> TRADE0["modeu5_run_monthly_country_trade_owner_cycle"]
        MF --> TRADE0
        MB --> TRADE0

        subgraph TRADE["Country-owned trade branch"]
            direction TB
            TRADE0 --> T1["every_trade from country scope"]
            T1 --> T2["inter-market trade only<br/>from_market != to_market"]
            T2 --> T3["delegate effects to stock handlers"]
        end

        T3 --> AUDIT{"audit enabled?"}
        AUDIT -->|yes| R1["monthly reconciliation / validation"]
        AUDIT -->|no| END["end country monthly cycle"]
        R1 --> END
    end
```

## Promotion / migration repair boundary

Promotion happens inside the market runtime accounting mode. Promotion is allowed only if the detailed country ledger can be made consistent with the market aggregate.

The current exception rule is expressed as **different**, not only as `country_sum > market_aggregate`:

```txt
if country_sum == market_aggregate:
  promote normally

if country_sum > 0 and country_sum != market_aggregate:
  market aggregate is source/cap
  rebuild country stocks from the aggregate
  validate
  promote only if repaired country_sum == market_aggregate

if country_sum == 0 and market_aggregate > 0:
  materialize country stocks from the aggregate
  validate
  promote only if materialized country_sum == market_aggregate
```

```mermaid
flowchart TB
    A["Promotion requested"] --> B["scan country ledger"]
    B --> C["read market aggregate"]
    C --> D{"country_sum == market_aggregate?"}
    D -->|yes| P["mark market promoted"]
    D -->|no, country_sum > 0| R["repair country ledger from aggregate"]
    D -->|no, country_sum = 0<br/>aggregate > 0| M["materialize country ledger from aggregate"]
    D -->|no usable source| Z["blocked / zero-source diagnostic"]
    R --> V["rescan + validate"]
    M --> V
    V --> OK{"clean after repair?"}
    OK -->|yes| P
    OK -->|no| F["promotion failure / blocked diagnostic"]
```

The aggregate is the cap/source for this promotion exception. The repair path must not inflate the aggregate from stale country stocks.

## Q8.0 baseline decision

Q8.0 adds no runtime flow change. It creates this Q8-owned flow contract for future stacked PRs.

## Q8.1 update — no flow-order change

Q8.1 gates PR7.1 metrics only.

```txt
US-00 active-good guard still runs.
US-10 pending-request guard still runs.
Heavy helper calls remain controlled by the existing business gates.
Only the temporary PR7.1 metric writes are gated.
```

Therefore Q8.1 does not change the Q5 phase order.

## Q8.3 update — refined capacity preparation internals

Q8.3 preserves the Q5 ordering:

```txt
country capacity preparation / promoted-market country-market capacity refresh
before
US-00 admission
before
US-10 same-market consumption
before
country-owned trade / validation / reconciliation
```

The refined capacity step is:

```txt
modeu5_calculate_country_storage_capacity_pool
  -> if country/month stamp missing or stale:
       modeu5_calculate_country_storage_capacity_pool_raw
       modeu5_store_country_storage_capacity_pool_cache
  -> else:
       modeu5_load_country_storage_capacity_pool_cache

modeu5_apply_country_storage_capacity_pool_to_current_market
  -> still reads current market merchant capacity
  -> still writes country-market capacity maps
```

The promoted-market dispatcher semantics are unchanged: it still gets a refreshed country-market capacity record before US-00, but the country-wide pool facts may be reused for that country during the same month.

## Q8.2 / Q8.5 implementation update

Q8.2 is deferred.

Rejected live flow shape:

```txt
promoted-market local cycle
  -> market country cache
  -> country-market capacity refresh
  -> US-00 active-good dispatch for all present countries
  -> US-10 pending-request dispatch
       -> aggregate all-goods country-market pending pre-scan
       -> if pending exists: existing per-good US-10 pending dispatcher
       -> if no pending exists: skip generated per-good US-10 dispatcher
```

Reason:

```txt
If most country-market pairs have at least one pending request, the aggregate pre-scan adds work before the existing per-good dispatcher.
Q8.2 should instead become a later sparse pending-index design written when requests are created.
```

Q8.5 preserves the same flow position for market-country work-cache rebuilds:

```txt
confirmed topology/lifecycle producer
  -> modeu5_mark_market_country_cache_dirty
  -> modeu5_market_country_cache_dirty_markets scheduling list
  -> modeu5_repair_dirty_market_country_caches_if_needed
  -> modeu5_rebuild_countries_present_in_market for dirty markets only
```

The dirty repair path is scheduling/repair flow only. It does not authorize a durable `market -> countries_present_in_market` cache and does not change stock mutation order.

## Q8.6 implementation update

Q8.6 adds a debug/audit-only verifier flow:

```txt
modeu5_run_market_sliced_verifier_candidates
  -> modeu5_prepare_market_sliced_verifier_candidates
     -> copy dirty markets from modeu5_market_country_cache_dirty_markets
     -> copy promoted markets from modeu5_promoted_markets_this_cycle
  -> for each candidate market only:
       modeu5_rebuild_countries_present_in_market
       record pass/fail counters
```

Boundary:

```txt
- no stock mutation;
- no stock repair;
- dirty market scheduling list is not cleared;
- no live dispatcher is replaced.
```

## Q8.7 live implementation update

Q8.7 is no longer proof-only in this PR. The live market-local owner is now:

```txt
modeu5_run_monthly_q8_7_global_market_local_cycle_once
  -> monthly stamp guard
  -> every_market_in_world
  -> modeu5_prepare_market_runtime_accounting_mode
  -> detailed markets run the existing market-local branch
  -> fallback/blocked markets record diagnostics only
```

The old market-center owner remains available only via the fallback variable. This is a rollback/comparison surface, not the default Q8 flow.

#160's Performance Mode boundary still applies:

```txt
human-relevant market
not human-country-only
```

Consequence for Q5:

```txt
Live market-local ownership has changed.
Trade position is unchanged.
US-00 before US-10 ordering is unchanged.
Validation/reconciliation position is unchanged.
Performance Mode detailed processing is market-level once the market is relevant.
AI countries inside a human-relevant market remain part of the market-local surface.
```

## Delta summary

| Area | Before Q8.7 live switch | HEAD after Q8.7 |
|---|---|---|
| Market-local owner | `every_market_center_in_country` workaround. | `every_market_in_world` once per month behind `modeu5_run_monthly_q8_7_global_market_local_cycle_once`. |
| Fallback owner | N/A for Q8.7. | Old market-center owner retained behind `modeu5_q8_7_live_global_market_owner_disabled`. |
| US-10 no-request country-market | Enters generated per-good US-10 wrapper surface; Q8.2 aggregate pre-gate deferred. | Unchanged. |
| US-10 positive request country-market | Per-good wrappers check pending maps and call heavy helper only for requested goods. | Unchanged. |
| US-00 ordering | Runs before any US-10 pass. | Unchanged. |
| Dirty market-country cache | Guarded `modeu5_repair_dirty_market_country_caches_if_needed` exists. | Unchanged; Q8.6 copies dirty candidates but does not clear the dirty list. |
| Market-sliced verifier | Debug/audit runtime verifier slice exists, bounded to dirty/promoted candidate markets. | Unchanged. |
| Performance Mode relevant-market boundary | Human-relevant market is the boundary; AI-controlled countries inside such markets remain in market-local scope. | Unchanged and now consumed by the live global market-local owner. |
| Promotion mismatch repair | Conservative promotion failure when country sum exceeds market aggregate. | Market aggregate is source/cap; non-zero differing country ledger is rebuilt to the aggregate, logged as blocked/migration repair, then promotion proceeds only after validation. |
| Durable per-market country-list cache | Not confirmed. | Still not confirmed; no durable `market -> countries_present_in_market` cache is introduced. |

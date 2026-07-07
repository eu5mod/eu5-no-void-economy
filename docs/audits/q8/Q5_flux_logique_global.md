# Q5 — Q8 global logical flow

## Purpose

Q8 refactoring must preserve the post-PR126 business order while reducing duplicated work. This document is the Q8-owned flow standard.

The inherited PR126 Q5 and Q5.1 documents remain source context, especially for the current guarded-dispatch diagram. Q8 owns this document for changes made by the new optimisation/refactoring stack.

## Current post-PR126 flow baseline

```txt
monthly_country_pulse
  -> modeu5_run_monthly_stock_cycle
     -> readiness / runtime-mode gates
     -> performance and relevance preparation
     -> current-country capacity refresh
     -> monthly seen-market registry
     -> human-relevant full-ledger preparation
     -> promoted-market local cycle
          -> market country cache
          -> country-market capacity refresh
          -> US-00 active-good dispatch
          -> US-10 pending-request dispatch
     -> country trade-owner cycle
     -> optional audit reconciliation
```

## Q8 ordering invariants

```txt
1. Capacity must be prepared before stock admission.
2. US-00 admission facts must be frozen before US-10 consumes same-market stock.
3. US-10 same-market consumption remains non-trade local work.
4. Inter-market vanilla trade remains country-owned and owner-gated.
5. Validation/reconciliation must not compensate for duplicated orchestration.
6. Probes/verifiers must not mutate stock.
7. A future global market-local pass must prove equivalence before replacing the market-center owner workaround.
8. Performance Mode relevance is market-level; it must not exclude AI countries that are present inside a human-relevant market.
```

## Flow ownership table

| Phase | Owner | Current surface | Q8 rule |
|---|---|---|---|
| Runtime readiness | country pulse | `modeu5_run_monthly_stock_cycle` | fail closed when runtime not ready. |
| Country prep | country | capacity/relevance/monthly registries | may prepare caches, not repeat market-local mutation for each country. |
| Runtime mode / accounting gate | central configuration trigger surface | `modeu5_configuration_triggers.txt`, `modeu5_configuration_effects.txt` | centralise Performance/Normal/Deactivated policy; #160 clarifies human-relevant market semantics. |
| Promoted-market local | market-local logical owner, market-center workaround in current implementation | `modeu5_run_monthly_promoted_market_local_cycle` | process each promoted market once according to the chosen owner rule. |
| US-00 | present country inside promoted market | PR7.1 active-good dispatch | run before US-10 for all present-country admission facts. |
| US-10 local | present country inside promoted market | PR7.1 pending-request dispatch | same-market consumption only; keep after US-00. Q8.2 aggregate pre-gate is deferred. |
| Q8.6 verifier | debug/audit verifier surface | `modeu5_run_market_sliced_verifier_candidates` | bounded candidate-market verification only; no stock mutation or repair. |
| Q8.7 proof stack | test-package proof surface | `event modeu5_q8_probe_debug.7`, `.9`, `.11`, and related Q8.7 probes | prove future global market-local ownership before live replacement; no stock mutation. |
| Trade | country | country-owned trade pass | inter-market only; owner-gated; no direct stock writes. |
| Validation | audit/debug/reconciliation surface | optional monthly/audit helpers | bounded, diagnostic, or repair after divergence. |

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

## Q8.2 / Q8.4 / Q8.5 / Q8.6 / Q8.7 probe update

PR #150 contains all five remaining probes in one test-package PR and does not change the Q5 flow.

```txt
modeu5_q8_probe_us10_pending_gate
modeu5_q8_probe_helper_inventory
modeu5_q8_probe_dirty_cache_lifecycle
modeu5_q8_probe_market_sliced_verifier_candidate
modeu5_q8_probe_global_market_iterator_exposure
```

Runtime validation attached on 2026-07-06 confirms the probe layer passed through `event modeu5_q8_probe_debug.1`.

Q5 phase order remains unchanged. No gameplay flow change is authorised by #150 until a later implementation PR proves equivalence and updates this document again.

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

## Q8.7 proof-stack update

Q8.7 now proves progressively more of the future global market-local pass while keeping the live Q5 dispatcher flow unchanged.

Current live flow remains:

```txt
country preparation / relevance discovery
  -> promoted-market local cycle through every_market_center_in_country workaround
  -> country trade-owner pass
  -> validation / reconciliation
```

Future target flow remains:

```txt
country preparation / relevance discovery
  -> global market-local pass
  -> country trade-owner pass
  -> validation / reconciliation
```

The proof stack currently covers:

```txt
#155:
  every_market_in_world can enter market-local scope and rebuild countries_present_in_market.

#159:
  every_market_in_world sees the same Normal Mode market universe as the market-center workaround.

#160 / relevant-market proof:
  every_market_in_world filtered to modeu5_performance_relevant_markets sees the same Performance Mode relevant-market set and can rebuild countries_present_in_market for those markets.

#160 / workshape proof:
  current market-center owner shape and candidate global market-local owner shape rebuild the same relevant-market work-cache surface and count the same present-country surface.

#160 / no-op dispatcher proof:
  current market-center owner shape and candidate global market-local owner shape produce matching pass counters without capacity mutation, US-00, US-10, trade-owner work, validation, or stock mutation.
```

#160 clarifies the Performance Mode boundary:

```txt
Performance Mode relevance discovery remains a preparation step.
The future global market-local pass consumes the relevant-market set.
Once inside a relevant market, the pass may process all countries present in that market.
AI countries inside a human-relevant market are part of the market-local surface.
```

Spec reading:

```txt
human-relevant market
not human-country-only
```

Consequence for Q5:

```txt
Current monthly dispatcher flow is unchanged.
Trade position is unchanged.
US-00 before US-10 ordering is unchanged.
Validation/reconciliation position is unchanged.
Live market-local ownership is unchanged.
The central Performance Mode trigger semantics are corrected so the runtime gate can represent the human-relevant-market boundary.
```

The #160 production trigger correction does not move any phase. It only clarifies whether a Performance Mode accounting decision should use detailed processing or fallback when the market has already been classified as human-relevant.

A later Q8.7/F7 implementation PR is still required before moving US-00 or US-10 live work onto the global market-local owner.

## Delta summary

| Area | Before Q8.6 | HEAD after Q8.6 / Q8.7 proofs |
|---|---|---|
| US-10 no-request country-market | Enters generated per-good US-10 wrapper surface; Q8.2 aggregate pre-gate deferred. | Unchanged. |
| US-10 positive request country-market | Per-good wrappers check pending maps and call heavy helper only for requested goods. | Unchanged. |
| US-00 ordering | Runs before any US-10 pass. | Unchanged. |
| Dirty market-country cache | Guarded `modeu5_repair_dirty_market_country_caches_if_needed` exists. | Unchanged; Q8.6 copies dirty candidates but does not clear the dirty list. |
| Market-sliced verifier | Probe-only candidate list in test package. | Debug/audit runtime verifier slice exists, bounded to dirty/promoted candidate markets. |
| Q8.7 global market-local pass | Not implemented. | Proof-only comparisons exist for Normal Mode market universe, Performance Mode relevant-market subset, workshape, and no-op dispatcher counters. No live switch. |
| Performance Mode relevant-market boundary | Not separately documented in Q5. | Human-relevant market is the boundary; AI-controlled countries inside such markets remain in market-local scope. |
| Production trigger semantics | Human-relevant market boundary could be read as human-country-only in trigger decisions. | #160 corrects the central configuration trigger semantics without moving the dispatcher flow. |
| Stock mutation / repair | No verifier stock mutation. | Still none; Q8.6 and Q8.7 record counters only. |
| Durable per-market country-list cache | Not confirmed. | Still not confirmed; no durable `market -> countries_present_in_market` cache is introduced. |
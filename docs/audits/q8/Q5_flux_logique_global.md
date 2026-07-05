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
```

## Q5.1 / future Q5.2 placement

Q5.1 is a flow checkpoint and belongs with Q5 context, not inside Q8 future-optimisation findings.

If Q5.2 is added later, it should be a Q5 flow checkpoint or subsection before Q8 implementation notes. It should clarify current flow, not become a separate optimisation track.

## Flow ownership table

| Phase | Owner | Current surface | Q8 rule |
|---|---|---|---|
| Runtime readiness | country pulse | `modeu5_run_monthly_stock_cycle` | fail closed when runtime not ready. |
| Country prep | country | capacity/relevance/monthly registries | may prepare caches, not repeat market-local mutation for each country. |
| Promoted-market local | market-local logical owner, market-center workaround in current implementation | `modeu5_run_monthly_promoted_market_local_cycle` | process each promoted market once according to the chosen owner rule. |
| US-00 | present country inside promoted market | PR7.1 active-good dispatch | run before US-10 for all present-country admission facts. |
| US-10 local | present country inside promoted market | PR7.1 pending-request dispatch | same-market consumption only; keep after US-00. |
| Trade | country | country-owned trade pass | inter-market only; owner-gated; no direct stock writes. |
| Validation | audit/debug/reconciliation surface | optional monthly/audit helpers | bounded, diagnostic, or repair after divergence. |

## Q8.0 baseline decision

Q8.0 adds no runtime flow change. It creates this Q8-owned flow contract for future stacked PRs.

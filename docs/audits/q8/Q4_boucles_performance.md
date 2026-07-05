# Q4 — Q8 loops and performance model

## Purpose

Q8 is a performance-oriented refactoring track. Its purpose is to reduce repeated monthly work after PR126 while preserving PR126's business contracts and ordering.

This document is the Q8-owned performance standard. Stacked Q8 PRs must update it when they materially change loop shape, metric writes, counters, dispatcher ownership, or cost assumptions.

## Post-PR126 baseline shape

```txt
monthly_country_pulse
  -> performance / human-relevant preparation
  -> current-country capacity refresh
  -> monthly market-seen registry
  -> human-relevant full-ledger preparation
  -> promoted-market local cycle through current market-center ownership workaround
  -> country trade-owner cycle
  -> optional audit reconciliation
```

## Q8 performance notation

| Symbol | Meaning |
|---|---|
| `C` | countries touched by monthly country pulse |
| `M_c` | markets present in a country |
| `P` | promoted / relevant markets processed by local branch |
| `K_m` | countries present in a promoted market |
| `G_supported` | generated supported goods |
| `G_a` | active / produced / pending goods after Q8 guards |
| `T_country` | trade candidates owned by a country |

## Target work shape

```txt
country preparation:              O(C * M_c)
promoted-market local work:        O(P * K_m * G_a)
country-owned trade pass:          O(C * T_country)
validation/debug/probes:           bounded, opt-in, or dirty/candidate scoped
```

## Current Q8 classification

| Track | Performance intent | Q8.0 classification |
|---|---|---|
| Q8.1 / F3 | remove normal-runtime per-good debug/profile counter writes | IMPLEMENT_NOW |
| Q8.2 / F2 | avoid generated US-10 per-good checks for no-request country-market pairs if still present | PROBE_FIRST |
| Q8.3 / F1 | avoid repeated country-wide capacity-pool calculation inside promoted-market capacity refresh | IMPLEMENT_NOW |
| Q8.4 / F4 | reduce duplicate guard layers after caller inventory | PROBE_FIRST |
| Q8.5 / F5/F9a | move derived cache repair toward dirty/candidate consumers | PROBE_FIRST |
| Q8.6 / F9c | verify candidate/dirty market slices before verifier promotion | PROBE_FIRST |
| Q8.7 / F7 | replace market-center ownership workaround only if global market pass is proven safe | PROBE_FIRST |

## Performance guardrails

```txt
1. A performance change must identify whether it reduces loop count, metric writes, repeated recalculation, or only documentation risk.
2. Work-shape counters are not wall-clock profiling.
3. Debug/profile counters must not become normal-runtime overhead unless they are necessary for business correctness.
4. Broad world scans are rejected unless they replace more work than they add and are debug/probe scoped first.
5. Performance Mode should stay candidate/promoted/relevant-market scoped.
```

## Q8.0 baseline decision

Q8.0 freezes this post-PR126 performance model but does not alter runtime behaviour.

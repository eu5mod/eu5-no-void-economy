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
| Q8.2 / F2 | avoid generated US-10 per-good checks for no-request country-market pairs if still present | IMPLEMENT_NOW after PR150 probe |
| Q8.3 / F1 | avoid repeated country-wide capacity-pool calculation inside promoted-market capacity refresh | IMPLEMENT_NOW |
| Q8.4 / F4 | reduce duplicate guard layers after caller inventory | PROBE_FIRST |
| Q8.5 / F5/F9a | move derived cache repair toward dirty/candidate consumers | IMPLEMENT_NOW after PR150 probe |
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

## Q8.1 update — metric-write reduction

Q8.1 changes metric-write cost, not the business loop count.

```txt
Normal runtime:
  PR7.1 per-good business guards still run.
  PR7.1 per-good metric writes are skipped unless debug/audit enables them.

Debug/audit runtime:
  PR7.1 counters remain available for validation/profile scenarios.
```

Interpretation:

```txt
Q8.1 reduces hot-path write overhead and debug-state churn in normal runtime.
It does not yet reduce G_supported guard traversal.
Q8.2 remains responsible for probing whether an aggregate US-10 country-market gate is needed.
```

## Q8.3 update — capacity-pool recalculation reduction

Q8.3 changes the capacity-pool recalculation shape:

```txt
Before:
  country-market capacity refresh could recalculate country-wide pool facts again for the same country/month.

After:
  first public pool calculation for country/month computes and caches country-wide pool facts;
  later country-market refreshes reuse the stamped pool facts;
  each market still recalculates merchant/trade-capacity contribution.
```

The high-level work model remains:

```txt
O(C * M_c preparation) + O(P * K_m * G_a) + O(C * T_country)
```

But the constant factor inside capacity preparation and promoted-market country-market capacity refresh is reduced for countries seen repeatedly in the same month.

## Q8.2 / Q8.4 / Q8.5 / Q8.6 / Q8.7 probe update

PR #150 contains all five remaining probes in one PR. They are test-package probes only and do not change the runtime work model yet.

```txt
Q8.2 — pending-request probe before an aggregate country-market gate.
Q8.4 — helper inventory bridge before any body-helper split.
Q8.5 — dirty repair lifecycle probe before cache expansion.
Q8.6 — candidate market slice probe before verifier promotion.
Q8.7 — isolated global market iterator exposure probe before dispatcher replacement.
```

Runtime validation attached to #150 on 2026-07-06 shows all five probes passed through:

```txt
event modeu5_q8_probe_debug.1
```

The full revalidation suite is not required for this performance-probe PR:

```txt
event modeu5_revalidate_debug.1   # not required for #150
```

The probe layer itself is passed; implementation still requires separate PRs and clean-log hardening where relevant.

## Q8.2 / Q8.5 implementation update

Q8.2 changes the normal US-10 work shape for no-request country-market pairs:

```txt
Before:
  for each country present in promoted market:
    count US-10 country pass
    generated US-10 dispatcher enters every per-good wrapper
    each per-good wrapper checks its own pending-request map

After:
  for each country present in promoted market:
    generated aggregate pending-request gate checks whether any supported good has a positive pending request
    if no pending request exists:
      skip the generated per-good US-10 dispatcher
    if at least one pending request exists:
      run the existing per-good pending dispatcher unchanged
```

This reduces generated per-good wrapper dispatch for the common no-request country-market case. It does not remove the per-good literal map surface and does not split Q8.4 body helpers.

Q8.5 changes dirty-cache repair from probe-only evidence to a guarded repair consumer:

```txt
modeu5_repair_dirty_market_country_caches_if_needed
```

The dirty repair path remains candidate-scoped:

```txt
producers: confirmed lifecycle hooks that call modeu5_mark_market_country_cache_dirty
consumer: modeu5_repair_dirty_market_country_caches / if_needed wrapper
scope: dirty markets only
```

It does not introduce durable per-market country-list storage and therefore does not change the Q4 assumption that `modeu5_countries_present_in_market` is a rebuilt current-market work cache.

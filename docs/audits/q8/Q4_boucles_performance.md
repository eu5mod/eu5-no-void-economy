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
| `M_world` | all markets exposed by `every_market_in_world` |
| `M_rel` | Performance Mode human-relevant markets |
| `P` | promoted / relevant markets processed by local branch |
| `K_m` | countries present in a promoted market |
| `G_supported` | generated supported goods |
| `G_a` | active / produced / pending goods after Q8 guards |
| `T_country` | trade candidates owned by a country |
| `V_m` | candidate markets selected by the Q8.6 verifier slice |

## Target work shape

```txt
country preparation:              O(C * M_c)
promoted-market local work:        O(P * K_m * G_a)
country-owned trade pass:          O(C * T_country)
validation/debug/probes:           bounded, opt-in, or dirty/candidate scoped
Q8.6 verifier slice:               O(V_m * locations_in_candidate_market), debug/audit only
Q8.7 candidate market owner:        proof-only now; future target O(M_rel * K_m * G_a) in Performance Mode
```

## Current Q8 classification

| Track | Performance intent | Current status |
|---|---|---|
| Q8.1 / F3 | remove normal-runtime per-good debug/profile counter writes | IMPLEMENTED |
| Q8.2 / F2 | avoid generated US-10 per-good checks for no-request country-market pairs if still present | DEFERRED; aggregate pre-scan likely unprofitable when pending demand is common |
| Q8.3 / F1 | avoid repeated country-wide capacity-pool calculation inside promoted-market capacity refresh | IMPLEMENTED |
| Q8.4 / F4 | reduce duplicate guard layers after caller inventory | PROBE_FIRST |
| Q8.5 / F5/F9a | move derived cache repair toward dirty/candidate consumers | IMPLEMENTED |
| Q8.6 / F9c | verify candidate/dirty market slices before verifier promotion | IMPLEMENTED as debug/audit candidate slice; no stock repair |
| Q8.7 / F7 | replace market-center ownership workaround only if global market pass is proven safe | PROBE_STACK; universe, relevant-market, workshape, and no-op dispatcher shadows exist; no live switch |

## Performance guardrails

```txt
1. A performance change must identify whether it reduces loop count, metric writes, repeated recalculation, or only documentation risk.
2. Work-shape counters are not wall-clock profiling.
3. Debug/profile counters must not become normal-runtime overhead unless they are necessary for business correctness.
4. Broad world scans are rejected unless they replace more work than they add and are debug/probe scoped first.
5. Performance Mode should stay candidate/promoted/relevant-market scoped.
6. Human-relevant-market scoping must not collapse the market-local work surface to human countries only.
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
Q8.2 remains responsible for proving a better sparse pending-work design if US-10 dispatch needs further narrowing.
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
event cbp_q8_probe_debug.1
```

The probe layer itself is passed; implementation still requires separate PRs and clean-log hardening where relevant.

## Q8.2 / Q8.5 implementation update

Q8.2 is deferred.

Rejected live shape:

```txt
for each country present in promoted market:
  generated aggregate pending-request gate scans supported goods
  if any pending request exists:
    run the existing per-good pending dispatcher
```

Reason:

```txt
If most country-market pairs have at least one pending request, the aggregate gate adds a full pre-scan before the existing per-good dispatch.
It is only profitable when no-request country-market pairs dominate.
```

Preferred later work shape:

```txt
request write -> sparse pending country-market / country-market-good index
monthly US-10 -> iterate sparse pending work -> clear index after processing
```

Q8.5 changes dirty-cache repair from probe-only evidence to a guarded repair consumer:

```txt
cbp_repair_dirty_market_country_caches_if_needed
```

The dirty repair path remains candidate-scoped:

```txt
producers: confirmed lifecycle hooks that call cbp_mark_market_country_cache_dirty
consumer: cbp_repair_dirty_market_country_caches / if_needed wrapper
scope: dirty markets only
```

It does not introduce durable per-market country-list storage and therefore does not change the Q4 assumption that `cbp_countries_present_in_market` is a rebuilt current-market work cache.

## Q8.6 implementation update

Q8.6 adds a bounded debug/audit verifier slice:

```txt
candidate producers:
  cbp_market_country_cache_dirty_markets
  cbp_promoted_markets_this_cycle

candidate list:
  cbp_market_sliced_verifier_candidate_markets

runner:
  cbp_run_market_sliced_verifier_candidates
```

Work shape:

```txt
build candidate list from dirty/promoted markets
for each candidate market only:
  rebuild current-market countries_present_in_market work cache
  record pass/fail counters
```

This changes validation/debug work shape only. It avoids blind world-location scans and does not run in normal runtime unless debug/audit mode enables the verifier.

## Q8.7 proof-stack update

Q8.7 adds proof-only loop evidence for replacing the current market-center ownership workaround later.

Existing live owner shape remains:

```txt
monthly_country_pulse
  -> every_market_center_in_country
     -> promoted-market local branch
```

Q8.7 proof surfaces now cover:

```txt
Exposure / cache-rebuild proof:
  every_market_in_world
    -> current-market country cache rebuild

Normal Mode universe shadow comparison:
  every_market_in_world
    == every_country -> every_market_center_in_country

Performance Mode relevant-market shadow comparison:
  cbp_performance_relevant_markets
    == every_market_in_world filtered to cbp_performance_relevant_markets

Performance Mode market-owner workshape shadow:
  current market-center workaround
    == every_market_in_world filtered to cbp_performance_relevant_markets
    -> rebuild countries_present_in_market
    -> count present-country work surface

Performance Mode no-op dispatcher shadow:
  current market-center workaround pass counters
    == candidate global market-local pass counters
    without capacity mutation, US-00, US-10, trade-owner work, validation, or stock mutation
```

The #160 Performance Mode proof stack adds only lightweight loop shapes:

```txt
every_market_in_world
  -> if market in cbp_performance_relevant_markets
     -> rebuild countries_present_in_market
     -> count countries / pass surfaces only
```

Boundary:

```txt
No US-00 loop is run by the Q8.7 proof stack.
No US-10 loop is run by the Q8.7 proof stack.
No generated-good loop is run by the Q8.7 proof stack.
No stock mutation loop is run by the Q8.7 proof stack.
No validation or repair loop is run by the Q8.7 proof stack.
No every_trade-from-market-scope pattern is introduced.
```

Updated Q4 interpretation:

```txt
Performance Mode should reduce the number of markets processed.
It should not incorrectly reduce the processing surface to human countries only.
The relevant-market set is the boundary; all countries present inside that relevant market remain part of the market-local work surface.
```

Therefore the intended future Performance Mode work shape is:

```txt
M_rel * K_m * G_a
```

not:

```txt
human countries only * their markets * G_a
```

The #160 configuration trigger correction is a production policy-boundary correction, not a dispatcher loop change. It does not by itself replace the market-center workaround or authorise live execution of the candidate global market-local dispatcher.

Q8.7 still does not authorise a live dispatcher switch. The next required step is the actual switch PR with economic equivalence validation before moving US-00 or US-10 live work.
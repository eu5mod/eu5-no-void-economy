# TECH-01 companion — Q8-F9 runtime validation

## Purpose

This companion note records the TECH-01 impact of PR #150 without changing the meaning of the main engine exposure matrix.

It exists because PR #150 provides runtime evidence for Q8-F9 probe surfaces, especially the global market iterator exposure used by Q8.7.

## Validation event

For PR #150, the required runtime event is:

```txt
event modeu5_q8_probe_debug.1
```

The full revalidation event is not required for this PR:

```txt
event modeu5_revalidate_debug.1   # not required for #150
```

A full-revalidation summary reporting zero scenarios therefore does not invalidate Q8-F9 runtime evidence when the Q8 event has been run separately.

## TECH-01 row impact

| TECH-01 row | Exposure | PR #150 impact | Status after PR #150 |
|---:|---|---|---|
| 002 | `every_market_in_world` | Q8.7 isolated test-package probe ran and counted 129 markets. | `CONFIRMED` remains valid; add PR #150 runtime probe as local test basis. |
| 110 | PASS marker handling | Q8 result events read marker presence. | `CONFIRMED`; keep avoiding numeric comparisons against absent result markers. |
| 111 | global variable-list scheduling | Q8.6 candidate-market list and Q8.5 dirty repair use list/counter surfaces. | `CONFIRMED`; list remains scheduling/debug state only. |
| 125 | current-market country work cache | Q8.5 exercises existing dirty repair consumer. | `CONFIRMED`; no durable cache introduced. |
| 126 | durable per-market country-list cache | Q8.5/Q8.6 do not prove durable per-market storage. | `NOT_CONFIRMED`; fallback remains rebuild current-market work cache. |

## Observed Q8 runtime PASS markers

```txt
ModeU5 Q8.2 PROBE us10_pending_gate PASS wheat_pending=0.0000
ModeU5 Q8.4 PROBE helper_inventory PASS runtime_noop_static_inventory_required
ModeU5 Q8.5 PROBE dirty_cache_lifecycle PASS repair_count=3
ModeU5 Q8.6 PROBE market_slice_candidate PASS
ModeU5 Q8.7 PROBE global_market_iterator PASS count=129
ModeU5 Q8 PROBE RESULT all_remaining_candidates PASS
```

## Boundary

The PR #150 result confirms probe surfaces, not gameplay replacement.

```txt
Confirmed: test-package exposure of every_market_in_world.
Not confirmed: replacing the market-center owner workaround in the monthly gameplay dispatcher.
```

A future implementation PR must still prove:

```txt
- equivalent market ownership semantics;
- preserved US-00 before US-10 ordering;
- bounded runtime cost;
- no stock mutation from verifier/probe code;
- no reliance on full revalidation for Q8-only probe acceptance.
```

## Known cleanup

```txt
- Q8.7 emitted PASS count=129 while also producing unset-counter script errors for modeu5_test_q8_7_global_market_count.
- Q8 event localization keys are missing.
```

These are cleanup items for a clean-log validation pass. They do not overturn the observed Q8 PASS markers.

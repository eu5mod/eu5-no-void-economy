# Q8-F9 / TECH-01 — Remaining probe exposure validation

## Purpose

This document records the TECH-01 exposure implications of PR #150.

PR #150 is a single probe PR covering:

```txt
Q8.2 — US-10 pending-request / aggregate-gate probe
Q8.4 — guarded-helper / body-helper inventory bridge
Q8.5 — dirty market-country cache lifecycle probe
Q8.6 — candidate market-slice verifier probe
Q8.7 — global market iterator exposure probe
```

It is not a gameplay implementation PR.

## Static validation

Command:

```sh
bash tools/audit_q8_remaining_candidates.sh
```

Expected status:

```txt
PASS for all five probe entry points.
PENDING for implementation decisions until runtime evidence is attached.
```

The static script validates that all five probe entry points exist and that Q8.7 exposure remains isolated to the test package.

## Runtime validation event

The runtime validation event for PR #150 is:

```txt
event cbp_q8_probe_debug.1
```

The full revalidation suite event is not required for #150:

```txt
event cbp_revalidate_debug.1   # not required for Q8 probe validation
```

The revalidation summarizer may report zero full-suite scenarios if only the Q8 probe event was run. That does not invalidate PR #150.

## Observed runtime evidence — 2026-07-06

Observed PASS markers:

```txt
ModeU5 Q8.2 PROBE us10_pending_gate PASS wheat_pending=0.0000
ModeU5 Q8.4 PROBE helper_inventory PASS runtime_noop_static_inventory_required
ModeU5 Q8.5 PROBE dirty_cache_lifecycle PASS repair_count=3
ModeU5 Q8.6 PROBE market_slice_candidate PASS
ModeU5 Q8.7 PROBE global_market_iterator PASS count=129
ModeU5 Q8 PROBE RESULT all_remaining_candidates PASS
```

Decision:

```txt
Q8 probe runtime validation: PASS
Q8.7 every_market_in_world test-package exposure: CONFIRMED for probe usage
Gameplay dispatcher replacement: NOT APPROVED by this probe
```

## TECH-01 implications

### TECH-01 row 002 — `every_market_in_world`

Existing row status remains:

```txt
CONFIRMED
```

Additional test basis:

```txt
PR #150 / Q8.7 runtime probe confirmed that `every_market_in_world` can iterate markets from an isolated test-package event and counted 129 markets.
```

Boundary:

```txt
The exposure is confirmed for controlled test-package probing.
This does not authorize replacing the market-center ownership workaround in gameplay runtime.
A future implementation PR must prove equivalent ordering, ownership semantics, and runtime cost before any dispatcher switch.
```

### TECH-01 rows 111 / 125 / 126 — market-country cache and list storage

PR #150 exercises dirty repair and candidate-market lists but does not change these rows:

```txt
111 — global variable-list scheduling remains CONFIRMED.
125 — rebuilt current-market country work cache remains CONFIRMED.
126 — durable per-market country-list cache remains NOT_CONFIRMED.
```

Q8.5 validates that the current dirty writer/consumer surface can be exercised. It does not prove durable per-market cache storage.

### TECH-01 row 110 — optional PASS-marker reads

PR #150 result events rely on marker presence, not numeric comparison against absent variables.

This is aligned with row 110:

```txt
Read optional PASS/FAIL markers through `has_global_variable`.
Do not compare unset numeric variables in result-event triggers.
```

## Known cleanup items

The runtime evidence is sufficient for probe PASS, but the log is not clean:

```txt
- Q8.7 emitted PASS count=129 but also produced unset-counter script errors around cbp_test_q8_7_global_market_count.
- Q8 probe event localization keys are missing.
```

These should be handled as cleanup before treating #150 as clean-log validated.

## Resulting rule

For PR #150:

```txt
Required runtime validation event: event cbp_q8_probe_debug.1
Not required: event cbp_revalidate_debug.1
```

A future Q8 implementation PR must not cite #150 as authorization to change gameplay runtime. It may cite #150 only as probe evidence for the five candidate surfaces.

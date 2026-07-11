# PR #69 runtime validation — 2026-07-11

## Accepted annual-layer provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
commit: 87a1e29c1751adbc5955c3ac3be30267ee93f123
runtime mode: debug
source_dirty: no
```

Validated annual fixture:

```txt
baseline                         1.2000
12 satisfied months             1.2120
12 unsatisfied months           1.1880
mixed year                      1.2000
zero-observation year           1.2000
annual counters after read      0
PASS
```

The fixture explicitly seeds its records, so this result remains valid after later integration redesigns.

## Current architecture under test

PR #69 now uses:

```txt
1.20 = explicit one-time initialized saved state
1.00 = disabled / missing / uninitialized / invalid fallback
```

The former exact-path vanilla `pop_demands.txt` generator has been removed.

Current vanilla integration candidate:

```txt
INJECT:pop_demand = {
    wheat = {
        multiply = "modeu5_us04_live_pop_demand_multiplier_wheat"
    }
}
```

No Paradox demand formula is copied or generated.

## Engine question

Runtime must establish how nested injection behaves:

```txt
A. merge into existing wheat script value     desired
B. replace existing wheat script value        reject
C. duplicate-key/parser/database error         reject
```

The wiki-level database entry rule establishes that `INJECT:key` adds content to an existing object, but the nested repeated wheat-key behavior still requires empirical EU5 validation.

## Static implementation status

Implemented:

```txt
- tracked wheat-only INJECT file;
- tracked production Pop-scope multiplier value;
- multiplier-1 failback;
- versioned one-time 1.20 initialization;
- yearly updates on existing records only;
- deletion of the vanilla override generator;
- automatic cleanup of stale generated override artifacts;
- static architecture validator forbidding vanilla regeneration;
- endpoint adapter delegating to the production value;
- wheat/beer controlled runtime demand probe.
```

## Required new-campaign runtime validation

Run the normal static/install sequence, then start a clean campaign and let at least one full in-game day pass.

```txt
event modeu5_us04_debug.1
```

### Scenario 1 — initialization

```txt
us04_pop_demand_initialization
```

Required:

```txt
version=1
wheat=1.2000
beer=1.2000
second call remains idempotent
deleted wheat key is not recreated
missing fallback=1.0000
PASS
```

### Scenario 2 — production Pop endpoint

```txt
us04_pop_demand_endpoint
```

Required:

```txt
seeded=1.3700
missing=1.0000
uninitialized=1.0000
disabled=1.0000
PASS
```

The test delegates to the exact production script value referenced by the injection file.

### Scenario 3 — nested injection behavior

```txt
us04_vanilla_pop_demand_integration
```

Probe:

```txt
wheat coefficient 1.0 -> capture wheat and beer demand
wheat coefficient 4.0 -> capture wheat and beer demand
```

Acceptance:

```txt
wheat low demand > 0
wheat high demand > wheat low demand
beer high demand approximately equals beer low demand
no duplicate-key/parser/database/value errors
```

Expected marker:

```txt
ModeU5 US-04 VANILLA DEMAND RESULT injection_nested_merge_candidate PASS
```

A failure reason `wheat_baseline_nonpositive_possible_nested_replacement` is an explicit replacement/corruption warning.

## Log review

```sh
grep -E \
"us04_pop_demand_initialization|us04_pop_demand_endpoint|us04_vanilla_pop_demand_integration|ModeU5 US-04 INITIALIZATION|ModeU5 US-04 ENDPOINT|ModeU5 US-04 VANILLA DEMAND|INJECT|pop_demand|Duplicated key|duplicate|Failed to read|Failed to find|database|This scope doesn't support variables|ASSERT FAIL" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/error.log" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/debug.log" || true
```

The standard summarizer also displays all US-04 diagnostic families:

```sh
./tools/summarize_modeu5_test_logs.sh --expected none
```

## Current status

```txt
Annual fixture arithmetic:                  PASS
Annual fixture counter reset:               PASS
Versioned world initialization:             IMPLEMENTED / RUNTIME PENDING
Multiplier-1 safe fallback:                 IMPLEMENTED / RUNTIME PENDING
Production Pop.location endpoint:           IMPLEMENTED / RUNTIME PENDING
Nested wheat injection behavior:            IMPLEMENTED / RUNTIME PENDING
Vanilla formula regeneration:               REMOVED
Live US-10.3 location outcome handoff:       NOT_CONFIRMED
All-good injection:                         DEFERRED
TECH-01 #039:                               NOT_CONFIRMED
Complete PR #69 runtime acceptance:         PENDING
```

## Separate full-revalidation tail

The earlier repository-wide full revalidation entered `us17_us20_route_reconciliation` without a terminal marker or final summary. That remains separate from US-04.

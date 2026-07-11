# PR #69 runtime validation — 2026-07-11

## Accepted annual-layer provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
commit: 87a1e29c1751adbc5955c3ac3be30267ee93f123
runtime mode: debug
source_dirty: no
installed_at_utc: 2026-07-11T10:18:34Z to 2026-07-11T10:18:36Z
```

All installed ModeU5 packages reported the same clean source commit.

## Static and load result at the accepted commit

The requested static/install sequence passed:

```txt
ModeU5 CI static contract validation passed
ModeU5 module package validation passed
ModeU5 CMM value-link validation passed
Unclassified persistent maps/lists: 0
Direct stock-map write candidates outside generated adapter template: 0
Ownership/rebuild/reset policy gaps: 0
ModeU5 generator and validator convention checks passed
ModeU5 script-safety validation passed
source_dirty=no
```

The previous US-04 parser/load defects were absent:

```txt
no generated reset-helper collision
no invalid named script-value read
no nested add_to_variable_map arithmetic failure
no invalid event-target link for the annual value block
```

## Accepted annual runtime result

Focused and full-chain execution both produced:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_adaptation
ModeU5 US-04 DUMP base_multiplier=1.2000 wheat_multiplier=1.2120 beer_multiplier=1.1880 cloth_multiplier=1.2000 tools_multiplier=1.2000 wheat_sat=0 wheat_unsat=0 beer_sat=0 beer_unsat=0 cloth_sat=0 cloth_unsat=0 tools_sat=0 tools_unsat=0
ModeU5 US-04 RESULT pop_demand_adaptation PASS
ModeU5 TEST PASS scenario=us04_pop_demand_adaptation
```

Validated annual fixture behavior:

```txt
baseline                         1.2000
12 satisfied months             1.2120
12 unsatisfied months           1.1880
mixed year                      1.2000
zero-observation year           1.2000
annual counters after read      0
```

The fixture explicitly seeds its test records. This annual result remains valid after the later lifecycle redesign.

## Architecture correction after annual acceptance

The branch subsequently adopted the stricter lifecycle:

```txt
1.20 = explicit one-time initialized saved state
1.00 = disabled / missing / uninitialized / invalid fallback
```

Changes after commit `87a1e29` include:

```txt
- versioned new-campaign world initialization;
- every location × supported good seeded once at 1.20;
- initialization version written only after the world pass;
- live reader starts at multiplier 1;
- live reader requires both integration and initialization gates;
- yearly adaptation modifies existing records only;
- missing records are never recreated by normal yearly runtime;
- live vanilla integration narrowed to a wheat-only probe;
- new initialization, endpoint and vanilla-demand tests;
- static US-04 architecture validator.
```

Therefore the earlier statement `PR #69 runtime acceptance: PASS` now applies only to the annual fixture layer, not to the revised complete PR.

## New runtime validation required

Use a clean new campaign, unpause for at least one full day, then run:

```txt
event modeu5_us04_debug.1
```

### Scenario 1 — versioned initialization

```txt
us04_pop_demand_initialization
```

Required markers:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_initialization
ModeU5 US-04 INITIALIZATION DUMP version=1 wheat=1.2000 beer=1.2000 missing_fallback=1.0000
ModeU5 US-04 INITIALIZATION RESULT versioned_seed PASS
ModeU5 TEST PASS scenario=us04_pop_demand_initialization
```

This must prove:

```txt
initial seed = 1.20
second initialization call is idempotent
deleted key is not recreated while version = 1
missing key reads as multiplier 1
```

### Scenario 2 — Pop-scope location endpoint

```txt
us04_pop_demand_endpoint
```

Required markers:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_endpoint
ModeU5 US-04 ENDPOINT DUMP seeded=1.3700 missing=1.0000 uninitialized=1.0000 disabled=1.0000
ModeU5 US-04 ENDPOINT RESULT pop_scope_location_map PASS
ModeU5 TEST PASS scenario=us04_pop_demand_endpoint
```

### Scenario 3 — vanilla wheat demand response

```txt
us04_vanilla_pop_demand_integration
```

Required markers:

```txt
ModeU5 TEST ENTERED scenario=us04_vanilla_pop_demand_integration
ModeU5 US-04 VANILLA DEMAND DUMP wheat_low_multiplier=1.0000 ... wheat_high_multiplier=4.0000 ... delta=<positive>
ModeU5 US-04 VANILLA DEMAND RESULT integrated_pop_demand PASS
ModeU5 TEST PASS scenario=us04_vanilla_pop_demand_integration
```

Only this result can confirm that vanilla `pop_demand.wheat` consumes the location coefficient.

## TECH-01 boundary

Still not proven:

```txt
vanilla live Pop requested consumption reads the ModeU5 location coefficient
monthly vanilla Pop demand feeds the intended location × good US-10.3 counters
all-good integration is safe
```

TECH-01 #039 remains `NOT_CONFIRMED`.

## Separate full-revalidation tail

The earlier repository-wide chain entered:

```txt
us17_us20_route_reconciliation
```

without emitting its terminal marker or `main_revalidation_summary`. This remains separate from the accepted annual US-04 fixture and from the new US-04 runtime probes.

## Separate US-09 observation

The earlier command sequence generated 25 US-09 building overrides on the first pass and 26 on an install-triggered pass. This remains a separate generation-order observation.

## Current PR #69 status

```txt
Annual fixture arithmetic:                  PASS
Annual fixture counter reset:               PASS
Versioned world initialization:             IMPLEMENTED / RUNTIME PENDING
Missing-state vanilla fallback:             IMPLEMENTED / RUNTIME PENDING
Wheat Pop.location endpoint:                IMPLEMENTED / RUNTIME PENDING
Vanilla wheat market-demand response:       IMPLEMENTED / RUNTIME PENDING
Live US-10.3 location outcome handoff:       NOT_CONFIRMED
All-good live integration:                  DEFERRED
TECH-01 #039:                               NOT_CONFIRMED
PR #69 complete runtime acceptance:         PENDING
```

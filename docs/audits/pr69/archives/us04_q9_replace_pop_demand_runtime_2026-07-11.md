# US-04 Q9 full `REPLACE:pop_demand` runtime — 2026-07-11

## Run provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
installed commit: d914cc12dd83828c13fd02ed74c0c16c06089f60
source_dirty: no
runtime mode: debug
package: cbp_core_tests_q9 enabled
```

## Important test isolation note

The Q9 package contains a destructive static replacement:

```txt
REPLACE:pop_demand = {
    books = {
        multiply = global_var:cbp_us04_q9_replace_global_books
    }
}
```

Therefore any subsequent Q7/Q8 or additive syntax-matrix result from the same loaded playset is contaminated by the Q9 replacement package and must not be interpreted as a clean additive-probe result.

The Q7/Q8 lines observed after Q9 in this run are ignored for evidence purposes.

## First Q9 attempt

The first attempt was blocked because the control good changed across the monthly window:

```txt
control_good=wool low=16.5095 high=17.5030 delta=0.9934
books source_low=1.0000 source_high=4.0000 low=0.6440 high=0.6440 delta=0.0000
BLOCKED reason=unstable_control
```

This is not a failure of Q9.

## Second Q9 attempt

The second attempt had a stable control:

```txt
control_good=wool low=18.3057 high=18.3057 delta=0.0000
```

The Q9 replacement source changed from 1 to 4:

```txt
source_low=1.0000
source_high=4.0000
```

Books demand changed:

```txt
books low=0.6440
books high=1.0270
delta=0.3830
```

Result:

```txt
ModeU5 US-04 VANILLA DEMAND RESULT q9_replace id=09 syntax=replace_pop_demand good=books PASS
ModeU5 TEST PASS scenario=us04_q9_replace_pop_demand
```

## Interpretation

Q9 proves that a full `REPLACE:pop_demand` can affect runtime demand for a good.

This means the earlier additive negative results should be interpreted as:

```txt
Additive INJECT-style mutation of the hardcoded pop_demand object is ineffective for the tested shapes.
```

not as:

```txt
pop_demand cannot be modded at all.
```

## Limits of the proof

The response was not a direct 4× final market-demand response:

```txt
0.6440 -> 1.0270
```

Therefore Q9 does not prove the final business formula yet. It proves that full replacement reaches the engine, while the final observed demand remains affected by the vanilla demand lifecycle, Pop aggregation, market context, or other downstream factors.

Q9 also does not prove a safe production approach, because full replacement may require copying or owning the vanilla `pop_demand` object and can be patch-fragile.

## Decision impact

Validated:

```txt
- Full replacement is a live route into vanilla pop_demand.
- Additive injection failure is probably a merge/override issue, not absolute engine impossibility.
```

Still not validated:

```txt
- Read vanilla Pop × good base consumption directly.
- Initialize that Pop × good value to vanilla × 1.20 once.
- Persist/update it yearly without copying fragile vanilla formulas.
- Confirm final Pop consumption/demand matches the intended US-04 business rule.
```

## Next engineering options

1. Build a controlled exact-replacement probe with a constant/simple formula to map how final demand scales.
2. If full replacement remains the only path, decide whether copying/owning the vanilla `pop_demand` object is acceptable.
3. Prefer asking for engine exposure if a non-fragile Pop × good read/write/multiplier endpoint is required.

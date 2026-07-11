# US-04 injection probe candidate 1 — runtime result

Date: 2026-07-11

Tested candidate:

```txt
INJECT:pop_demand = {
    wheat = {
        multiply = "modeu5_us04_live_pop_demand_multiplier_wheat"
    }
}
```

## Results

### Production Pop → location value

```txt
seeded=1.3700
missing=1.0000
uninitialized=1.0000
disabled=1.0000
```

Result:

```txt
ModeU5 TEST PASS scenario=us04_pop_demand_endpoint
```

Conclusion: the production script value correctly resolves Pop → location and reads the location × wheat coefficient. Its safe fallback behavior is confirmed.

### Vanilla wheat demand response

```txt
wheat_low_multiplier=1.0000
wheat_low=54.2594
wheat_high_multiplier=4.0000
wheat_high=54.2594
wheat_delta=0.0000
beer_low=9.2151
beer_high=9.2151
beer_delta=0.0000
```

Result:

```txt
ModeU5 US-04 VANILLA DEMAND RESULT injection_nested_merge_candidate FAIL
ModeU5 TEST FAIL scenario=us04_vanilla_pop_demand_integration
```

Conclusion:

```txt
- the file loaded without an observed duplicate-key/parser/database error;
- vanilla wheat demand remained positive;
- changing the production multiplier from 1 to 4 had no effect;
- the plain repeated wheat child was therefore not merged into the existing wheat script value;
- candidate 1 is rejected.
```

This result does not invalidate the location × good storage model, the Pop-scope reader, or annual adaptation.

### Annual adaptation

```txt
base_multiplier=1.2000
wheat_multiplier=1.2120
beer_multiplier=1.1880
cloth_multiplier=1.2000
tools_multiplier=1.2000
annual counters=0
```

Result:

```txt
ModeU5 TEST PASS scenario=us04_pop_demand_adaptation
```

Conclusion: the US-04 business arithmetic remains confirmed.

### Initialization lifecycle

Result:

```txt
ModeU5 TEST BLOCKED scenario=us04_pop_demand_initialization reason=day1_initialization_not_completed
```

This is not a failure. The test was invoked before the delayed day-1 initialization gate existed. It must be rerun after the new campaign advances beyond the delayed startup pulse.

## Next candidate

```txt
INJECT:pop_demand = {
    INJECT:wheat = {
        multiply = "modeu5_us04_live_pop_demand_multiplier_wheat"
    }
}
```

Nested entry-mode behavior is undocumented for this object shape and remains an empirical probe.

Acceptance remains:

```txt
wheat demand at multiplier 1 > 0
wheat demand at multiplier 4 > wheat demand at multiplier 1
beer demand unchanged
no parser/database/duplicate errors
```

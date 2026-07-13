# US-04 Q10/Q10b/Q10c replacement lifecycle runtime — 2026-07-11

## Context

After Q9 initially appeared to pass, Q10/Q10b/Q10c were added to distinguish causal runtime response from demand-cache/background-regime changes.

The active package was the isolated destructive replacement package:

```txt
packages/modeu5_core_tests_q9
```

The replacement under test remained:

```txt
REPLACE:pop_demand = {
    books = {
        multiply = global_var:modeu5_us04_q9_replace_global_books
    }
}
```

## Q10c — daily hold at 0.99 for ten days

Purpose:

```txt
Capture vanilla output at source=1.00, then hold source=0.99 for ten consecutive days.
```

Runtime output:

```txt
day=00 source=1.0000 books=0.6440 control_wool=16.4355
day=01 source=0.9900 books=0.6440 control_wool=16.4355
day=02 source=0.9900 books=0.6440 control_wool=16.4355
day=03 source=0.9900 books=0.6440 control_wool=16.4355
day=04 source=0.9900 books=0.6440 control_wool=16.4355
day=05 source=0.9900 books=0.6440 control_wool=16.4355
day=06 source=0.9900 books=0.6440 control_wool=16.4355
day=07 source=0.9900 books=0.6440 control_wool=16.4355
day=08 source=0.9900 books=0.6440 control_wool=16.4355
day=09 source=0.9900 books=0.6440 control_wool=16.4355
day=10 source=0.9900 books=0.6440 control_wool=16.4355
```

Result:

```txt
COMPLETE held_source=0.9900 days=10
PASS scenario=us04_q10c_replace_pop_demand_daily_099
```

Interpretation:

```txt
No intra-month response to a held 0.99 runtime-global change.
```

## Q10b — same-month curve

Purpose:

```txt
Measure source=1.00 -> 0.99 -> 1.01 -> 1.20 -> 4.00 inside the same month.
```

Runtime output:

```txt
point=100 source=1.0000 books=1.0256 control_wool=15.5805
point=099 source=0.9900 books=1.0256 control_wool=15.5805
point=101 source=1.0100 books=1.0256 control_wool=15.5805
point=120 source=1.2000 books=1.0256 control_wool=15.5805
point=400 source=4.0000 books=1.0256 control_wool=15.5805
COMPLETE delta099_vs100=0.0000 delta101_vs100=0.0000 delta120_vs100=0.0000 delta400_vs100=0.0000
```

Interpretation:

```txt
No same-month response to runtime-global changes, including source=4.00.
```

## Q10 — monthly curve

Purpose:

```txt
Measure source=1.00 -> 0.99 -> 1.01 -> 1.20 -> 4.00 with monthly waits.
```

Runtime output:

```txt
point=100 source=1.0000 books=0.6440 control_wool=15.0407
point=099 source=0.9900 books=0.6440 control_wool=14.1706
point=101 source=1.0100 books=0.6440 control_wool=13.5274
point=120 source=1.2000 books=0.6440 control_wool=15.9008
point=400 source=4.0000 books=0.6440 control_wool=17.4407
COMPLETE delta099_vs100=0.0000 delta101_vs100=0.0000 delta120_vs100=0.0000 delta400_vs100=0.0000
```

Interpretation:

```txt
No monthly response to runtime-global changes, including source=4.00.
The control changed significantly, so the environment was not stable; however, books remained exactly flat despite all source changes.
```

## Revised interpretation of Q9

The earlier Q9 run showed:

```txt
books source_low=1.0000 source_high=4.0000 low=0.6440 high=1.0270 delta=0.3830
PASS
```

Given Q10/Q10b/Q10c, that Q9 result should no longer be treated as causal proof that changing `global_var:modeu5_us04_q9_replace_global_books` at runtime updates `pop_demand`.

More conservative interpretation:

```txt
Q9 showed that books demand can differ across the replacement-test session, but Q10/Q10b/Q10c failed to reproduce a causal response to runtime-global changes.
```

The likely issue is that the `pop_demand` script value is parsed/evaluated/cached in a way that does not re-read the global variable after load or after the tested refresh windows.

## Current conclusion

```txt
REPLACE:pop_demand with a runtime global is not yet a viable implementation path for yearly US-04 updates.
```

Supported conclusions:

```txt
- Additive INJECT-style mutation is rejected for tested shapes.
- Full REPLACE can be loaded syntactically in an isolated package.
- Runtime global changes inside that replacement did not affect books demand in Q10/Q10b/Q10c.
- The original Pop × good read/write/update requirement remains NOT_CONFIRMED.
```

Open possibilities:

```txt
- A full replacement using static compile-time values may affect initial demand, but cannot provide yearly runtime updates.
- A different script-value form may be re-evaluated dynamically.
- A true Pop × good engine endpoint may be required.
```

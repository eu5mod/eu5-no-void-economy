# US-04 Q7/Q8 globals and observed-current target runtime — 2026-07-11

## Run provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
installed commit: f8c03ed0b50e4c1cc0e167319311002a055b18fc
source_dirty: no
runtime mode: debug
campaign: existing campaign, not a fresh new campaign
```

## Q7/Q8 direct-global probe

The focused Q7/Q8 probe used positive-demand goods:

```txt
Q7: books      direct global_var multiplier
Q8: furniture  direct global_var wrapped in value block
```

Control stayed stable:

```txt
wool low=16.5095
wool high=16.5095
delta=0.0000
```

Q7 result:

```txt
id=07 syntax=direct_global good=books
source_low=1.0000
source_high=4.0000
low=0.6440
high=0.6440
delta=0.0000
FAIL reason=no_target_response
```

Q8 result:

```txt
id=08 syntax=direct_global_value_block good=furniture
source_low=1.0000
source_high=4.0000
low=0.5928
high=0.5928
delta=0.0000
FAIL reason=no_target_response
```

Summary:

```txt
ModeU5 US-04 INJECTION MATRIX SUMMARY q7_q8_positive pass=0 fail=2 blocked=0
ModeU5 TEST FAIL scenario=us04_q7_q8_positive_globals
```

Interpretation:

```txt
- The selected goods had positive baseline demand.
- The global source values changed from 1.0 to 4.0.
- Vanilla market demand did not change.
```

Therefore Q7/Q8 are now valid negative results, not blocked probes.

## Observed-current target architecture

The observed-current target architecture passed in the same existing campaign.

Runtime output:

```txt
observed=1.0232
initial=1.2278
satisfied_target=1.2401
shortage_target=1.2156
consumed_satisfied=1.2278
consumed_unsatisfied=0.0000
```

Expected math:

```txt
initial = observed × 1.20
        = 1.0232 × 1.20
        = 1.22784

satisfied_target = initial × 1.01
                 = 1.2401184

shortage_target = initial × 0.99
                = 1.2155616
```

Observed values match expected rounded log output.

The target also fed ModeU5 stock consumption:

```txt
consumed_satisfied = initial target
consumed_unsatisfied = 0
```

This means the target was not only persisted and transitioned; it was also usable as a consumption request in the stock layer.

Result:

```txt
ModeU5 US-04 RESULT observed_current_target PASS
ModeU5 TEST PASS scenario=us04_observed_current_target_architecture
```

## Decision

Upstream vanilla `pop_demand` mutation is rejected for the tested additive/static candidates, including direct global variables.

The implementation path should be:

```txt
observe current engine demand
  -> initialize ModeU5 current consumption target = observed × 1.20
  -> yearly target transition = current target × 0.99 / 1.00 / 1.01
  -> feed ModeU5 stock consumption from that target
```

## Caveats

This was an existing-campaign run, not a fresh new-campaign initialization run.

Therefore this evidence confirms:

```txt
- positive-demand Q7/Q8 direct-global probes are valid negatives;
- observed-current target math works;
- observed-current target can feed ModeU5 consumption in a controlled fixture.
```

It does not by itself confirm:

```txt
- fresh new-campaign lazy country-owned location initialization;
- broad all-goods/all-countries production integration;
- annual production pulse integration beyond the controlled fixture.
```

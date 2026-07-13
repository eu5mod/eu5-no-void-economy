# US-04 injection matrix runtime result — 2026-07-11

## Source / install provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
commit installed: 0946cb8de315d5d2483d2502dcdb7c973b821fcb
source_dirty: no
runtime mode: debug
installed_at_utc: 2026-07-11T13:53:10Z
```

Static validation before launch:

```txt
ModeU5 US-04 explicit additive syntax matrix validation passed
```

## Confirmed still passing

### US-04 annual business rule

```txt
base_multiplier=1.2000
wheat_multiplier=1.2120
beer_multiplier=1.1880
cloth_multiplier=1.2000
tools_multiplier=1.2000
annual counters reset to 0
```

Result:

```txt
ModeU5 US-04 RESULT pop_demand_adaptation PASS
```

### Production Pop → location endpoint

```txt
seeded=1.3700
missing=1.0000
uninitialized=1.0000
disabled=1.0000
```

Result:

```txt
ModeU5 US-04 ENDPOINT RESULT pop_scope_location_map PASS
```

Conclusion: the location coefficient reader and safe multiplier-1 fallback are confirmed.

## Additive candidates 01–06

Detailed rerun confirmed that candidates 01–06 had valid positive baselines and valid source changes from `1.0000` to `4.0000`, but no demand response:

```txt
id=01 plain_child wheat                 source 1 -> 4, low=56.1723 high=56.1723 delta=0.0000
id=02 inner_inject beer                 source 1 -> 4, low=9.2194  high=9.2194  delta=0.0000
id=03 inner_try_inject cloth            source 1 -> 4, low=15.6373 high=15.6373 delta=0.0000
id=04 inner_inject_or_create tools      source 1 -> 4, low=7.6701  high=7.6701  delta=0.0000
id=05 outer_try_inject fish             source 1 -> 4, low=24.0997 high=24.0997 delta=0.0000
id=06 outer_inject_or_create wine       source 1 -> 4, low=12.2536 high=12.2536 delta=0.0000
```

Control:

```txt
wool low=15.8076 high=15.8076 delta=0.0000
```

Conclusion:

```txt
Candidates 01–06 are rejected as no-target-response.
```

## Direct-global candidates 07–08

The original tea/coffee run was inconclusive because both goods had zero baseline demand:

```txt
id=07 direct_global tea                 source 1 -> 4, low=0 high=0 BLOCKED
id=08 direct_global_value_block coffee  source 1 -> 4, low=0 high=0 BLOCKED
```

Conclusion:

```txt
The global variables changed correctly, but the goods were invalid probes.
Direct-global syntax was not disproven by that run.
```

## Follow-up implemented

Candidates 07–08 were retargeted to positive-demand candidates:

```txt
id=07 direct_global              good=books
id=08 direct_global_value_block  good=furniture
```

A focused combined launcher now runs:

```txt
Q7/Q8 positive-demand global probes
then
observed-current target architecture test
```

## Architectural decision

Continue away from upstream vanilla `pop_demand` mutation unless the retargeted Q7/Q8 probe proves otherwise.

Target architecture now implemented as explicit helpers:

```txt
observe current engine demand
  -> initialize ModeU5 current consumption target = observed × 1.20
  -> yearly target transition = current target × 0.99 / 1.00 / 1.01
  -> feed ModeU5 stock consumption from the target
```

The first integrated test uses `books` and logs:

```txt
observed
initial target
satisfied-year target
shortage-year target
consumed_satisfied
consumed_unsatisfied
```

## Next runtime command

```txt
event cbp_us04_debug.1
```

Choose:

```txt
Run Q7/Q8 globals + observed-current target
```

Then advance four in-game days and run:

```sh
./tools/summarize_test_cbp_logs.sh --expected none
```

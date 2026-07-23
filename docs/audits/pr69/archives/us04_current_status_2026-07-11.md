# US-04 current status — 2026-07-11

## Current branch head

```txt
2fb1fb4434bec2ced571eac09bd5568f85bf323d
```

## Confirmed

```txt
Annual arithmetic:              PASS
Pop -> location endpoint:       PASS
Safe fallback to multiplier 1:  PASS
Candidates 01-06:               FAIL / no target response with positive baselines
Original Q7/Q8 tea/coffee:      BLOCKED / zero baseline demand
```

## Implemented follow-up

### Retargeted Q7/Q8

```txt
Q7 direct_global              -> books
Q8 direct_global_value_block  -> furniture
```

### Observed-current target architecture

Implemented explicit helpers:

```txt
in_game/common/scripted_effects/cbp_us04_observed_current_target_effects.txt
```

Flow:

```txt
observe current engine demand
  -> persist ModeU5 current consumption target by country × market × good
  -> initialize target = observed × 1.20
  -> yearly transition target × 1.01 / 1.00 / 0.99
  -> feed target into cbp_resolve_stock_consumption
```

### Combined runtime probe

Implemented explicit test:

```txt
packages/cbp_core_tests/in_game/common/scripted_effects/cbp_us04_q7_q8_and_target_architecture_test_effects.txt
```

Debug option:

```txt
Run Q7/Q8 globals + observed-current target
```

Runtime phases:

```txt
1. Set Q7/Q8 globals to 1.0
2. Capture books/furniture/wool low demand
3. Set Q7/Q8 globals to 4.0
4. Capture books/furniture/wool high demand
5. Classify Q7/Q8
6. Run observed-current books target architecture test
```

Expected logs:

```txt
ModeU5 US-04 INJECTION CANDIDATE id=07 syntax=direct_global good=books source_low=1.0000 source_high=4.0000 low=... high=... delta=...
ModeU5 US-04 INJECTION CANDIDATE id=08 syntax=direct_global_value_block good=furniture source_low=1.0000 source_high=4.0000 low=... high=... delta=...
ModeU5 US-04 INJECTION MATRIX SUMMARY q7_q8_positive pass=N fail=N blocked=N
ModeU5 US-04 DUMP observed_current_target good=books observed=... initial=... satisfied_target=... shortage_target=... consumed_satisfied=... consumed_unsatisfied=...
ModeU5 US-04 RESULT observed_current_target PASS|FAIL|BLOCKED
```

## Next runtime command

```txt
event cbp_us04_debug.1
```

Choose:

```txt
Run Q7/Q8 globals + observed-current target
```

Advance four in-game days, then:

```sh
./tools/summarize_cbp_logs.sh --expected none
```

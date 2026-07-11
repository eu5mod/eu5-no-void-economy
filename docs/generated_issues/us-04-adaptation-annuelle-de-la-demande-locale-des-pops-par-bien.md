# US-04 — Annual local Pop demand adjustment

Labels: `blocked:engine-exposure`, `module:economy`

## User Story

```txt
US-04 — Annual local Pop demand adjustment
```

As a player, I want actual Pop good demand in each location to adapt slowly after a full year of availability or shortage.

## Functional objective

Close the complete loop:

```txt
vanilla Pop requested demand
  -> monthly satisfied / shortage outcomes
  -> yearly location × good coefficient adjustment
  -> next year's vanilla Pop requested demand
```

Persisting an annual ModeU5 number is not enough. The stored coefficient must be consumed by vanilla `pop_demand`.

## Runtime state

ModeU5 owns one persistent coefficient per:

```txt
location × good
```

Physical representation:

```txt
location.variable_map(modeu5_pop_demand_multiplier|goods:<good>)
```

The Pop is only the evaluation scope used by vanilla `pop_demand`. It is not part of persistent storage.

## Safety invariant

```txt
1.20 = explicit one-time initialized saved state
1.00 = disabled, missing, uninitialized, or invalid-state fallback
```

A missing key must never silently recreate the `1.20` bonus.

Correct formula:

```txt
actual Pop-demand coefficient
  = complete vanilla coefficient
  × stored location × good coefficient
```

The baseline is applied once, during initialization only.

## One-time initialization

On a clean campaign:

```txt
on_game_start
  -> delay 1 day
  -> modeu5_initialize_pop_demand_multipliers_once
```

Initialization version:

```txt
modeu5_us04_multiplier_initialization_version = 1
```

Algorithm:

```txt
if version is missing or < 1:
    every_location
      -> for every supported good:
           if key does not exist:
               write 1.20
           else:
               preserve current value

    after the complete world pass:
        set version = 1
```

The version gate must be saved and global so campaign reloads do not apply the baseline again.

The initializer must be idempotent:

```txt
first run:   missing key -> 1.20
second run:  1.20 stays 1.20
reload:      1.20 stays 1.20
```

A key removed after initialization must remain missing during ordinary runtime. The once-only public initializer must not recreate it while version `1` is present.

## Live vanilla integration

Prototype only wheat before all-good expansion.

Generator:

```txt
tools/generate_us04_pop_demand_override.py --goods wheat
```

It reads the installed vanilla file:

```txt
<EU5_GAME_COMMON_DIR>/goods_demand/pop_demands.txt
```

It preserves the complete vanilla file and wraps only `pop_demand.wheat`:

```txt
pop_demand = {
    wheat = {
        value = {
            value = <unchanged vanilla wheat calculation>
            multiply = "modeu5_us04_live_pop_demand_multiplier_wheat"
        }
    }

    # every other vanilla good remains unchanged
}
```

Generated local artifacts:

```txt
packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt
packages/modeu5_economy_rebalance/in_game/common/script_values/modeu5_us04_pop_demand_values_generated.txt
```

The live wheat value starts at `1` and reads the stored value only when all gates pass:

```txt
integration marker exists
initialization version exists and >= 1
Pop.location has multiplier map
Pop.location has wheat key
```

Otherwise it returns `1` and vanilla remains unchanged.

## CMM behavior

```txt
Package: Rebalance Economy
Setting: Pop consumption influenced by offer & demand
```

The country-scoped setting is mirrored into:

```txt
modeu5_pop_demand_live_integration_enabled
```

Behavior:

```txt
setting disabled -> multiplier 1 -> vanilla
setting enabled + valid initialized key -> stored coefficient
setting enabled + missing key -> multiplier 1 -> vanilla
```

Disabling the setting does not delete stored coefficients.

## Yearly adaptation

Existing record only:

```txt
12 satisfied months / 0 shortage -> current × 1.01
0 satisfied months / 12 shortage -> current × 0.99
mixed year                       -> no write
zero-observation year            -> no write
```

The yearly helper must not create a record.

```txt
if multiplier key exists:
    apply 0.99 or 1.01 when required
else:
    do nothing
```

Annual counters reset after the decision reads them.

## Monthly outcome dependency

Target flow:

```txt
vanilla Pop requested demand
  -> US-10 stock removal
  -> requested quantity
  -> satisfied quantity
  -> unsatisfied quantity
  -> location × good annual counters
```

The exact live handoff from vanilla Pop demand into location-local US-10.3 outcome counters remains `NOT_CONFIRMED` until runtime evidence exists.

## Engine exposure status

| Need | Status |
|---|---|
| location variable-map storage keyed by goods | `CONFIRMED` |
| yearly country pulse | `CONFIRMED` |
| Pop-scope script value | prototype implemented |
| Pop → location → local map read | runtime pending |
| vanilla `pop_demand.wheat` consumes wrapper | runtime pending |
| full all-good integration | deferred |

TECH-01 #039 remains `NOT_CONFIRMED`.

## Files

Tracked source:

```txt
tools/templates/modeu5_us04_pop_demand_good.template.txt
tools/generate_us04_pop_demand_helpers.sh
tools/generate_us04_pop_demand_override.py
tools/validate_us04_pop_demand_architecture.py
tools/generate_all.sh
in_game/common/scripted_effects/modeu5_us04_pop_demand_live_integration_effects.txt
in_game/common/on_action/modeu5_stock_on_actions.txt
packages/modeu5_core_tests/in_game/common/script_values/modeu5_us04_pop_demand_endpoint_probe_values.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_initialization_test_effects.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_pop_demand_endpoint_test_effects.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_us04_vanilla_pop_demand_integration_test_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_us04_debug_events.txt
```

## Runtime tests

Start a new campaign and let at least one full day pass.

Run:

```txt
event modeu5_us04_debug.1
```

### Initialization lifecycle

Expected:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_initialization
ModeU5 US-04 INITIALIZATION DUMP version=1 wheat=1.2000 beer=1.2000 missing_fallback=1.0000
ModeU5 US-04 INITIALIZATION RESULT versioned_seed PASS
ModeU5 TEST PASS scenario=us04_pop_demand_initialization
```

This verifies:

```txt
version gate
1.20 initial seed
idempotent second call
missing key not recreated
missing key reads as vanilla multiplier 1
```

### Pop-scope endpoint

Expected:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_endpoint
ModeU5 US-04 ENDPOINT DUMP seeded=1.3700 missing=1.0000 uninitialized=1.0000 disabled=1.0000
ModeU5 US-04 ENDPOINT RESULT pop_scope_location_map PASS
ModeU5 TEST PASS scenario=us04_pop_demand_endpoint
```

### Vanilla market-demand response

Disposable-save probe:

```txt
capital wheat coefficient = 1.0
wait
read goods_demand_in_market(wheat)
capital wheat coefficient = 4.0
wait
read goods_demand_in_market(wheat)
```

Expected:

```txt
high demand > low demand
ModeU5 US-04 VANILLA DEMAND RESULT integrated_pop_demand PASS
ModeU5 TEST PASS scenario=us04_vanilla_pop_demand_integration
```

### Annual adaptation

Already validated:

```txt
1.2000 -> 1.2120 after full satisfaction
1.2000 -> 1.1880 after full shortage
mixed and zero-observation unchanged
counters reset
```

## Static validation

`generate_all.sh` runs:

```txt
tools/validate_us04_pop_demand_architecture.py
```

The validator rejects:

```txt
1.20 as a getter fallback
missing-record yearly recreation
initialization version written before world traversal
missing initialization gate in the live reader
all-good live wrapping before wheat acceptance
endpoint tests expecting 1.20 for missing state
```

## Acceptance criteria

- [x] Annual multiplier arithmetic implemented.
- [x] Annual counter reset implemented.
- [x] One-time versioned initializer implemented.
- [x] Initializer preserves existing values.
- [x] Missing-state read fallback is `1`.
- [x] Yearly runtime does not recreate missing records.
- [x] Wheat-only vanilla wrapper implemented.
- [x] Static architecture validator implemented.
- [ ] New-campaign initialization probe passes.
- [ ] Pop → location endpoint probe passes.
- [ ] Vanilla wheat demand response probe passes.
- [ ] Live US-10.3 location outcome handoff is confirmed.
- [ ] TECH-01 #039 is promoted with runtime evidence.
- [ ] Wheat pattern is generalized to all goods only after acceptance.

## Merge rule

PR #69 remains draft until the new-campaign tests pass without:

```txt
pop_demand duplicate-key errors
invalid Pop.location link errors
invalid variable-map reads
empty-scope variable writes
initialization version set before complete traversal
missing-key recreation
```

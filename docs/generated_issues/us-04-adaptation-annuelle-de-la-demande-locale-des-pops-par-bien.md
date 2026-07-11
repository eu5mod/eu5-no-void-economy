# US-04 — Annual local Pop demand adjustment

Labels: `blocked:engine-exposure`, `module:economy`

## User story

As a player, I want actual Pop demand in each location to adapt slowly after a full year of availability or shortage.

## Target loop

```txt
vanilla Pop requested demand
  -> monthly satisfied / shortage outcomes
  -> yearly location × good coefficient adjustment
  -> next year's vanilla Pop requested demand
```

## Runtime state

Persistent owner:

```txt
location
```

Persistent key/value:

```txt
modeu5_pop_demand_multiplier[goods:<good>] = coefficient
```

The Pop is only the evaluation scope used by vanilla `pop_demand`.

## Safety invariant

```txt
1.20 = explicit one-time initialized saved state
1.00 = disabled, missing, uninitialized, or invalid fallback
```

A missing record must never silently recreate the `1.20` baseline.

## One-time initialization

After the existing one-day campaign-start delay:

```txt
if modeu5_us04_multiplier_initialization_version is missing or < 1:
    every_location
      -> every supported good helper
         -> missing key: write 1.20
         -> existing key: preserve value

    after the complete world pass:
        initialization version = 1
```

The version gate is saved and global. Reloading a campaign does not apply `1.20` again.

## Yearly adjustment

Only an existing record may be changed:

```txt
12 satisfied / 0 shortage -> current × 1.01
0 satisfied / 12 shortage -> current × 0.99
mixed year                -> no write
zero-observation year     -> no write
missing multiplier key    -> no write
```

Annual counters reset after the decision reads them.

## Vanilla integration strategy

ModeU5 must not copy or regenerate Paradox's `pop_demand` formulas because those formulas may change between minor and major EU5 versions.

The current implementation is a wheat-only database-injection probe:

```txt
INJECT:pop_demand = {
    wheat = {
        multiply = "modeu5_us04_live_pop_demand_multiplier_wheat"
    }
}
```

Tracked file:

```txt
packages/modeu5_economy_rebalance/in_game/common/goods_demand/
zz_modeu5_us04_pop_demand_injection_probe.txt
```

Tracked production script value:

```txt
packages/modeu5_economy_rebalance/in_game/common/script_values/
modeu5_us04_pop_demand_injection_values.txt
```

No exact-path vanilla `pop_demands.txt` override is allowed.

The former generator has been removed:

```txt
tools/generate_us04_pop_demand_override.py
```

## Injection hypothesis

Desired behavior:

```txt
existing Paradox wheat demand formula
  + ModeU5 multiply operator
```

Possible engine outcomes:

```txt
A. nested wheat block is merged      accept
B. nested wheat block replaces       reject
C. duplicate/parser error            reject
```

The implementation remains a probe until runtime evidence supports A.

## Live Pop-scope multiplier

```txt
modeu5_us04_live_pop_demand_multiplier_wheat = {
    value = 1
    # read Pop.location × wheat only when all gates are valid
}
```

Required gates:

```txt
live CMM marker exists
initialization version exists and >= 1
Pop.location has multiplier map
Pop.location has wheat key
```

All other paths return `1`, preserving vanilla behavior.

## Compatibility cleanup

`generate_all.sh` deletes obsolete local artifacts from the abandoned generator:

```txt
packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt
packages/modeu5_economy_rebalance/in_game/common/script_values/
modeu5_us04_pop_demand_values_generated.txt
```

This prevents a stale exact-path override or duplicate production value from entering a local install.

## Runtime validation

Use a clean new campaign and let at least one full in-game day pass.

Run:

```txt
event modeu5_us04_debug.1
```

### Initialization lifecycle

Expected:

```txt
version=1
wheat=1.2000
beer=1.2000
second initialization call is idempotent
deleted wheat key is not recreated
missing fallback=1.0000
PASS
```

### Production Pop endpoint

The test adapter delegates to the exact production script value used by the injection.

Expected:

```txt
seeded=1.3700
missing=1.0000
uninitialized=1.0000
disabled=1.0000
PASS
```

### Injection semantics

Sequence:

```txt
wheat coefficient = 1.0
wait
capture wheat and beer market demand
wheat coefficient = 4.0
wait
capture wheat and beer market demand
```

Acceptance:

```txt
wheat demand at 1.0 > 0
wheat demand at 4.0 > wheat demand at 1.0
beer demand unchanged within tolerance
no duplicate-key/parser/database errors
```

Expected marker:

```txt
ModeU5 US-04 VANILLA DEMAND RESULT injection_nested_merge_candidate PASS
```

## Static validation

```txt
tools/validate_us04_pop_demand_architecture.py
```

The validator rejects:

```txt
- exact-path vanilla pop_demands.txt override;
- vanilla formula generator;
- copied wheat value formula;
- injection of goods other than wheat;
- 1.20 read fallback;
- missing-record yearly recreation;
- missing initialization gate;
- endpoint tests not using the production value.
```

## Accepted annual fixture

Previously validated:

```txt
1.2000 -> 1.2120 after full satisfaction
1.2000 -> 1.1880 after full shortage
mixed and zero-observation unchanged
annual counters reset
```

## Acceptance criteria

- [x] Versioned one-time `1.20` initializer implemented.
- [x] Missing-state live fallback is `1`.
- [x] Yearly runtime changes existing records only.
- [x] Exact-path vanilla regeneration removed.
- [x] Wheat-only injection probe implemented.
- [x] Production Pop-scope value tracked directly.
- [x] Stale override cleanup implemented.
- [x] Static injection architecture validator implemented.
- [ ] New-campaign initialization probe passes.
- [ ] Production Pop endpoint probe passes.
- [ ] Nested wheat injection behavior passes.
- [ ] Live US-10.3 location outcome handoff is confirmed.
- [ ] TECH-01 #039 is promoted with runtime evidence.
- [ ] Injection is generalized to all goods only after wheat acceptance.

## Current status

```txt
Annual adaptation fixture:            PASS
Injection architecture:               IMPLEMENTED / RUNTIME PENDING
All-good integration:                 DEFERRED
TECH-01 #039:                         NOT_CONFIRMED
```

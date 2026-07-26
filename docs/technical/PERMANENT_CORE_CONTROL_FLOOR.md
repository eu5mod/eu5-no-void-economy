# Permanent owner-core Control floor

## Business rule

A location that is a core of its current owner has a permanent minimum effective
Control based on its current location rank:

```txt
Rural Settlement = 25%
Town             = 30%
City             = 35%
Megalopolis      = 35%
```

The rule is additive-only:

```txt
control_delta = max(0, rank_floor - current_control)
```

The implementation never lowers Control. When a location stops being a core of
its owner, the floor simply stops being enforced and normal engine evolution
resumes.

## Runtime ownership

`cbp_enforce_owner_core_control_floor` is the single location-scoped business
effect. It checks the current owner, verifies `is_core_of`, selects the floor from
`location_rank`, and calls `change_control` only for a positive delta.

### Immediate event-driven paths

`on_location_changed_owner` invokes the effect immediately after the existing
CORE-03 succession handler. The effect rechecks the post-transition owner and core
status, so non-core conquests receive no floor while a returned owner core receives
the correct floor immediately.

The repository already subscribes to the hardcoded `on_location_changed_rank`
on-action. Its existing `cbp_capacity_location_rank_changed_pulse` invokes the same
floor effect after refreshing location capacity, so promotion or demotion is
handled immediately.

### Integration/core-status exposure

No confirmed integration-status on-action is currently available for a location.
The reviewed hardcoded on-action list exposes `on_location_changed_owner` and
`on_location_changed_rank`, but does not document an equivalent
`on_location_changed_integration_status`, `on_location_integrated`, or
`on_location_became_core` callback.

This is an exposure boundary, not proof that no internal engine callback exists.
Core status can also change without ownership or rank changing, so a low-frequency
fallback remains necessary until local Vanilla files, current script-docs output,
or a controlled runtime probe confirms a reliable callback.

### Yearly safety path

The fallback runs once per yearly country pulse, after the existing yearly US-04
adaptation:

```txt
cbp_yearly_pop_demand_adaptation_pulse
  -> cbp_run_yearly_pop_demand_adaptation_for_current_country
  -> cbp_core04_refresh_current_country_location_market_memory
     -> every_owned_location
        -> cbp_enforce_owner_core_control_floor
        -> refresh cbp_core04_last_known_market
```

A location becoming or ceasing to be a core without an owner or rank change is
therefore reconciled no later than the next yearly country pulse.

### Monthly CORE-04 path

The monthly stock cycle still requires location-market memory refresh, but it now
uses a dedicated memory-only effect:

```txt
cbp_monthly_stock_cycle_pulse
  -> cbp_core04_refresh_current_country_location_market_memory_monthly
     -> every_owned_location
        -> refresh cbp_core04_last_known_market
```

**No monthly Control-floor evaluation** occurs in this traversal.

### Campaign start and save repair

Both lifecycle hooks run after a one-day delay. A fresh campaign follows:

```txt
on_game_start
  -> cbp_start_game_stock_initialization_pulse
     -> cbp_start_game_stock_initialization_dispatcher
     -> cbp_core04_refresh_all_location_market_memory
```

A loaded save follows:

```txt
on_game_load
  -> cbp_load_game_stock_initialization_pulse
     -> cbp_repair_stock_lifecycle_on_game_load
        -> repair or rerun stock initialization when required
        -> cbp_core04_refresh_all_location_market_memory
```

The global CORE-04 refresh then retains the combined effect:

```txt
cbp_core04_refresh_all_location_market_memory
  -> every_country
     -> cbp_core04_refresh_current_country_location_market_memory
```

The global refresh is guarded by `cbp_stock_runtime_ready_trigger`. The start and
load sequences place it after initialization or readiness repair, so every
successfully initialized campaign evaluates the floor at least once without
waiting for the first yearly pulse. A failed or incompatible initialization
remains fail-closed and does not mutate Control.

## Persistence and performance

The floor stores no country or location variable, modifier, list, or stamp. Its
eligibility is derived directly from current owner, current core status, current
rank, and current Control.

The high-frequency monthly location traversal performs market-memory work only.
Owner and rank changes remain event-driven. The unresolved core-status edge case
adds one constant-time floor check per owned location only during the yearly
country pulse and during one-time lifecycle repair.

## Validation contract

Static validation requires:

- exact floors `0.25`, `0.30`, and `0.35`;
- an owner-core gate for every rank branch;
- positive delta calculation with `min = 0`;
- no subtractive or negative Control mutation;
- immediate owner-change re-evaluation through the existing CORE-03 on-action;
- immediate rank-change re-evaluation through `on_location_changed_rank`;
- use of the memory-only CORE-04 effect from the monthly country pulse;
- absence of the Control-floor effect from the monthly memory traversal;
- use of the combined CORE-04 effect from the yearly country pulse;
- registration of the delayed start and load initialization pulses;
- start ordering of stock initialization before
  `cbp_core04_refresh_all_location_market_memory`;
- load ordering of stock readiness repair before
  `cbp_core04_refresh_all_location_market_memory`;
- a runtime-ready guard on the global country traversal;
- an explicit record that integration/core-status event exposure is not confirmed.

Runtime acceptance still requires an in-game test because static validation cannot
prove the observed timing of Control recalculation relative to the engine's native
Control tick, nor prove that no undocumented integration-status hook exists in the
installed game build.

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

## Temporary scripted implementation

The intended long-term implementation is a native location modifier equivalent to
`minimum_control`. Until that modifier type exists, the floor must be maintained by
script because native Control continues to move toward `max_control` every month.

`cbp_enforce_owner_core_control_floor` is the single location-scoped business
effect. It checks the current owner, verifies `is_core_of`, selects the floor from
`location_rank`, and calls `change_control` only for a positive delta.

### Immediate event-driven paths

`on_location_changed_owner` invokes the effect immediately after the existing
CORE-03 succession handler. The effect rechecks the post-transition owner and core
status, so non-core conquests receive no floor while a returned owner core receives
the correct floor immediately.

The repository also subscribes to the hardcoded `on_location_changed_rank`
on-action. Its existing `cbp_capacity_location_rank_changed_pulse` invokes the same
floor effect after refreshing location capacity, so promotion or demotion is
handled immediately.

### Integration/core-status exposure

No confirmed integration-status on-action is currently available for a location.
The reviewed hardcoded on-action list exposes `on_location_changed_owner` and
`on_location_changed_rank`, but does not document an equivalent
`on_location_changed_integration_status`, `on_location_integrated`, or
`on_location_became_core` callback.

This remains an exposure boundary rather than proof that no internal engine
callback exists. The monthly authoritative clamp also covers these otherwise
unobserved core-status transitions.

## Monthly authoritative clamp

The monthly country pulse runs the combined CORE-04 location traversal after the
monthly stock/US-04 owner switch:

```txt
cbp_monthly_stock_cycle_pulse
  -> cbp_run_monthly_stock_cycle_q8_7_owner_switch
  -> cbp_core04_refresh_current_country_location_market_memory
     -> every_owned_location
        -> cbp_enforce_owner_core_control_floor
        -> refresh cbp_core04_last_known_market
```

This is deliberately one shared loop. The Control floor does not introduce a
second monthly `every_owned_location`; it reuses the existing CORE-04 market-memory
traversal.

The monthly cadence is required even when no owner, rank, or core-status transition
occurs. Without it, the initial scripted correction is temporary and native Control
moves the location back toward its lower `max_control` on subsequent monthly ticks.

The yearly US-04 pulse no longer runs an additional Control-floor traversal.

## Campaign start and save repair

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

The global CORE-04 refresh delegates to the same combined country effect:

```txt
cbp_core04_refresh_all_location_market_memory
  -> every_country
     -> cbp_core04_refresh_current_country_location_market_memory
```

The global refresh is guarded by `cbp_stock_runtime_ready_trigger`. The start and
load sequences place it after initialization or readiness repair. A failed or
incompatible initialization remains fail-closed and does not mutate Control.

## Observed timing boundary

The scripted target remains 25% / 30% / 35%. If the UI briefly shows values such as
20% / 25% / 30%, that five-point difference indicates the native Control movement
ran after an earlier scripted correction. Reapplying the correction from the
monthly country pulse is the current workaround; exact ordering relative to the
native Control tick must still be verified in-game.

## Persistence and performance

The floor stores no country or location variable, modifier, list, or stamp. Its
eligibility is derived directly from current owner, current core status, current
rank, and current Control.

Each country already traverses its owned locations monthly for CORE-04 market
memory. The floor adds constant-time eligibility and threshold checks inside that
existing loop, plus one positive `change_control` call only when the current value
is below the applicable threshold.

## Validation contract

Static validation requires:

- exact floors `0.25`, `0.30`, and `0.35`;
- an owner-core gate for every rank branch;
- positive delta calculation with `min = 0`;
- no subtractive or negative Control mutation;
- immediate owner-change re-evaluation through the existing CORE-03 on-action;
- immediate rank-change re-evaluation through `on_location_changed_rank`;
- monthly use of the combined CORE-04 effect after the monthly stock/US-04 owner
  switch;
- exactly one owned-location iterator in that combined country effect;
- no separate memory-only monthly effect;
- no duplicate yearly Control-floor traversal;
- registration of the delayed start and load initialization pulses;
- start ordering of stock initialization before
  `cbp_core04_refresh_all_location_market_memory`;
- load ordering of stock readiness repair before
  `cbp_core04_refresh_all_location_market_memory`;
- a runtime-ready guard on the global country traversal;
- an explicit record that integration/core-status event exposure is not confirmed.

Runtime acceptance still requires an in-game test because static validation cannot
prove the exact ordering between `monthly_country_pulse` and the engine's native
Control movement.

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

The monthly safety check is fused into the existing CORE-04 location-memory
traversal:

```txt
cbp_core04_refresh_current_country_location_market_memory
  -> every_owned_location
     -> cbp_enforce_owner_core_control_floor
     -> refresh cbp_core04_last_known_market
```

No separate monthly `every_owned_location` traversal is introduced.

The existing start/load repair path already delegates to the same country effect:

```txt
cbp_core04_refresh_all_location_market_memory
  -> every_country
     -> cbp_core04_refresh_current_country_location_market_memory
```

Therefore fresh campaigns, loaded saves, newly gained cores, and location-rank
changes all converge through the same authoritative loop. A newly gained core or
rank change is corrected no later than the next monthly country pulse.

`on_location_changed_owner` additionally invokes the same location-scoped effect
immediately after the existing CORE-03 succession handler. The effect rechecks the
post-transition owner and core status, so non-core conquests receive no floor.

## Persistence and performance

The floor stores no country or location variable, modifier, list, or stamp. Its
eligibility is derived directly from current owner, current core status, current
rank, and current Control.

The monthly implementation adds only constant-time checks and, when needed, one
positive `change_control` mutation inside a traversal that already exists for every
owned location.

## Validation contract

Static validation requires:

- exact floors `0.25`, `0.30`, and `0.35`;
- an owner-core gate for every rank branch;
- positive delta calculation with `min = 0`;
- no subtractive or negative Control mutation;
- the monthly call inside the existing CORE-04 `every_owned_location` body;
- no `every_owned_location` inside the dedicated floor effect file;
- immediate owner-change re-evaluation through the existing CORE-03 on-action;
- start/load reuse of `cbp_core04_refresh_all_location_market_memory`.

Runtime acceptance still requires an in-game test because static validation cannot
prove the observed timing of Control recalculation relative to the engine's own
monthly Control tick.

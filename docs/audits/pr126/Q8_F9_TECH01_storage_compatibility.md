# Q8 / F9 — TECH-01 and storage compatibility note

## Purpose

This note constrains the Q8/F9 rolling location-cache idea against the confirmed TECH-01 and variable-map storage limits.

The conclusion is:

```txt
F9 remains useful as a location-derived dirty-set and derived-cache system.

F9 should not be implemented as a rich persistent record per location unless a dedicated probe proves that the exact physical representation is safe and cheap.
```

This is a documentation-only update for PR146. It does not change runtime behaviour.

## Relevant confirmed constraints

TECH-01 and the variable-map storage model currently establish these constraints:

```txt
1. A native variable-map entry is one key mapped to one value.
2. The value may be a number or a scope.
3. Inline multi-field records are not confirmed.
4. Nested maps are not confirmed.
5. Unique persistent record scopes for every logical tuple are not confirmed.
6. Map names must be static identifiers.
7. Runtime-built map names are not allowed.
8. Market scope does not support variables in the tested EU5 build.
9. Logical multi-field records must be represented as synchronized map families.
```

Therefore this is not an accepted physical model:

```txt
location_cache[location] = {
  owner = country_scope
  market = market_scope
  capacity = number
  dirty = number
}
```

This is also not acceptable:

```txt
cbp_location_owner_$location_id$
cbp_location_market_$location_id$
cbp_location_capacity_$location_id$
```

Those forms either rely on nested/structured values or runtime-built map names.

## What remains compatible

A per-location cache is only compatible if represented as a fixed map family:

```txt
global map: cbp_location_cached_owner_by_location
  key:   location scope
  value: country scope

global map: cbp_location_cached_market_by_location
  key:   location scope
  value: market scope

global map: cbp_location_cached_capacity_by_location
  key:   location scope
  value: number
```

This is technically aligned with the confirmed `one key -> one value` model.

However, it is still map-heavy:

```txt
L locations * N persisted fields = many map entries
```

It should therefore be treated as a `TO_TEST` physical implementation, not as an assumed design baseline.

## Preferred reframing

The safer F9 design is not:

```txt
cache every location as a persistent record
```

The safer design is:

```txt
location-derived dirty-set and derived-cache system
```

That means the primary persisted state should be closer to:

```txt
dirty countries
dirty markets
dirty country-market pairs
country location-capacity pool
country-market capacity records
market participant work cache, if needed
```

The valuable outputs are the derived country/market caches, not necessarily a durable per-location fact table.

## Dirty-set first design

Use event-driven dirtying wherever confirmed:

```txt
on_location_changed_owner:
  root = changed location
  loser = previous owner
  winner = new owner

  current_market = root.market

  mark loser dirty
  mark winner dirty
  mark current_market dirty
  mark loser + current_market dirty
  mark winner + current_market dirty
```

This does not require storing a previous owner per location, because the hook already exposes loser and winner.

It may not require storing a previous market either if the dirtying is only for owner-change capacity and participant refresh in the current market.

## Market drift is the difficult case

Ownership drift has a confirmed hook path.

Market drift is harder because F9 has not confirmed a reliable `on_location_changed_market` hook.

There are two possible strategies:

```txt
Option A — cached-market comparison
  store cbp_location_cached_market_by_location
  daily rolling verifier compares current location.market to cached market
  if changed, dirty old market and new market

Option B — no per-location market cache
  periodically rebuild or shadow-check market participant caches from actual locations
  avoid persistent cached market per location
```

Option A is cleaner for detecting old/new market membership, but it introduces a global per-location map.

Option B is less elegant and may scan more, but it is safer if per-location map volume or scope-valued map entries prove costly.

Do not choose Option A until a probe confirms:

```txt
1. global map keyed by location can store market scope values reliably;
2. remove/re-add update works for location keys at scale;
3. save/reload preserves scope-valued map entries correctly;
4. the performance cost is lower than rebuilding affected participant caches directly.
```

## Early-exit limitation

Do not rely on true loop break semantics.

The likely available pattern is:

```txt
every_location_in_the_world = {
  limit = {
    NOT = { market already dirty }
  }

  if drift detected:
    mark market dirty
}
```

This can avoid repeated heavy writes for a market that is already dirty, but it probably still pays the iterator / limit-evaluation cost for remaining locations.

Therefore the main optimisation should not be framed as:

```txt
scan locations until one dirty market is found, then stop
```

It should be framed as:

```txt
avoid broad scans by writing dirty sets directly from lifecycle hooks
and only use rolling verification as a bounded audit/probe layer
```

## Revised profitability judgement

Split F9 into two parts:

```txt
F9a — dirty-set architecture
  status: likely profitable
  storage: compatible with existing country/market map-family patterns

F9b — per-location owner/market persistent cache
  status: uncertain / TO_TEST
  storage: compatible only as fixed single-field map families
  risk: high entry count and scope-valued map persistence cost
```

### F9a likely remains profitable

F9a avoids broad speculative rebuilds by making affected scopes explicit:

```txt
on location-owner change:
  dirty country / market / country-market state

monthly:
  rebuild only dirty country pools
  rebuild only dirty market participant caches
  refresh only dirty country-market records
```

This remains compatible with the existing country x market storage pattern.

### F9b is uncertain

F9b requires per-location owner/market maps for rolling drift detection:

```txt
location -> cached owner
location -> cached market
```

That may be valid as a map family, but it is not free. It should begin as a debug-only probe.

## Practical implementation sequence

Recommended sequence:

```txt
F9.1 Dirty-set probe from on_location_changed_owner
  - no per-location cache
  - mark dirty countries / markets / country-market pairs
  - log dirty counts

F9.2 Dirty rebuild consumers
  - rebuild country capacity pools only for dirty countries
  - rebuild market participant cache only for dirty markets
  - refresh country-market records only for dirty pairs

F9.3 Optional rolling verifier without live dependency
  - debug-only 1/30 location slice
  - compare current state to either shadow cache or live derived cache
  - log drift only

F9.4 Per-location cached-market probe only if needed
  - fixed global map keyed by location
  - value = market scope
  - verify save/load and remove/re-add replacement

F9.5 Promote the verifier only if metrics prove it replaces more work than it adds
```

## Guardrails to add to F9

```txt
1. Do not require a rich per-location record.
2. Do not use nested maps or multi-field map values.
3. Do not use runtime-built map names.
4. Prefer dirty derived country/market caches over full per-location storage.
5. Treat per-location cached owner/market maps as TO_TEST until probed.
6. Do not rely on loop early-exit semantics.
7. Rolling verification should be debug/probe first, live dependency later.
8. If the verifier cannot early-exit, keep it lightweight: compare, mark dirty, update only the tested cache field.
```

## Decision

F9 is compatible with TECH-01 only after this narrowing:

```txt
Accepted target:
  location-derived dirty-set architecture
  + derived country/market caches
  + optional tested per-location map-family verifier

Rejected target:
  rich per-location persistent cache record
  + broad monthly rebuild
  + dynamic map/helper names
```

Given the restrictions, F9 is still profitable if it primarily removes broad country-market preparation and repeated participant/capacity rebuilding.

It is not yet proven profitable as a full per-location owner/market cache. That part requires a small runtime/storage probe before implementation.

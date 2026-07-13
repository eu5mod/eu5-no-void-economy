# Q8 / F9 — Location owner/market cache with rolling verification

## Purpose

This note expands Q8 with a dedicated future optimisation finding: build a stable location owner/market cache, use location-change hooks where available, and verify the cache with a rolling daily slice rather than a single broad monthly full-world scan.

The target is to accelerate and stabilise:

```txt
market -> countries_present_in_market
country -> markets_present_in_country
country -> location capacity pool
country-market initialisation
promotion / detailed-market eligibility
```

This is a future optimisation / architecture finding. It should not be mixed into PR146 runtime behaviour.

## Core question

A location cache is attractive because many ModeU5 flows repeatedly need the same facts:

```txt
location -> owner country
location -> market
location -> capacity contribution
market -> countries present in market
country -> markets present in country
country-market -> exists / initialized
```

The risk is that a cache that is not kept current becomes wrong after conquest, ownership transfer, market changes, colonisation, split/merge behaviour, or other lifecycle changes.

Therefore, a startup-only cache is not sufficient unless all relevant changes are event-driven and perfectly captured.

The better design is:

```txt
startup full build
+ event-driven dirtying for known location changes
+ daily rolling verification of 1/30th of locations
+ monthly rebuild only for dirty derived caches
```

## Good idea vs false good idea

### Good idea

```txt
on game start / reload / migration:
  every_location_in_the_world:
    cache location owner
    cache location market
    cache location capacity contribution
    derive market-country membership
    derive country-market existence
    derive country location-capacity pools
```

Then:

```txt
on detected owner/market drift:
  dirty old country
  dirty new country
  dirty old market
  dirty new market
  dirty old country-market
  dirty new country-market
```

Then monthly:

```txt
rebuild only dirty country pools
rebuild only dirty market-country participant caches
run global market-local pass / promoted-market pass using derived caches
```

### False good idea

```txt
every month:
  every_location_in_the_world:
    compare owner / market
    rebuild all derived market-country and capacity caches
```

This is accurate but adds a permanent broad `O(L)` monthly tax and can become another heavy global pass before the already-expensive market/country/goods work.

### Better compromise

```txt
every day:
  verify 1/30th of world locations
  mark only drifted entities dirty

monthly:
  consume the accumulated dirty sets
  rebuild only affected derived caches
```

This preserves monthly accuracy while spreading verification cost across the month.

## Why daily 1/30 verification is attractive

A single monthly global location scan has this shape:

```txt
monthly spike = L locations
```

A rolling daily verifier has the same monthly order of work, but a much lower daily spike:

```txt
daily cost = L / 30 locations
monthly total = L locations
```

That is useful for a game tick because a large monthly spike is more visible than small daily checks.

The rolling verifier also improves mid-month correctness. If a market change has no reliable on-action hook, drift is detected within at most one rolling cycle rather than waiting indefinitely.

## Event-driven first, rolling verification second

The target should not rely only on scanning.

Use event-driven invalidation wherever the engine exposes reliable lifecycle hooks:

```txt
on_location_changed_owner:
  root = changed location
  loser = previous owner
  winner = new owner

  read cached market
  dirty cached market
  dirty loser country
  dirty winner country
  dirty loser-market membership
  dirty winner-market membership
  update cached owner
```

Owner changes are the clearest candidate for event-driven dirtying.

Market changes are less certain. A location has a market link, but the availability of a reliable market-change hook must be confirmed before relying on event-only updates. Until then, market drift should be detected by rolling verification:

```txt
rolling verifier:
  read current location market
  compare to cached location market
  if changed:
    dirty old market
    dirty new market
    dirty country-market membership
    update cached market
```

## Mapping and generated-helper restrictions

The design must avoid runtime-built map names and runtime-built helper names.

Do not do this:

```txt
cbp_location_cache_day_$day$
cbp_location_owner_$location_id$
cbp_location_market_$location_id$
```

Use fixed canonical maps and generated fixed helper surfaces instead:

```txt
cbp_location_cached_owner
cbp_location_cached_market
cbp_location_cached_capacity_contribution
cbp_location_cache_dirty_countries
cbp_location_cache_dirty_markets
cbp_location_cache_dirty_country_markets
```

Generate fixed day-slice helpers:

```txt
cbp_location_cache_verify_day_01
cbp_location_cache_verify_day_02
...
cbp_location_cache_verify_day_30
```

The dispatcher can be a generated fixed if-chain:

```txt
if current day = 1:
  cbp_location_cache_verify_day_01 = yes
if current day = 2:
  cbp_location_cache_verify_day_02 = yes
...
if current day = 30:
  cbp_location_cache_verify_day_30 = yes
```

This preserves the existing generator rule: helper names and map names must remain literal script identifiers.

## Possible slicing strategies

### Preferred if supported: ordered world-location slices

If the engine supports stable ordered location iteration with `position`, `min`, or `max`, generate daily slices over the ordered world-location list:

```txt
cbp_location_cache_verify_day_01:
  ordered_location_in_the_world position/min/max range for first 1/30

cbp_location_cache_verify_day_02:
  ordered_location_in_the_world position/min/max range for second 1/30
```

The key requirement is deterministic coverage. The same location should not be permanently skipped, and the same slice should not drift unpredictably between reloads.

### Fallback: generated location buckets

If ordered slicing cannot select stable ranges, generate explicit location buckets at build time if the location list is available to the generator:

```txt
cbp_location_cache_verify_day_01:
  verify literal location A
  verify literal location B
  ...

cbp_location_cache_verify_day_02:
  verify literal location C
  verify literal location D
  ...
```

This is more generated code, but it avoids runtime-built identifiers and gives predictable coverage.

### Last resort: full monthly verifier behind profile/debug

If daily slicing is not technically possible, keep the full verifier as audit/debug or low-frequency repair:

```txt
if cache strict audit enabled:
  every_location_in_the_world:
    compare owner / market with cached owner / market
    mark dirty on drift
```

Do not make this the default hot path unless profiling proves that it replaces more work than it adds.

## Derived caches to build from the location cache

### Location source facts

```txt
location_cached_owner
location_cached_market
location_cached_capacity_contribution
```

These are source-of-derivation caches. They are not the stock source of truth.

### Market participant cache

```txt
market -> countries_present_in_market
```

This cache is consumed by the market-local branch:

```txt
market-local pass:
  load countries_present_in_market
  for each present country:
    refresh country-market capacity
    run US-00 guarded dispatch
  for each present country:
    run US-10 guarded dispatch
```

### Country market-membership cache

```txt
country -> markets_present_in_country
```

This helps country preparation and capacity distribution:

```txt
country prep:
  know how many markets the country participates in
  know which country-market records may need initialisation
```

### Country location-capacity pool

```txt
country -> location_capacity_pool_total
country -> location_capacity_location_count
country -> location_capacity_pool_stamp
```

This is the cache that should feed F1 capacity-pool reuse.

### Country-market existence and initialisation

```txt
country-market exists
country-market initialized
country-market capacity record dirty
country-market stock maps initialized if needed
country-market demand/request surfaces initialized if needed
```

This is probably one of the biggest functional benefits: the mod can avoid initializing country-market surfaces for pairs that do not exist.

## Dirtying model

When a location owner changes:

```txt
old_owner = cached owner
new_owner = current owner
market    = cached or current market

mark old_owner dirty
mark new_owner dirty
mark market dirty
mark old_owner + market dirty
mark new_owner + market dirty
mark location dirty only until cache updated
```

When a location market changes:

```txt
owner      = cached or current owner
old_market = cached market
new_market = current market

mark old_market dirty
mark new_market dirty
mark owner + old_market dirty
mark owner + new_market dirty
mark location dirty only until cache updated
```

When both owner and market changed:

```txt
mark all four country-market combinations dirty if needed:
  old_owner + old_market
  old_owner + new_market
  new_owner + old_market
  new_owner + new_market
```

This is important because a location can leave one country-market pair and enter another.

## Rebuild model

The rolling verifier should mostly mark dirty state. It should not fully rebuild the world.

Monthly or scheduled cache-application phase:

```txt
for each dirty country:
  rebuild or update country location-capacity pool

for each dirty market:
  rebuild or update countries_present_in_market

for each dirty country-market:
  initialise / delete / refresh country-market records as required
```

If incremental add/remove is safe, use it:

```txt
owner changed from A to B in market M:
  remove location contribution from A capacity pool
  add location contribution to B capacity pool
  decrement A/M location count
  increment B/M location count
```

If incremental removal is not safe because list/map deletion is limited, use dirty rebuild:

```txt
mark A dirty
mark B dirty
mark M dirty
rebuild A pool from cached locations
rebuild B pool from cached locations
rebuild M participants from cached locations
```

The second approach is slower but safer under EU5 mapping restrictions.

## Interaction with F7 global market pass

F9 is especially valuable after F7.

F7 moves market-local orchestration to:

```txt
every_market_in_world:
  if detailed/promoted/human-relevant:
    run market-local work
```

F9 gives that market-local pass a clean market-owned participant cache:

```txt
market scope owns countries_present_in_market work cache
```

This avoids re-scanning every location in the market every time the global market pass processes a detailed market.

F9 also helps country prep before F7:

```txt
country prep:
  load country markets-present cache
  load or refresh country capacity pool
  initialise only real country-market pairs
```

## Interaction with F1 capacity-pool reuse

F1 says the country capacity pool should not be recalculated once per country-market inside promoted markets.

F9 provides the underlying mechanism:

```txt
location cache -> country location-capacity pool -> country-market capacity records
```

Target:

```txt
country preparation:
  prepare/stamp country-wide capacity pool once per country/month

global market pass:
  for each present country in market:
    reuse country-wide pool facts
    add / apply market-specific contribution
    write country-market capacity record
```

## Interaction with promotion and market-country initialisation

F9 can fast-track promotion because it gives stable derived facts:

```txt
market has human-relevant country
market has ModeU5 stock state
market has present countries
country participates in market
country-market pair exists
```

It can also avoid expensive speculative initialisation:

```txt
instead of:
  initialise many possible country-market pairs

use:
  initialise only country-market pairs derived from location cache / trade state / stock state
```

This is a structural performance win even if the daily verifier adds some scanning cost.

## Accuracy model

The cache should be considered monthly-valid only if:

```txt
1. startup full build has completed
2. all known event-driven dirty hooks have applied immediately
3. rolling verification has covered the whole world within the last 30 daily slices
4. dirty derived caches have been rebuilt or safely refreshed before the monthly market pass consumes them
```

If any condition fails, fall back to conservative behaviour:

```txt
strict mode:
  rebuild affected cache from actual locations

or debug/audit mode:
  log cache not trusted and run legacy local rebuild path
```

## Performance estimate using Q4 assumptions

Q4 uses these sizing assumptions:

```txt
C = 800 countries
M = 100 markets
P_normal = 100 retained/promoted markets
P_performance = 5 likely retained/promoted markets
K_m = 40 countries present in a promoted market
G_a = 10 active goods in a promoted market
G_market = 60 candidate / produced goods per market
```

Q4's current broad baseline is:

```txt
C * M * G_market = 800 * 100 * 60 = 4,800,000 logical monthly iterations
```

Q4's ownership-split target is:

```txt
normal:
  C * M prep + P_normal * K_m * G_a
  = 80,000 + 100 * 40 * 10
  = 120,000 logical monthly iterations before trade pass

performance:
  C * M prep + P_performance * K_m * G_a
  = 80,000 + 5 * 40 * 10
  = 82,000 logical monthly iterations before trade pass
```

F7 can remove the market-center ownership workaround, but it does not by itself remove the `C * M` preparation term if country preparation still scans all country-market presence.

F9 targets that `C * M` preparation term.

If F9 replaces broad country-market prep with a location-derived dirty cache, the steady-state shape becomes closer to:

```txt
startup / migration:
  L locations full build

normal month steady state:
  L / 30 daily verification * 30 days = L verification checks per month
  + D_c dirty countries rebuilt
  + D_m dirty markets rebuilt
  + P * K_m * G_a market-local active work
  + C * T_country trade pass
```

Where:

```txt
L   = number of world locations
D_c = countries affected by owner/market drift this month
D_m = markets affected by owner/market drift this month
```

### Conservative interpretation

If the world has a few thousand locations, then `L` may be far smaller than the Q4 broad prep term `C * M = 80,000`.

Example only:

```txt
L = 10,000 locations
rolling verification monthly cost = 10,000 lightweight owner/market checks
old broad prep term = 80,000 country-market prep iterations
```

That would be roughly:

```txt
80,000 -> 10,000
≈ 8x reduction on the preparation/discovery part
```

The total loop-only estimate becomes:

```txt
normal:
  old ownership-split: 80,000 prep + 40,000 local = 120,000
  F7+F9 target:        10,000 verify + 40,000 local = 50,000
  gain vs ownership split: ~2.4x on pre-trade market/country local orchestration
  gain vs broad baseline: 4,800,000 / 50,000 = ~96x

performance:
  old ownership-split: 80,000 prep + 2,000 local = 82,000
  F7+F9 target:        10,000 verify + 2,000 local = 12,000
  gain vs ownership split: ~6.8x on pre-trade market/country local orchestration
  gain vs broad baseline: 4,800,000 / 12,000 = ~400x
```

These numbers are optimistic because a location verification check is not necessarily the same cost as a country-market prep iteration, and trade/engine overhead still exists.

### If `L` is larger

If the game has many more locations, for example:

```txt
L = 30,000
```

then:

```txt
normal:
  F7+F9 target = 30,000 + 40,000 = 70,000
  gain vs 120,000 ownership-split = ~1.7x
  gain vs 4,800,000 broad baseline = ~69x

performance:
  F7+F9 target = 30,000 + 2,000 = 32,000
  gain vs 82,000 ownership-split = ~2.6x
  gain vs 4,800,000 broad baseline = ~150x
```

Still meaningful, especially in Performance Mode where local market work is already small and the prep/discovery term dominates.

### If daily verification must rebuild instead of only mark dirty

If each daily slice fully rebuilds derived market/country caches rather than only detecting drift, the optimisation can collapse.

Bad shape:

```txt
L verification
+ broad dirty rebuilds every month
+ market-local work
```

Good shape:

```txt
L lightweight comparisons
+ small dirty rebuild set
+ market-local work
```

The win depends on keeping the verifier lightweight and making derived-cache rebuilds sparse.

## Practical win estimate

Using Q4's hypothesis, F9 is probably worth it if it replaces most of the `C * M = 80,000` preparation/discovery term with `L` lightweight checks plus sparse dirty rebuilds.

Expected gain range:

```txt
normal mode:
  additional ~1.5x to ~3x over the Q4 ownership-split target
  depending on location count and dirty rebuild density

performance mode:
  additional ~2.5x to ~7x over the Q4 ownership-split target
  because P * K_m * G_a is already small and prep dominates

vs original broad baseline:
  still plausibly ~70x to ~400x loop-count reduction before trade and engine overhead,
  depending on L and P
```

Visible tick-time gain will be smaller if vanilla/engine work or trade-owner handlers dominate the tick.

## Validation metrics

A future F9 probe should measure:

```txt
location_cache_full_build_locations
location_cache_daily_slice_locations_checked
location_cache_daily_slice_drift_owner_count
location_cache_daily_slice_drift_market_count
location_cache_dirty_countries_count
location_cache_dirty_markets_count
location_cache_dirty_country_markets_count
country_capacity_pools_rebuilt_from_dirty
market_participant_caches_rebuilt_from_dirty
country_market_records_initialized_from_dirty
legacy_countries_present_rebuilds_avoided
legacy_country_market_prep_iterations_avoided
```

Compare against Q4 counters:

```txt
country-market prep iterations
promoted/detailed markets processed
countries_present_in_market rebuilds
present-country iterations
active goods considered
heavy goods processed
trade-owner candidates processed
```

## Guardrails

- Do not make a full `every_location_in_the_world` rebuild part of the default monthly hot path unless metrics prove it is cheaper than the scans it replaces.
- Keep daily verifier slices lightweight: compare, mark dirty, update cached source facts.
- Do not rebuild all derived caches inside the daily slice unless the dirty set is small and explicitly bounded.
- Do not rely on event-only accuracy until all relevant owner/market lifecycle hooks are confirmed.
- Do not use runtime-built map names or runtime-built helper names.
- Generate fixed day-slice helpers or use stable ordered iteration only if it is confirmed deterministic.
- Treat location cache as source-of-derivation cache, not stock source of truth.
- Keep central stock operators as the only stock mutation surface.
- Keep a strict audit mode that can compare cache-derived market-country state to actual location links.

## Recommended sequence

```txt
F9.0 Documentation only
  - record this design

F9.1 Startup full-build probe
  - count all locations
  - cache owner and market
  - derive basic market-country / country-market facts in debug mode

F9.2 Owner-change dirty hook
  - use confirmed location-owner change action
  - dirty old/new country and affected market/country-market state

F9.3 Daily rolling verifier probe
  - verify fixed 1/30 slices
  - log drift and dirty counts
  - prove coverage over 30 days

F9.4 Shadow-derived caches
  - keep current live cache path
  - build derived country/market caches in parallel
  - compare with current countries_present_in_market and country-market prep outputs

F9.5 Switch consumers
  - have capacity, promotion, and market-country init consume the derived caches
  - keep strict audit fallback

F9.6 Remove redundant broad prep
  - remove or gate broad country-market discovery loops replaced by the cache
```

## Decision

F9 is a strong future optimisation candidate, but only if implemented as:

```txt
event-driven dirtying
+ rolling 1/30 daily verification
+ sparse dirty rebuilds
+ fixed generated helpers/maps
```

It is probably not worth implementing as:

```txt
monthly full-world location rebuild
+ broad derived-cache rebuild
```

Under Q4 assumptions, F9 is most valuable after F7 and F1 because the global market pass gives the cache a clear market-scope consumer, and F1 gives the capacity pool a clear country-scope consumer.

# ModeU5 Variable-Map Storage Model

## Purpose

This document defines when ModeU5 user stories should use persistent variable maps and how each multidimensional value is represented.

It supplements `AGENTS.md`, `CLAUDE.md`, and TECH-01 exposure `007`. It does not authorize direct stock mutation or bypass any centralized scripted effect.

Engine reference:

```txt
https://eu5.paradoxwikis.com/Variable#Variable_maps
```

The official 1.1 section defines variable maps as associative arrays mapping one key scope to one value scope or number.

## Selection rule

Use a persistent variable map when all of the following are true:

1. The value must survive the current effect or event chain.
2. The value belongs to a stable game-object scope.
3. One remaining dimension can be represented by a stable scope key.
4. The value is state, a durable counter, or an intentional cache.

Use local variables and saved scopes for one resolver call, one stock transaction, intermediate arithmetic, candidate scores, and other temporary data.

Use static definitions or scripted/config values for fixed balance data. Do not copy static configuration into runtime maps without a demonstrated need.

## Map contract

Every map-owning user story must define:

```txt
logical dimensions
logical record and fields
record owner scope
tuple/key
confirmed physical map family
physical value type
default value
write owner
readers
reset/rebuild lifecycle
```

General rules:

- Map names are static identifiers. Do not assume a map name can be built dynamically from an argument or variable.
- A native variable-map entry is one `key -> value` association. The value may be a number or a scope, but the official variable-map documentation does not define inline structs, named fields, or a nested map value.
- Missing numeric entries must have an explicit safe default.
- `add_to_variable_map` does not replace an existing key. Update by reading the old value, removing the key, and re-adding the replacement.
- Preserve or save the key scope before changing scope.
- Clear a map only at its documented lifecycle boundary.
- Aggregate/cache maps are rebuilt from their source-of-truth maps, never the reverse.
- Stock maps are writable only through the centralized stock effects required by `AGENTS.md`.

## Confirmed CORE-01 implementation constraints

Controlled implementation and runtime testing for PR #43 established these
additional rules:

- The logical owner of `market × good` remains the market, but Market scope
  cannot own variables in the tested build. The physical aggregate is a global
  per-good map keyed by market scope.
- A scripted-effect argument may select a generated per-good adapter, but it
  must not contain or forward a map identifier.
- Every generated adapter contains complete literal country-stock, capacity,
  and market-aggregate map identifiers.
- Shared scripted effects own validation, arithmetic, outputs, and diagnostics.
  The generator only expands the versioned adapter template.
- `in_game/common/scripted_effects/modeu5_stock_goods_generated.txt` is generated
  output and must not be edited manually.
- The goods registry used by the generator must stay synchronized with the
  supported vanilla goods set and generation must be idempotent.
- Deliberate cache corruption is allowed only through the centralized
  test-only fault injector used by CORE-01.5/CORE-01.6 tests.

## Logical records and physical map families

ModeU5 should model related fields as one logical record:

```txt
country_market_good_record = {
    stock
    capacity
    produced
    added
    rejected
    overproduction_ratio
    effective_overproduction_ratio
    void_wealth
    production_penalty
}
```

This is domain notation, not a claim that EU5 supports an inline record as one map value.

With currently documented engine exposure, one logical record is represented by a synchronized map family:

```txt
same owner scope
same tuple key
one native map per record field that must persist
centralized helpers enforcing record-level updates
```

A true single-map representation would require the map value to reference a unique persistent scope for each logical record, with the fields stored as variables on that scope. No suitable persistent `country x market x good` record scope or nested-map value is currently confirmed. Track that possible optimization under TECH-01 `088`.

## Canonical representations

### Country x market x good

Logical model:

```txt
country.country_market_good_record[market][good] = {
    stock
    produced
    added
    rejected
    overproduction_ratio
    effective_overproduction_ratio
    void_wealth
    production_penalty
}
```

Confirmed physical model:

```txt
record owner: country
tuple:        market × good
shared key:   market scope
map family:   modeu5_<good>_<field>_by_market
map value:    one numeric field
default:      field-specific, normally 0
```

Variable maps provide one keyed dimension on one owner scope and one value per key. Because no persistent record object is confirmed, the good and field remain encoded in static map names while the market is the shared key.

Goods iteration must call a generated per-good adapter when a physical map name
changes by good or field. The adapter contains complete literal map identifiers
for reading and remove/re-add replacement, then calls a shared arithmetic effect
that receives only temporary values and saved scopes. Map identifiers must not
be forwarded as scripted-effect arguments. Runtime map-name construction is not
assumed.

All maps in the family represent one logical record. They must use the same owner, market key, default rules, and lifecycle. Centralized helpers provide record-level consistency.

This logical record owns:

```txt
country stock
US-00 produced/added/rejected ledger
US-00 ratios, void wealth, and next-month penalty
country/market demand outcomes that cannot live on a more specific consumer scope
```

US-10.3 current-month country × market × good outcome fields are:

```txt
consumption_requested
consumption_satisfied
consumption_unsatisfied
trade_requested
trade_transferred
trade_unsatisfied
```

They are additive current-month counters written by explicit US-10.1/US-10.2
requests. They must not duplicate Pop location records once a more specific
consumer scope is available.

Capacity is deliberately not stored in this per-good record. US-02 capacity is
the same for every good in one country-market relation, so persisting it here
would multiply identical values by the number of goods and repeat the same
monthly work.

### Country x market capacity

Logical model:

```txt
country.country_market_capacity_record[market] = {
    stock_cap
    base_capacity
    building_capacity
    foreign_capacity
}
```

Confirmed physical model:

```txt
record owner: country
tuple:        market
shared key:   market scope
map family:
  modeu5_stock_cap_by_market
  modeu5_base_capacity_by_market
  modeu5_building_capacity_by_market
  modeu5_foreign_capacity_by_market
map value:    one numeric field
default:      0
```

Generated per-good adapters read the shared capacity maps when stock
operations need available capacity. The generated country-market capacity
dispatcher recalculates capacity once through the sentinel `wheat` adapter, not
once per good. Compatibility wrappers for other goods remain callable, but they
write the same shared maps and must not recreate per-good capacity maps.

The value stored in each country-market capacity record combines the current
market's own trade-capacity contribution with the per-market share of one
country-level location pool:

```txt
country_location_pool
= sum(country owned-location rank/capital capacity)

country_market_capacity
= target_market_trade_capacity
  + country_location_pool / count(markets present in country)
```

This keeps the stock-facing data shape as `country x market`, while avoiding
the old monthly hot path that scanned owned locations once per market and once
per good. The country location pool is cached on the country and rebuilt at
campaign start, after owner/rank/capital changes, or during explicit
debug/manual full recalculation. Ordinary monthly refreshes read the cached
pool and write market shares with current market trade capacity.

### Market x good aggregate

Logical model:

```txt
market.stock[good]
```

Physical model:

```txt
owner:    global variable system
map name: modeu5_<good>_market_stock
key:      market scope
value:    numeric
default:  0
```

This is an aggregate/cache rebuilt from country stock maps. Controlled runtime
testing on June 14, 2026 confirmed that Market scope does not support
variables, so the aggregate cannot be stored on the market itself.

### Location x good

Logical model:

```txt
location.pop_demand_record[good] = {
    multiplier
    requested_quantity
    satisfied_quantity
    unsatisfied_quantity
    satisfied_months
    unsatisfied_months
}
```

Physical model:

```txt
record owner: location
tuple:        good
shared key:   goods scope
map family:   one static map per record field
map value:    one numeric field
default:      field-specific
```

This map family represents one logical location × good demand record shared by US-04 and US-10.3.

### Country x market aggregate across goods

Logical model:

```txt
country.metric[market]
```

Physical model:

```txt
owner:    country
map name: one static aggregate map
key:      market scope
value:    numeric
default:  0
```

Examples include a per-market total void-wealth diagnostic. Country-wide totals remain ordinary country variables when no keyed dimension remains.

## Transaction boundary

The following values should normally remain local to the current scripted effect or event chain:

```txt
requested quantity for one operation
remaining quantity
actual added/removed/transferred quantity
rejected or unsatisfied quantity for one operation
candidate score
candidate exclusion reason
stock before/after for one operation
temporary arithmetic
saved country/market/good scopes
```

Persist only the monthly/yearly aggregates explicitly required by US-00, US-04,
US-10.3, debug, or stock-consistency orchestration.

## All-US review

| User story | Map decision | Required improvement |
|---|---|---|
| CORE-01.1 | Writes stock and aggregate maps | Use generated per-good EU5 adapters with literal map reads/writes; keep validation and arithmetic in the shared effect, expose add/reject outputs, and support explicit `enforce` versus authorized `allow_over_capacity` policy without owning ledger persistence. |
| CORE-01.2 | Writes stock and aggregate maps | Reuse the same literal persistence adapters and shared arithmetic contract while keeping requested/removed/unsatisfied values transaction-local. |
| CORE-01.3 | Writes two stock records and up to two aggregates | Calculate the complete transfer before replacement; enforce target capacity by default and allow the explicit CORE-03 lifecycle exception. |
| CORE-01.4 | Writes stock and aggregate maps | Calculate decay from country stock only; keep decay transaction state local. |
| CORE-01.5 | Rebuilds the market aggregate map | Sum country source maps and replace only the selected market key in the global per-good aggregate map. |
| CORE-01.6 | Reads source and aggregate maps | Keep validation state local and delegate every aggregate correction to CORE-01.5. |
| CORE-02 | Initializes capacity and stock maps once | Keep global schema/state as scalars, use shared country x market capacity as the allocation weight, conserve the full opening source, and route writes through CORE-01.1 with `allow_over_capacity`. |
| CORE-03 | Reassigns existing stock ownership after lifecycle events | Read per-good stock plus shared country x market capacity, keep ratios temporary, conserve the full formula-derived transfer, and route movements through CORE-01.3 with `allow_over_capacity`. |
| EPIC US-00 | Owns one logical record | Use the canonical country x market x good record backed by a synchronized map family. |
| US-00.1 | Owns ledger fields | Treat produced/added/rejected as fields of one logical record; update their physical maps through one helper. |
| US-00.2 | Owns ratio fields | Add raw/effective ratios to the same logical record and physical map family. |
| US-00.3 | Owns next-month field | Add the prepared penalty field to the same logical record until N+1 application. |
| US-00.4 | Owns valuation fields and aggregates | Add detailed valuation fields to the logical record; keep market totals and country totals as explicit aggregates. |
| US-10-UI, including folded US-00 visibility | Reads maps and transaction diagnostics | Iterate the same map families without maintaining a UI copy or second authoritative outcome store. |
| US-01 | Owns stock field and aggregate cache | Treat stock as a field of the country x market x good record and retain the separate market x good aggregate map. |
| US-01-UI | Reads maps | Read US-01/US-02 maps directly and remain non-mutating. |
| US-02 | Owns capacity fields | Treat total and optional contribution breakdowns as one shared country x market record, not as duplicated per-good fields. |
| US-02-UI | Reads maps | Read the capacity maps directly; do not recalculate a second UI capacity. |
| US-03 | Inherits US-01 maps | Iterate and mutate stock only through `modeu5_decay_stock`; no separate persistent decay-state map. |
| US-03-UI | Reads transaction output | Keep operation diagnostics temporary unless a monthly aggregate is explicitly required. |
| US-04 | Owns location demand-record fields | Use one logical location x good record backed by maps keyed by goods. |
| US-04-UI | Reads maps | Read US-04 and US-10.3 location maps directly. |
| US-05 | No map needed | Wealth, Trade Income, and Economic Base are country scalars for the calculation. |
| US-05-UI | No map needed | Read US-05 scalar outputs; do not persist a UI copy. |
| US-07 | No runtime map | Keep building balance in static definitions/configuration. |
| US-07-UI | No runtime map | Read static/configured values. |
| US-08 | No runtime map | Keep price changes in static definitions. |
| US-08-UI | No runtime map | Read static price definitions or documented UI output. |
| US-09 | No runtime map | Use the country modifier; no per-country shadow map. |
| US-09-UI | No runtime map | Read the active modifier. |
| EPIC US-10 | Mixed | Use stock and outcome maps, but keep resolver transactions temporary. |
| US-10.0 | No persistent map | Candidate lists, scores, and exclusions are transaction-local unless a debug snapshot is explicitly requested. |
| US-10.1 | Uses stock maps | Keep requested/remaining/satisfied values local; persist only through US-10.3. |
| US-10.2 | Uses stock maps | Keep one transfer transaction local; persist only through US-10.3. |
| US-10.3 | Owns outcome-record fields | Persist current-month country-market-good consumption and trade outcome maps for explicit requests; add Pop outcomes to the shared location x good demand record once live Pop demand exposure is confirmed. |
| US-10-UI | Reads maps and transaction diagnostics | Do not create a second authoritative outcome store. |
| US-11 | Validates/rebuilds maps | Compare country source maps with market aggregate maps and repair only the aggregate. |
| US-13 | No runtime map | Use static CB/wargoal variants and triggers. |

## Review outcome

The main record/map-family improvements are concentrated in US-00, US-01, US-02, US-04, US-10.3, and US-11.

US-03, US-10.0, US-10.1, and US-10.2 should consume those maps but keep transaction state temporary. US-05, US-07, US-08, US-09, and US-13 do not gain useful behavior from runtime maps.

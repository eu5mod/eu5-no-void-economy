# ModeU5 Variable-Map Storage Model

## Purpose

This document defines when ModeU5 user stories should use persistent variable maps and how each multidimensional value is represented.

It supplements `AGENTS.md`, `CLAUDE.md`, and TECH-01 exposure `007`. It does not authorize direct stock mutation or bypass any centralized scripted effect.

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
owner scope
map name
key scope
value type
default value
write owner
readers
reset/rebuild lifecycle
```

General rules:

- Map names are static identifiers. Do not assume a map name can be built dynamically from an argument or variable.
- Missing numeric entries must have an explicit safe default.
- `add_to_variable_map` does not replace an existing key. Update by reading the old value, removing the key, and re-adding the replacement.
- Preserve or save the key scope before changing scope.
- Clear a map only at its documented lifecycle boundary.
- Aggregate/cache maps are rebuilt from their source-of-truth maps, never the reverse.
- Stock maps are writable only through the centralized stock effects required by `AGENTS.md`.

## Canonical representations

### Country x market x good

Logical model:

```txt
country.metric[market][good]
```

Physical model:

```txt
owner:    country
map name: modeu5_<good>_<metric>_by_market
key:      market scope
value:    numeric
default:  0
```

Variable maps provide one keyed dimension on one owner scope. Because no persistent `country x market` object is available, the good remains encoded in a static map name and the market is the map key.

Goods iteration must call generated per-good helpers when the map name changes by good. Runtime map-name construction is not assumed.

This pattern owns:

```txt
country stock
country stock capacity
US-00 produced/added/rejected ledger
US-00 ratios, void wealth, and next-month penalty
country/market demand outcomes that cannot live on a more specific consumer scope
```

### Market x good aggregate

Logical model:

```txt
market.stock[good]
```

Physical model:

```txt
owner:    market
map name: modeu5_market_good_stock
key:      goods scope
value:    numeric
default:  0
```

This is an aggregate/cache rebuilt from country stock maps.

### Location x good

Logical model:

```txt
location.metric[good]
```

Physical model:

```txt
owner:    location
map name: one static map per metric
key:      goods scope
value:    numeric
default:  metric-specific
```

This pattern owns US-04 multipliers and Pop-demand outcome counters consumed by US-04.

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

Persist only the monthly/yearly aggregates explicitly required by US-00, US-04, US-10.3, debug, or reconciliation.

## All-US review

| User story | Map decision | Required improvement |
|---|---|---|
| EPIC US-00 | Owns durable maps | Use the canonical country x market x good ledger family and map lifecycle. |
| US-00.1 | Owns durable maps | Define concrete produced/added/rejected map families and centralized replacement writes. |
| US-00.2 | Owns derived maps | Store raw/effective ratios in per-good maps keyed by market. |
| US-00.3 | Owns next-month state | Store the prepared penalty in a per-good map keyed by market until N+1 application. |
| US-00.4 | Owns detailed and aggregate maps | Keep detailed per-good maps; use one country map keyed by market for market totals and a scalar for country total. |
| US-00-UI | Reads maps | Iterate the same map families without maintaining a UI copy. |
| US-01 | Owns source and cache maps | Use country per-good stock maps keyed by market and a market map keyed by good. |
| US-01-UI | Reads maps | Read US-01/US-02 maps directly and remain non-mutating. |
| US-02 | Owns capacity maps | Store total and optional contribution breakdowns in country per-good maps keyed by market. |
| US-02-UI | Reads maps | Read the capacity maps directly; do not recalculate a second UI capacity. |
| US-03 | Inherits US-01 maps | Iterate and mutate stock only through `modeu5_decay_stock`; no separate persistent decay-state map. |
| US-03-UI | Reads transaction output | Keep operation diagnostics temporary unless a monthly aggregate is explicitly required. |
| US-04 | Owns location maps | Current location-scoped maps keyed by goods are the reference two-dimensional pattern. |
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
| US-10.3 | Owns outcome maps | Use location maps keyed by good for Pops and canonical country/per-good maps keyed by market for broader aggregates. |
| US-10-UI | Reads maps and transaction diagnostics | Do not create a second authoritative outcome store. |
| US-11 | Validates/rebuilds maps | Compare country source maps with market aggregate maps and repair only the aggregate. |
| US-13 | No runtime map | Use static CB/wargoal variants and triggers. |

## Review outcome

The main map improvements are concentrated in US-00, US-01, US-02, US-04, US-10.3, and US-11.

US-03, US-10.0, US-10.1, and US-10.2 should consume those maps but keep transaction state temporary. US-05, US-07, US-08, US-09, and US-13 do not gain useful behavior from runtime maps.

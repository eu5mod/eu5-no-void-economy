# Monthly Country-Market Capacity Stamp

## Status

Implemented in the PR stacked directly on #212 as Layer B of the runtime
performance roadmap.

## Problem

Two monthly callers can reach the same country-market capacity record:

1. current-country preparation iterates every market present in the country;
2. the detailed promoted-market pass iterates every country present in the market.

The country-wide location/rank pool was already monthly cached, but each caller
still recalculated the market-specific merchant contribution and rewrote the
capacity maps.

## Scheduling state

The implementation adds one country-owned variable map keyed by market:

```txt
cbp_capacity_monthly_stamp_by_market[country, market]
  = current_year * 12 + current_month
```

This map is a scheduling guard only. It is not a source of capacity and is never
used in admission arithmetic. The existing capacity maps remain authoritative:

- `cbp_stock_cap_by_market`;
- `cbp_base_capacity_by_market`;
- `cbp_building_capacity_by_market`;
- `cbp_foreign_capacity_by_market`.

## Public monthly entry point

Both monthly callers continue to call:

```txt
cbp_recalculate_country_market_capacity_from_prepared_pool_shared
```

That effect now:

1. calculates the current month stamp;
2. reads the country-owned stamp through `scope:cbp_country`;
3. compares the stored value with the current month;
4. delegates to the raw capacity writer only when the stamp is missing or stale.

A missing entry is loaded as `-1`, avoiding an unset variable-map value read.

## Forced refreshes

Initialization and confirmed topology-change hooks must remain authoritative even
when a record was already calculated earlier in the same month. They therefore
use:

```txt
cbp_recalculate_country_market_capacity_from_prepared_pool_raw_shared
```

The raw path recalculates the capacity maps and overwrites the current-month
stamp. This preserves same-month correctness after:

- location ownership or rank changes;
- capital movement;
- explicit rebuild/initialization flows.

## Work-shape effect

Before:

```txt
current-country preparation -> calculate and write country-market capacity
promoted-market pass         -> calculate and write the same record again
```

After:

```txt
first monthly caller  -> calculate, write, stamp
later monthly caller  -> compare stamp, reuse persisted capacity maps
forced topology hook  -> calculate, write, restamp regardless of current stamp
```

This PR does not remove either caller or change the capacity formula. It removes
duplicate monthly calculation and variable-map writes through one shared gate.

## Static validation

`tools/validate_cbp_capacity_monthly_stamp.py` verifies that:

- the stamp formula is `year * 12 + month`;
- reads and writes use saved country scope and market keying;
- the monthly country pass and promoted-market pass share the idempotent entry;
- the public entry delegates to a raw writer only for stale/missing stamps;
- forced initialization/topology paths bypass the gate and restamp records;
- full capacity recalculation also records the stamp.

The dedicated `Capacity Monthly Stamp` workflow also runs the persistent-state
audit.

## Performance claim

This is a static work-shape optimisation. It is expected to reduce repeated
merchant-capacity calculations and capacity-map writes, but it does not claim a
measured wall-clock improvement. Benchmarking remains Layer C of the roadmap.

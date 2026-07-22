# Sparse US-04 Work Indexes

## Status

This document records the implementation of Layer D from
`FULL_RUNTIME_PERFORMANCE_ANALYSIS.md`:

```text
Build sparse US-04 work indexes.
```

The change modifies work selection only. The generated location-good accounting
continues to own the coefficient arithmetic, central stock mutation, market
supply delta, Estate charge/refund and monthly record.

## Baseline work shape

The previous monthly country pass executed:

```text
every_market_present_in_country
  -> all supported goods
     -> market Pop-demand gate
        -> every_owned_location filtered to that market
```

With 74 supported goods, this repeated broad good and location checks even when
almost every location-good coefficient was neutral and no prior record needed
maintenance.

## Sparse physical model

Each country owns one variable list per supported good:

```text
cbp_<good>_us04_active_locations
```

The list targets location scopes. A location is a member for one good when either
branch is true:

1. `cbp_us04_reconciliation_coefficient[good]` exists and differs from `1`,
   **and** at least one location-good Estate proxy map entry exists;
2. a prior US-04 monthly reconciliation record still exists and must be cleared.

The list is a scheduling index only. Membership cannot authorize an economic
mutation. Before processing an entry, the generated dispatcher rechecks:

- current owner;
- current market;
- market `demands_goods_by_pops` for the selected good;
- coefficient **and** proxy activity;
- the existing runtime-ready and option gates in the country owner;
- the existing per-location business conditions.

## Monthly execution

The monthly country owner now performs:

```text
prepare country sparse index
  -> for each supported good with a country list
     -> every_in_list(active locations)
        -> verify owner
        -> re-read coefficient/proxy/prior-record state
        -> if economically active and market demands the good
             run existing location-good reconciliation
           else
             clear any prior monthly record
        -> refresh membership and prune inactive entries
```

This removes the dense monthly market iterator and the repeated
`every_owned_location` filter from US-04. Compatibility entry points for explicit
country-market and location processing remain generated for tests and manual
repair; they are no longer the normal monthly owner.

## Index lifecycle

### Start and load repair

A global scalar generation is incremented on game start and game load:

```text
cbp_us04_sparse_index_load_generation
```

Each country stores the generation it last rebuilt. On its next monthly or
annual pulse, a missing or stale country generation causes:

```text
clear all country-owned per-good active-location lists
  -> every_owned_location
     -> refresh membership for all supported goods
  -> store current generation
```

This is idempotent: once rebuilt for the current generation, later monthly
pulses do not repeat the dense repair scan.

### Yearly verifier

The existing yearly business traversal remains dense because it must read and
reset annual counters for every location-good. The implementation clears the
country lists first, then each generated annual adjustment refreshes membership.
The yearly pulse therefore doubles as a complete sparse-index verifier/rebuild
without adding a second location traversal.

### Writer contract

Generated annual coefficient writes refresh the corresponding good immediately
through the all-goods annual wrapper. The loaded Estate-proxy writers and reset
surfaces also refresh the corresponding good immediately. Any additional external
coefficient or Estate-proxy writer must call:

```text
cbp_us04_refresh_sparse_index_for_location = { location = <location> }
```

Monthly record processing refreshes membership after clearing/storing, so an
entry remains only while the coefficient-and-proxy branch or the prior-record branch is true.

### Ownership-change repair

The confirmed `on_location_changed_owner` surface performs both repairs:

```text
loser country
  -> remove transferred location from every per-good list

winner country
  -> evaluate the transferred location for every supported good
```

The normal monthly dispatcher also verifies that every indexed location is
still owned by the list-owning country and removes stale entries defensively.

## Economic invariants retained

- Base US-10 consumption remains separate and completes before US-04.
- US-04 still applies only the signed coefficient delta.
- Missing coefficient state remains neutral at `1`.
- No synthetic or fixed Estate fallback is introduced.
- Positive deltas use `cbp_remove_stock` and actual removed quantity.
- Negative deltas use `cbp_add_stock` and actual restored quantity.
- Estate charge/refund allocation uses the existing per-location proxy shares.
- Monthly records are cleared before replacement.
- Audit reconciliation remains after US-04.
- Performance Mode does not change whether the business rule applies.

## Static validation

`tools/validate_cbp_us04_sparse_indexes.py` verifies:

- the monthly country owner calls the sparse dispatcher and contains no dense
  market/location traversal;
- start/load generation repair exists;
- yearly complete verification remains;
- owner-change removal and re-evaluation are wired;
- one generated per-good list and processor exists for every canonical good;
- coefficient, proxy and prior-record conditions all contribute to membership;
- the generated processor retains the market Pop-demand gate and prior-record
  clearing path;
- central stock and Estate mutation surfaces remain in the existing template;
- the persistent-state audit classifies the new lists as work caches.

## Performance claim

This is a static work-shape optimization. In sparse scenarios, expected monthly
work changes from roughly:

```text
country markets x all goods x owned-location filters
```

to:

```text
supported goods x indexed active locations
```

No wall-clock improvement is claimed without the controlled benchmark matrix
specified by the parent analysis. Exact stock, supply, Estate and annual-counter
equivalence still requires in-game comparison against the #212 baseline.

# US-04 final probe lessons and reconciliation pivot — 2026-07-11

## Summary

Runtime probes on PR #69 showed that EU5 1.2+ does not provide a reliable
script path to update engine `pop_demand × good` dynamically during a campaign.

ModeU5 must therefore stop treating `pop_demand` injection/replacement as a
production implementation path. The probes remain useful historical evidence,
but US-04 gameplay now uses a ModeU5-owned reconciliation coefficient and a
stock/cost proxy.

## Probe conclusions

### Confirmed

- Location × good annual counters are viable ModeU5 state.
- The annual arithmetic is viable:
  - full satisfaction: `coefficient × 1.01`;
  - full shortage: `coefficient × 0.99`;
  - mixed or empty year: unchanged.
- Versioned one-time initialization is required so the `1.20` baseline is not
  repeatedly applied after reloads.
- Missing state must fail closed to vanilla-equivalent `1.00`.

### Rejected for production

- Exact-path regeneration or copying of vanilla `pop_demands.txt`.
- Runtime `INJECT:pop_demand` as a gameplay dependency.
- Runtime `REPLACE:pop_demand` as a gameplay dependency.
- Any claim that ModeU5 can update engine `pop_demand × good` after campaign
  start on EU5 1.2+.

### Still unconfirmed

- Reading exact live Pop/Estate requested demand per estate and good.
- Charging a specific estate through a confirmed script effect.
- Applying a dynamic local `good × Pop demand` modifier upstream of vanilla
  consumption.

## New temporary architecture

US-04 keeps two coefficients on location × good:

```txt
modeu5_pop_demand_multiplier[goods:<good>]
```

Legacy archived coefficient used by the failed vanilla-injection path. It is
still initialized and updated so old probes remain interpretable, but gameplay
must not depend on the engine reading it.

```txt
modeu5_us04_reconciliation_coefficient[goods:<good>]
```

Active ModeU5 reconciliation coefficient. It starts at `1.20` and receives the
same yearly `× 1.01 / × 1.00 / × 0.99` updates.

Monthly reconciliation then reads the US-10.3 Pop requested quantity recorded
for the location and good:

```txt
modeu5_pop_demand_requested_quantity[goods:<good>]
```

The temporary extra demand is:

```txt
extra_quantity = requested_quantity × max(0, reconciliation_coefficient - 1)
```

That quantity is removed through the centralized stock operator:

```txt
modeu5_remove_stock(reason = consumption)
```

This single call updates both country × market × good stock and the market ×
good aggregate/cache, preserving the ModeU5 stock invariant. The active US-04
runtime also records country-stock and market-aggregate deltas so the debug
fixture proves both levels were reduced without depending on a later audit or
rebuild.

## Estate charge

`add_gold_to_estate` is confirmed from country scope and the active US-04
runtime uses it with a negative value:

```txt
add_gold_to_estate = {
    estate_type = estate_type:peasants_estate
    value = -(actual_removed_quantity × market_price(goods:<good>))
}
```

The positive charge amount is persisted on the location × good reconciliation
record as `modeu5_us04_reconciliation_estate_charge`. The temporary target is
`peasants_estate` because the current US-10.3 record is aggregated as
`location × good`, not yet `location × estate × good`.

## Candidate future estate allocation rule

The likely functional target is to allocate the reconciliation charge among the
Pops or Estates that actually generated local demand.

The business intuition is sound:

```txt
Pop = estate + culture + religion + location
```

If EU5 exposes a script-safe Pop or estate-demand iterator, ModeU5 can distribute
the monthly estate charge proportionally:

```txt
estate_share =
  estate_current_good_demand_in_location
  / sum(all estate current good demand in location)

estate_charge =
  total_location_good_estate_charge × estate_share
```

This must remain future work until the demand-allocation surface is confirmed:

- read current requested demand by estate × location × good;
- split the current temporary `peasants_estate` charge into the exact consuming
  estate targets.

Until then, the implementation deliberately keeps one location × good charge
record and does not claim exact estate allocation.

## Consequence

This is an explicit temporary reconciliation model:

- it does not modify vanilla demand upstream;
- it consumes extra ModeU5 stock after US-10.3 has recorded demand;
- it keeps the yearly adaptation behavior alive;
- it remains compatible with a future engine endpoint for dynamic local
  `good × Pop demand` if Tinto exposes one.

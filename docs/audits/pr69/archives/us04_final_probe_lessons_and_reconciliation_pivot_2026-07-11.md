# US-04 final probe lessons and reconciliation pivot — 2026-07-11

## Summary

Runtime probes on PR #69 showed that EU5 1.2+ does not provide a reliable
script path to update engine `pop_demand × good` dynamically during a campaign.

ModeU5 must therefore stop treating `pop_demand` injection/replacement as a
production implementation path. The probes remain useful historical evidence,
but US-04 gameplay now uses a ModeU5-owned reconciliation coefficient only.
Stock and estate reconciliation are blocked until exact live Pop demand by good
is confirmed.

Current source of truth:

```txt
docs/audits/pr69/Q5_flux_logique_global.v3.md
```

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
- Applying a dynamic local `good × Pop demand` modifier upstream of vanilla
  consumption.

## Current architecture

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
same yearly `× 1.01 / × 1.00 / × 0.99` updates. Monthly reconciliation can
calculate a diagnostic extra demand:

```txt
extra_quantity = requested_quantity × max(0, reconciliation_coefficient - 1)
```

While TECH-01 147 is unconfirmed, that diagnostic extra demand is not removed
from stock and is not charged to estates. The blocked runtime records zero stock
deltas and zero estate charge.

## Estate charge

`add_gold_to_estate` is confirmed from country scope, but the active US-04
runtime does not use it yet. When a future confirmed Pop-demand reader provides
estate-specific requested demand, the charge should be split proportionally:

```txt
estate_charge =
  actual_removed_quantity
  × market_price(goods:<good>)
  × estate_requested_quantity / total_estate_requested_quantity
```

The positive charge amount can then be persisted on the location × good
reconciliation record as `modeu5_us04_reconciliation_estate_charge`.
Per-estate diagnostics can be persisted as
`modeu5_us04_reconciliation_estate_charge_<estate>`.

Until a direct live `every_pop -> pop_demand × good` read is confirmed, US-04
must not invent an estate target or rely on a fixed estate-map bridge as a
production rule. The previous `peasants_estate` fallback is rejected as a
business rule. The runtime now fails closed for that location/good, logs
`direct_pop_demand_read_not_confirmed`, and performs no stock removal or estate
charge.

## Estate allocation rule

The likely functional target is to allocate the reconciliation charge among the
Pops or Estates that actually generated local demand.

The business intuition is sound:

```txt
Pop = estate + culture + religion + location
```

Once the direct demand surface is confirmed, ModeU5 can distribute the monthly
estate charge proportionally:

```txt
estate_share =
  estate_current_good_demand_in_location
  / sum(all estate current good demand in location)

estate_charge =
  total_location_good_estate_charge × estate_share
```

The remaining future work is the direct vanilla demand-allocation surface:

- confirm a direct live `every_pop -> pop_demand × good` read expression;
- in the Pop loop, sum requested demand by `estate_type`;
- after the loop, consume stock once and charge estates proportionally.

PR #69 proved Pop-to-location ModeU5 endpoint access and market-level observed
demand paths. It did not promote direct vanilla `pop -> pop_demand × good`
syntax in TECH-01.

## Consequence

This is an explicit blocked reconciliation model:

- it does not modify vanilla demand upstream;
- it does not consume extra ModeU5 stock until TECH-01 147 is confirmed;
- it does not charge estates until TECH-01 147 is confirmed;
- it keeps the yearly adaptation behavior alive;
- it remains compatible with a future engine endpoint for dynamic local
  `good × Pop demand` if Tinto exposes one.

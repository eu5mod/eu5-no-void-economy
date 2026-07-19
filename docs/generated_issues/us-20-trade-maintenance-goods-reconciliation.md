# US-20 — Selling-efficiency route-loss coefficient

## Functional objective

US-20 models goods physically lost in transit. Merchant Maintenance remains on
the native path. The loss is proportional to trade volume and uses the same
persisted country coefficient as US-17.

```txt
Q = trade_volume
C = var:cbp_us20_route_loss_coefficient

goods_loss_quantity = Q * C

target_goods_amount_received =
    max(Q - goods_loss_quantity, 0)
```

## Coefficient ownership

US-20 does not calculate `C` per route.

The country refresh reconstructs the non-CBP Selling baseline and calculates:

```txt
S   = reconstructed non-CBP Selling Efficiency
L_s = define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_MAX
K_s = define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_CURVE

coefficient_result =
    L_s / (1 + S * K_s)
```

It persists the result before calculating the US-17 Selling correction:

```txt
var:cbp_us20_route_loss_coefficient = coefficient_result
```

US-17 reads that variable:

```txt
Selling correction =
    -S - var:cbp_us20_route_loss_coefficient
```

US-20 later reads the same variable:

```txt
cbp_us20_route_loss_coefficient_input =
    var:cbp_us20_route_loss_coefficient
```

The US-20 route block contains no Selling-efficiency read, Selling-baseline read,
route-loss define lookup, denominator, or division.

## Units and examples

The persisted coefficient is dimensionless. With the default maximum of `0.05`,
a country with zero Selling Efficiency loses 5% of the moved quantity.

```txt
C = 0.05
Q = 10  -> goods_loss_quantity = 0.50
Q = 100 -> goods_loss_quantity = 5.00
```

For `S = 0.10` and curve `10`:

```txt
coefficient_result =
    0.05 / (1 + 0.10 * 10)
  = 0.025

var:cbp_us20_route_loss_coefficient = 0.025
Q = 10
goods_loss_quantity = 10 * 0.025 = 0.25
target_received = 9.75
```

Higher Selling Efficiency reduces the coefficient. The denominator safety floor
of `0.01` belongs to the upstream country calculation, not to US-20 route logic.

## Goods-side reconciliation

The captured native route quantity is treated as both the sent quantity and the
engine receipt baseline for the current MVP:

```txt
goods_amount_sent            = trade_volume
engine_goods_amount_received = trade_volume
```

Only the difference against the engine receipt is applied:

```txt
goods_reconciliation_delta =
    target_goods_amount_received
  - engine_goods_amount_received
```

When negative:

```txt
goods_loss_quantity = -goods_reconciliation_delta
```

The loss is not a transfer. US-20 separates:

```txt
base goods movement:
  add at destination, or transfer country-market to country-market

loss reconciliation:
  remove the proportional delivery loss at destination
```

## Destination accounting

The negative market-supply delta is applied through the central stock helper:

```txt
market_goods_supply_delta = -goods_loss_quantity

cbp_apply_vanilla_market_goods_supply_delta_from_saved_good = {
  cbp_vanilla_market_goods_supply_market = scope:target_market
  cbp_vanilla_market_goods_supply_good   = scope:route_good
  cbp_vanilla_market_goods_supply_delta  = market_goods_supply_delta
}
```

The central helper owns the actual market-scope `add_goods_supply` call.

## Four-case market-accounting matrix

```txt
1. origin non-promoted + destination non-promoted
   - remove loss from destination market supply

2. origin promoted + destination non-promoted
   - remove loss from destination market supply

3. origin non-promoted + destination promoted
   - add base receipt to selected destination country stock
   - remove loss from destination market supply
   - remove loss from selected destination country stock

4. origin promoted + destination promoted
   - transfer base receipt between country-market stocks
   - remove loss from destination market supply
   - remove loss from selected destination country stock
```

Destination promotion decides whether a detailed receiver country can be used.
Origin promotion decides whether the detailed base receipt is an add or transfer.

## Receiver-country selection

Selection order remains:

```txt
1. explicitly stored receiving country, when capacity eligible;
2. trade owner, when present in the destination market and capacity eligible;
3. deterministic market-country candidate ordering, filtered by capacity.
```

Receiver eligibility remains:

```txt
current_stock < capacity
```

The receipt is not clipped to remaining capacity for MVP. If no receiver is
available, only the country-stock portion is blocked; the market-level loss still
runs when the target market and good are available.

## Runtime placement

```txt
cbp_run_monthly_country_trade_owner_cycle
  -> reconstruct non-CBP country efficiencies
  -> calculate coefficient_result once
  -> persist var:cbp_us20_route_loss_coefficient
  -> calculate US-17 corrections from the persisted variable
  -> persist US-17 corrections and baselines
  -> every_trade
     -> capture native trade_volume
     -> US-17 route compatibility hook returns zero money delta
     -> owner country: cbp_run_us20_route_loss_reconciliation
        -> read var:cbp_us20_route_loss_coefficient
        -> goods_loss_quantity = trade_volume * coefficient
        -> apply destination goods reconciliation
```

US-20 must not add another route-discovery loop and must not run inside the
market-local `every_market_in_world` body.

## State and transaction fields

Persistent country input:

```txt
cbp_us20_route_loss_coefficient
```

Transaction-local fields:

```txt
cbp_us20_route_loss_coefficient_input
gui_cbp_us20_goods_amount_sent
gui_cbp_us20_engine_goods_amount_received
gui_cbp_us20_goods_received_loss
gui_cbp_us20_target_goods_amount_received
gui_cbp_us20_goods_reconciliation_delta
gui_cbp_us20_goods_loss_quantity
gui_cbp_us20_market_goods_supply_delta
cbp_us20_origin_market_is_promoted
cbp_us20_target_market_is_promoted
cbp_us20_goods_loss_target_country
```

Persistent route-level state remains unnecessary.

## Acceptance contract

```txt
- the coefficient is calculated once by the country refresh;
- the coefficient is persisted before the US-17 Selling correction;
- US-17 Selling reads the persisted coefficient;
- US-20 reads the exact same persisted coefficient;
- US-20 never recalculates the coefficient;
- goods_loss_quantity = trade_volume * coefficient;
- the coefficient is dimensionless;
- the removed quantity is proportional to trade volume;
- Merchant Maintenance is not an input;
- Import/Export compensation defines do not alter physical route loss;
- target receipt has a zero floor;
- only the delta against the engine receipt is applied;
- market loss uses the central vanilla market-supply helper;
- promoted destinations also reconcile the selected receiver country stock;
- receiver selection and four-case accounting remain unchanged;
- no second every_trade discovery loop is introduced.
```

## Focused validation

```txt
Selling baseline = 0.10
coefficient_result = 0.025
persisted coefficient = 0.025
trade_volume = 10
goods_loss_quantity = 0.25
target_received = 9.75

coefficient_calculated_upstream = verified
US-17 coefficient input = persisted coefficient
US-20 coefficient input = persisted coefficient
US-20 reciprocal recalculation = absent
maintenance_input = ignored
route_money_delta = 0
market_goods_supply_delta = -0.25
```

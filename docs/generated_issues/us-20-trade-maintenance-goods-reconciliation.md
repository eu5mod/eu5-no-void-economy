# US-20 — Separate Selling-driven route-loss coefficient

## Functional objective

US-20 models goods physically lost in transit. It is separate from the US-17
Merchant Maintenance formula.

```txt
Q = trade_volume
C = var:cbp_us20_route_loss_coefficient

goods_loss_quantity = Q * C

target_goods_amount_received =
    max(Q - goods_loss_quantity, 0)
```

## Coefficient ownership

US-20 does not calculate `C` per route. The country refresh reconstructs native
Selling Efficiency and calculates once:

```txt
S   = reconstructed non-CBP Selling Efficiency
L_s = CBP_ROUTE_LOSS_COEFFICIENT_MAX
K_s = CBP_ROUTE_LOSS_COEFFICIENT_CURVE

coefficient_result =
    L_s / (1 + S*K_s)
```

The result is persisted before `every_trade`:

```txt
var:cbp_us20_route_loss_coefficient = coefficient_result
```

US-17 does not consume this variable and does not apply it to Selling Efficiency.
The US-20 route block only reads the persisted value.

## Units and example

The coefficient is dimensionless. With the default maximum `0.05`, zero Selling
Efficiency produces a maximum 5% physical loss.

For `S = 0.10`:

```txt
C = 0.05 / (1 + 0.10*10)
  = 0.025

Q = 10
goods_loss_quantity = 10*0.025 = 0.25
target_received = 9.75
```

## Route calculation boundary

The route block contains no:

```txt
modifier:selling_efficiency
Selling baseline read
CBP_ROUTE_LOSS_COEFFICIENT_MAX
CBP_ROUTE_LOSS_COEFFICIENT_CURVE
denominator calculation
division
```

It performs only:

```txt
coefficient_input = var:cbp_us20_route_loss_coefficient
goods_loss_quantity = trade_volume * coefficient_input
```

## Goods-side reconciliation

The captured native route quantity is treated as both sent quantity and engine
receipt baseline for the current MVP:

```txt
goods_amount_sent            = trade_volume
engine_goods_amount_received = trade_volume
```

Only the delta against the engine receipt is applied:

```txt
goods_reconciliation_delta =
    target_goods_amount_received
  - engine_goods_amount_received
```

The negative market-supply delta continues through the central stock helper. For
promoted destinations, the selected receiver-country stock is reconciled as well.
Receiver selection and the four-case promoted/non-promoted accounting matrix are
unchanged.

## Runtime placement

```txt
cbp_run_monthly_country_trade_owner_cycle
  -> reconstruct country baselines
  -> calculate and persist US-20 coefficient once
  -> calculate independent US-17 maintenance corrections
  -> every_trade
     -> capture native trade_volume
     -> US-17 compatibility hook returns zero money delta
     -> cbp_run_us20_route_loss_reconciliation
        -> read persisted coefficient
        -> goods loss = trade_volume * coefficient
        -> apply destination reconciliation
```

US-20 must not add another route-discovery loop and must not run inside the
market-local world loop.

## State

Persistent country input:

```txt
cbp_us20_route_loss_coefficient
```

No persistent route-level state is required.

## Acceptance contract

```txt
- the coefficient is calculated once by the country refresh;
- US-20 reads the persisted country variable;
- US-20 never recalculates the coefficient per route;
- goods_loss_quantity = trade_volume * coefficient;
- target receipt has a zero floor;
- US-17 Selling Efficiency is independent of the coefficient;
- Merchant Maintenance is not an input to US-20;
- market and receiver-country reconciliation remain centralized;
- no second every_trade discovery loop is introduced.
```

## Focused validation

```txt
Selling baseline = 0.10
coefficient_result = 0.025
trade_volume = 10
goods_loss_quantity = 0.25
target_received = 9.75

us20_coefficient = separate
route_money_delta = 0
market_goods_supply_delta = -0.25
```

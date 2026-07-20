# US-20 — Shared Selling route-loss coefficient

## Functional objective

US-20 models physical goods lost in transit. It does not calculate its coefficient per route.

The country refresh calculates the Selling coefficient once from named script values:

```txt
S = reconstructed non-CBP Selling Efficiency

C = cbp_us17_us20_route_loss_coefficient_max
    / (1 + S * cbp_us17_us20_route_loss_coefficient_curve)
```

Default values are `0.05` and `10`. These are mod-owned named script values, not custom engine Defines.

It persists the result immediately:

```txt
var:cbp_us20_route_loss_coefficient = C
```

## Shared use with US-17

US-17 uses the persisted coefficient for Selling:

```txt
Selling correction = -S - C
effective Selling Efficiency = -C
```

US-20 later reads the same country variable:

```txt
coefficient_input = var:cbp_us20_route_loss_coefficient
```

The route block contains no Selling modifier read, Selling baseline read, script-value lookup, denominator calculation, or division.

## Goods loss

```txt
Q = trade_volume
C = coefficient_input

goods_loss_quantity = Q * C
target_goods_amount_received = max(Q - goods_loss_quantity, 0)
```

The coefficient is dimensionless. For example:

```txt
S = 0.10
C = 0.05 / (1 + 0.10*10) = 0.025
Q = 10

goods_loss_quantity = 10 * 0.025 = 0.25
target received = 9.75
```

## Separation from Merchant Maintenance

US-17 also redirects Import and Export Efficiency into Merchant Maintenance using:

```txt
-M + 1 - 1 / (1 + M/2 + 5*(I + Ex))
```

That maintenance formula does not change US-20 physical loss. US-20 continues to use only the persisted Selling coefficient `C`.

## Goods-side reconciliation

The captured route quantity is used as both sent quantity and engine receipt baseline:

```txt
goods_amount_sent = trade_volume
engine_goods_amount_received = trade_volume
```

Only the difference against the target receipt is applied:

```txt
goods_reconciliation_delta =
    target_goods_amount_received
  - engine_goods_amount_received
```

The negative destination market-supply delta is applied through the central stock helper. Promoted destinations also reconcile the selected receiver country stock.

## Runtime placement

```txt
cbp_run_monthly_country_trade_owner_cycle
  -> reconstruct country baselines
  -> calculate C once from named script values
  -> persist C
  -> calculate US-17 corrections
  -> every_trade
     -> capture trade_volume
     -> zero-delta US-17 compatibility hook
     -> US-20 reads C
     -> goods_loss_quantity = trade_volume * C
     -> centralized destination reconciliation
```

## Acceptance contract

```txt
- mod-owned constants are named script values, not custom engine Defines;
- coefficient is calculated once by the country refresh;
- coefficient is persisted before US-17 Selling consumes it;
- US-17 effective Selling equals -C;
- US-20 reads exactly the same persisted C;
- US-20 never recalculates C;
- goods_loss_quantity equals trade_volume * C;
- target receipt has a zero floor;
- no route-level money mutation is applied;
- Merchant Maintenance is not an input to physical goods loss;
- no second every_trade discovery loop is introduced.
```

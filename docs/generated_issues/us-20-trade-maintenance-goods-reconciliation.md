# US-20 — Shared Selling route-loss coefficient

## Functional objective

US-20 models physical goods lost in transit. It does not calculate its coefficient
per route.

```txt
Q = trade_volume
C = var:cbp_us20_route_loss_coefficient

goods_loss_quantity = Q * C
target_received = max(Q - goods_loss_quantity, 0)
```

## Shared coefficient ownership

The country refresh reconstructs non-CBP Selling Efficiency and calculates once:

```txt
C = CBP_ROUTE_LOSS_COEFFICIENT_MAX
    / (1 + S * CBP_ROUTE_LOSS_COEFFICIENT_CURVE)
```

It persists:

```txt
var:cbp_us20_route_loss_coefficient = C
```

The same variable is consumed by US-17:

```txt
effective Selling Efficiency = -C
```

and by US-20:

```txt
goods_loss_quantity = trade_volume * C
```

US-20 contains no Selling read, Selling-baseline read, Define lookup, denominator,
or division inside the route calculation.

## Separation from Trade Maintenance

Import and Export Efficiency are removed from price formation and transferred to
Merchant Maintenance through US-17's exact 50/50 maintenance-cost rule.

They do not change US-20's physical route-loss coefficient. Merchant Maintenance
is not an input to US-20.

## Example

```txt
S = 0.10
C = 0.05 / (1 + 0.10*10) = 0.025
trade_volume = 10
goods_loss_quantity = 0.25
target_received = 9.75
```

## Runtime order

```txt
country refresh
  -> calculate C once
  -> persist C
  -> calculate US-17 corrections
  -> every_trade
     -> US-20 reads C
     -> goods_loss_quantity = trade_volume * C
     -> apply destination reconciliation
```

The four-case destination-accounting matrix, receiver selection, central market
supply helper and promoted-country stock reconciliation remain unchanged.

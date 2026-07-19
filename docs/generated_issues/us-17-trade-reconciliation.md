# US-17 — Shared Selling coefficient and reciprocal Trade Maintenance

## Business rule

Definitions:

```txt
S  = reconstructed non-CBP Selling Efficiency
I  = reconstructed non-CBP Import Efficiency
Ex = reconstructed non-CBP Export Efficiency
M  = reconstructed non-CBP Merchant Maintenance Efficiency

L_s = CBP_ROUTE_LOSS_COEFFICIENT_MAX
K_s = CBP_ROUTE_LOSS_COEFFICIENT_CURVE
K_m = CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE
W   = CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT
```

Default values:

```txt
L_s = 0.05
K_s = 10
K_m = 10
W   = 0.5
```

## Shared Selling coefficient

The Selling curve is calculated once per country:

```txt
C = L_s / (1 + S * K_s)
```

The result is persisted immediately:

```txt
var:cbp_us20_route_loss_coefficient = C
```

US-17 consumes that persisted value:

```txt
Selling correction = -S - C
effective Selling Efficiency = -C
```

US-20 consumes the same value:

```txt
goods loss = trade_volume * C
```

The Selling correction does not recalculate the curve.

## Import and Export leave price formation

```txt
Import correction = -I
Export correction = -Ex

effective Import Efficiency = 0
effective Export Efficiency = 0
```

There are no residual Import or Export price curves.

## Exact Merchant Maintenance formula

The requested correction is:

```txt
Merchant Maintenance correction =
    -M
    + 1
    - 1 / (1 + M/2 + 5*(I + Ex))
```

The production form uses the Defines:

```txt
maintenance denominator =
    1
    + M * W
    + (I + Ex) * K_m * W

effective Merchant Maintenance Efficiency =
    1 - 1 / maintenance denominator

Merchant Maintenance correction =
    effective Merchant Maintenance Efficiency - M
```

With `W = 0.5` and `K_m = 10`, this is exactly:

```txt
-M + 1 - 1 / (1 + M/2 + 5*(I + Ex))
```

This is one mixed denominator. It is not an average of two separately calculated maintenance costs.

## Arithmetic fixture

```txt
S  = 0.10
I  = 0.20
Ex = 0.30
M  = 0.08
trade_volume = 10
```

Selling and US-20:

```txt
C = 0.05 / (1 + 0.10*10) = 0.025
effective Selling = -0.025
goods loss = 10 * 0.025 = 0.25
target received = 9.75
```

Merchant Maintenance:

```txt
M/2 = 0.04
5*(I + Ex) = 2.50

denominator = 1 + 0.04 + 2.50 = 3.54
reciprocal = 1 / 3.54 = 0.282486

effective maintenance = 1 - 0.282486 = 0.717514
maintenance correction = 0.717514 - 0.08 = 0.637514
```

## Runtime order

```txt
country refresh
  -> reconstruct S, I, Ex and M
  -> calculate C once
  -> persist C
  -> calculate Selling, Import, Export and Maintenance corrections
  -> persist four corrections and four baselines
  -> every_trade
     -> zero-delta US-17 compatibility hook
     -> US-20 reads C
     -> goods loss = trade_volume * C
```

State version is `7`.

## Acceptance contract

```txt
- Selling coefficient is calculated once and persisted before US-17 consumes it;
- effective Selling Efficiency equals -C;
- US-20 goods loss equals trade_volume * C;
- effective Import and Export Efficiency equal zero;
- effective Merchant Maintenance Efficiency equals 1 - 1/(1 + M/2 + 5*(I+Ex));
- Merchant Maintenance correction equals -M plus that effective value;
- no route-level add_gold mutation is applied;
- repeated refresh reconstructs all four baselines without drift.
```

## Focused probe

```txt
event cbp_us17_owner_modifiers.1
```

Wait one in-game day. Expected marker includes:

```txt
selling_shared_coefficient=verified
mixed_denominator_formula=verified
import_export_price_effect=zero
route_money_delta=zero
proportional_goods_loss=verified
idempotence=passed
live_auto_modifier_application=passed
```

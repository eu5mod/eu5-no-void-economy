# US-17 — Shared Selling coefficient and 50/50 Trade Maintenance

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
```

## Selling rule remains unchanged

The Selling curve is calculated once per country:

```txt
coefficient_result =
    L_s / (1 + S * K_s)
```

The result is persisted immediately:

```txt
var:cbp_us20_route_loss_coefficient = coefficient_result
```

The country variable remains the single source of truth for US-17 Selling and
US-20 physical goods loss.

US-17 consumes it as:

```txt
Selling correction =
    -S - var:cbp_us20_route_loss_coefficient

effective Selling Efficiency =
    -var:cbp_us20_route_loss_coefficient
```

## Import and Export leave price formation

```txt
Import correction = -I
Export correction = -Ex

effective Import Efficiency = 0
effective Export Efficiency = 0
```

There are no residual Import or Export price curves.

## Exact 50/50 maintenance-cost rule

The final Merchant Maintenance cost is split between two independent halves:

```txt
final maintenance cost =
    50% * Vanilla maintenance cost
  + 50% * Import+Export maintenance cost
```

The two maintenance factors are:

```txt
Vanilla factor = 1 - M
Directional factor = 1 / (1 + (I + Ex) * K_m)
```

Therefore:

```txt
final maintenance factor =
    0.5 * (1 - M)
  + 0.5 / (1 + (I + Ex) * K_m)
```

Expressed through the native Merchant Maintenance Efficiency surface:

```txt
effective Merchant Maintenance Efficiency =
    0.5 * M
  + 0.5 * (1 - 1 / (1 + (I + Ex) * K_m))

Merchant Maintenance correction =
    effective Merchant Maintenance Efficiency - M
```

This is not the rejected mixed-denominator formula
`1 - 1 / (1 + M/2 + (I + Ex)*5)`.

## Runtime placement

```txt
country refresh
  -> reconstruct S, I, Ex and M
  -> calculate Selling coefficient once
  -> persist cbp_us20_route_loss_coefficient
  -> calculate Selling, Import, Export and Maintenance corrections
  -> persist four corrections and four baselines
  -> every_trade
     -> zero-delta US-17 compatibility hook
     -> US-20 reads the persisted coefficient
```

State version is `7`.

## Fixture

```txt
S  = 0.10
I  = 0.20
Ex = 0.30
M  = 0.08
K_m = 10
```

Expected:

```txt
Selling coefficient = 0.025
effective Selling = -0.025
effective Import = 0
effective Export = 0

directional denominator = 1 + (0.20 + 0.30)*10 = 6
directional efficiency = 1 - 1/6 = 0.833333

effective maintenance =
    0.5*0.08 + 0.5*0.833333
  = 0.456667

maintenance correction = 0.456667 - 0.08 = 0.376667
```

## Focused probe

```txt
event cbp_us17_owner_modifiers.1
```

Expected final marker includes:

```txt
selling_shared_coefficient=verified
maintenance_cost_split=50_50
import_export_price_effect=zero
route_money_delta=zero
proportional_goods_loss=verified
idempotence=passed
live_auto_modifier_application=passed
```
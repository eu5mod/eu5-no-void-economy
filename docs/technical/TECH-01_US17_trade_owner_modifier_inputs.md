# TECH-01 — US-17 shared Selling coefficient and reciprocal maintenance inputs

## Confirmed engine surfaces

| Business input | EU5 exposure | Scope | Status |
|---|---|---|---|
| Selling Efficiency | `modifier:selling_efficiency` | country | Confirmed |
| Import Efficiency | `modifier:import_efficiency` | country | Confirmed |
| Export Efficiency | `modifier:export_efficiency` | country | Confirmed |
| Merchant Maintenance Efficiency | `modifier:merchant_maintenance_efficiency` | country | Confirmed |
| Native moved-goods quantity | `trade_volume` | trade | Confirmed |

The tested build rejects `modifier:buying_efficiency` and `modifier:merchant_maintenance_cost`.

## Shared Selling coefficient

```txt
S = reconstructed non-CBP Selling Efficiency
L_s = CBP_ROUTE_LOSS_COEFFICIENT_MAX
K_s = CBP_ROUTE_LOSS_COEFFICIENT_CURVE

C = L_s / (1 + S * K_s)
```

The country refresh persists:

```txt
var:cbp_us20_route_loss_coefficient = C
```

US-17 consumes the persisted value:

```txt
Selling correction = -S - C
effective Selling Efficiency = -C
```

US-20 consumes the same value:

```txt
goods loss = trade_volume * C
```

The strict runtime order is:

```txt
calculate C -> persist C -> calculate US-17 corrections -> every_trade reads C
```

## Directional price cancellation

```txt
Import correction = -I
Export correction = -Ex

effective Import Efficiency = 0
effective Export Efficiency = 0
```

No Import or Export reciprocal residual remains on the price surfaces.

## Merchant Maintenance formula

Let:

```txt
M = reconstructed non-CBP Merchant Maintenance Efficiency
I = reconstructed non-CBP Import Efficiency
Ex = reconstructed non-CBP Export Efficiency
W = CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT
K = CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE
```

Production calculation:

```txt
vanilla_term = M * W
directional_term = (I + Ex) * K * W

denominator = 1 + vanilla_term + directional_term
reciprocal = 1 / denominator

effective maintenance = 1 - reciprocal
maintenance correction = -M + effective maintenance
```

With the default Defines:

```txt
W = 0.5
K = 10
```

this is exactly:

```txt
maintenance correction =
    -M
    + 1
    - 1 / (1 + M/2 + 5*(I + Ex))
```

The formula uses one mixed denominator. The old `CBP_TRADE_MAINTENANCE_VANILLA_WEIGHT` and `CBP_TRADE_MAINTENANCE_DIRECTIONAL_WEIGHT` names remain only as compatibility aliases and are not read by production code.

## Runtime helpers

```txt
cbp_compute_us20_route_loss_coefficient_from_selling_baseline
  -> cbp_us20_route_loss_coefficient_result

cbp_compute_us17_native_corrections_from_baselines
  -> cbp_us17_native_selling_correction_result
  -> cbp_us17_native_import_correction_result
  -> cbp_us17_native_export_correction_result
  -> cbp_us17_maintenance_vanilla_term
  -> cbp_us17_maintenance_directional_term
  -> cbp_us17_maintenance_curve_denominator
  -> cbp_us17_maintenance_curve_reciprocal
  -> cbp_us17_native_effective_maintenance_result
  -> cbp_us17_native_maintenance_correction_result
```

## Persistence and idempotence

Persistent country state:

```txt
cbp_us17_native_selling_baseline
cbp_us17_native_import_baseline
cbp_us17_native_export_baseline
cbp_us17_native_maintenance_baseline

cbp_us17_native_selling_correction
cbp_us17_native_import_correction
cbp_us17_native_export_correction
cbp_us17_native_maintenance_correction

cbp_us20_route_loss_coefficient
cbp_us17_native_modifier_state_version = 7
```

Each refresh subtracts the previous persisted correction from the current effective modifier before rebuilding the non-CBP baseline.

## Arithmetic fixture

```txt
S = 0.10
I = 0.20
Ex = 0.30
M = 0.08
```

```txt
C = 0.05 / (1 + 0.10*10) = 0.025
effective Selling = -0.025

vanilla_term = 0.08 * 0.5 = 0.04
directional_term = (0.20 + 0.30) * 10 * 0.5 = 2.50

denominator = 1 + 0.04 + 2.50 = 3.54
effective maintenance = 1 - 1/3.54 = 0.717514
maintenance correction = 0.717514 - 0.08 = 0.637514
```

## Runtime probe

```txt
event cbp_us17_owner_modifiers.1
```

Expected marker includes:

```txt
selling_shared_coefficient=verified
mixed_denominator_formula=verified
import_export_price_effect=zero
route_money_delta=zero
proportional_goods_loss=verified
idempotence=passed
live_auto_modifier_application=passed
```

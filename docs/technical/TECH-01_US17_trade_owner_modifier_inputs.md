# TECH-01 — Shared Selling coefficient and 50/50 maintenance inputs

## Confirmed engine surfaces

| Business input | EU5 exposure | Scope |
|---|---|---|
| Selling Efficiency | `modifier:selling_efficiency` | country |
| Import Efficiency | `modifier:import_efficiency` | country |
| Export Efficiency | `modifier:export_efficiency` | country |
| Merchant Maintenance Efficiency | `modifier:merchant_maintenance_efficiency` | country |
| Moved-goods quantity | `trade_volume` | trade |

## Shared Selling coefficient

```txt
S = reconstructed non-CBP Selling Efficiency

C = CBP_ROUTE_LOSS_COEFFICIENT_MAX
    / (1 + S * CBP_ROUTE_LOSS_COEFFICIENT_CURVE)
```

The country refresh persists:

```txt
var:cbp_us20_route_loss_coefficient = C
```

US-17 consumes it through:

```txt
Selling correction = -S - C
effective Selling Efficiency = -C
```

US-20 consumes the same variable through:

```txt
goods_loss_quantity = trade_volume * C
```

The ordering is mandatory:

```txt
calculate C -> persist C -> calculate Selling correction -> every_trade
```

## Import and Export transfer

```txt
Import correction = -I
Export correction = -Ex
```

This produces zero effective Import and Export Efficiency on the two price
surfaces. There are no residual directional price curves.

## Exact maintenance-cost split

Defines:

```txt
CBP_TRADE_MAINTENANCE_VANILLA_WEIGHT = 0.5
CBP_TRADE_MAINTENANCE_DIRECTIONAL_WEIGHT = 0.5
CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE = 10
```

Let:

```txt
F_vanilla = 1 - M
F_directional = 1 / (1 + (I + Ex) * scale)
```

The actual native maintenance factor is targeted as:

```txt
F_final = 0.5 * F_vanilla + 0.5 * F_directional
```

Because EU5 exposes Merchant Maintenance Efficiency rather than the factor, the
runtime applies:

```txt
M_effective =
    0.5 * M
  + 0.5 * (1 - 1 / (1 + (I + Ex) * scale))

M_correction = M_effective - M
```

This construction is an exact 50/50 split of maintenance cost. It is deliberately
not the mixed reciprocal `1 - 1/(1 + M/2 + (I+Ex)*5)`.

## Persistence

```txt
cbp_us17_native_selling_correction
cbp_us17_native_import_correction
cbp_us17_native_export_correction
cbp_us17_native_maintenance_correction

cbp_us17_native_selling_baseline
cbp_us17_native_import_baseline
cbp_us17_native_export_baseline
cbp_us17_native_maintenance_baseline

cbp_us20_route_loss_coefficient
cbp_us17_native_modifier_state_version = 7
```

Each refresh subtracts all previous CBP corrections before reconstructing the
non-CBP baselines.

## Runtime probe

```txt
event cbp_us17_owner_modifiers.1
```

Expected marker:

```txt
selling_shared_coefficient=verified
maintenance_cost_split=50_50
import_export_price_effect=zero
proportional_goods_loss=verified
idempotence=passed
live_auto_modifier_application=passed
```
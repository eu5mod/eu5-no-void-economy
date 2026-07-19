# TECH-01 addendum — Reciprocal US-17 maintenance inputs

## Purpose

Record the production accounting surface after moving Import and Export
Efficiency away from trade-price formation and into Merchant Maintenance.

## Confirmed engine surfaces

| Business input | EU5 exposure | Scope | Status |
|---|---|---|---|
| Import Efficiency | `modifier:import_efficiency` | country | Confirmed |
| Export Efficiency | `modifier:export_efficiency` | country | Confirmed |
| Selling Efficiency | `modifier:selling_efficiency` | country | Confirmed |
| Merchant Maintenance Efficiency | `modifier:merchant_maintenance_efficiency` | country | Confirmed |
| Native moved-goods quantity | `trade_volume` | trade | Confirmed |

The tested build rejects `modifier:buying_efficiency` and
`modifier:merchant_maintenance_cost`.

## US-17 formula

Let:

```txt
S  = reconstructed non-CBP Selling Efficiency
I  = reconstructed non-CBP Import Efficiency
Ex = reconstructed non-CBP Export Efficiency
M  = reconstructed non-CBP Merchant Maintenance Efficiency
W  = CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT
K  = CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE
```

Production uses:

```txt
directional_term = (I + Ex) * K * W
denominator = 1 + M*W + directional_term
reciprocal = 1 / denominator
maintenance_target = 1 - reciprocal
maintenance_correction = maintenance_target - M
```

Defaults:

```txt
W = 0.5
K = 10
```

Therefore:

```txt
maintenance_target =
    1 - 1 / (1 + M/2 + (I + Ex)*5)
```

Import and Export corrections are exactly `-I` and `-Ex`. Selling has no CBP
correction.

## Auto-modifier surfaces

Exactly three country auto-modifiers are active:

```txt
cbp_us17_import_efficiency_cancellation
cbp_us17_export_efficiency_cancellation
cbp_us17_merchant_maintenance_reconciliation
```

There is no Selling auto-modifier. There is no route-level treasury correction.

## Baseline reconstruction

Country `modifier:*` reads include active CBP modifiers. Each refresh reconstructs:

```txt
S_baseline  = effective Selling
I_baseline  = effective Import  - previous Import correction
Ex_baseline = effective Export  - previous Export correction
M_baseline  = effective Maintenance - previous Maintenance correction
```

This preserves idempotence across monthly, policy, reform and reload refreshes.

## US-20 separation

US-20 independently calculates once per country:

```txt
route_loss_coefficient =
    CBP_ROUTE_LOSS_COEFFICIENT_MAX
    / (1 + S * CBP_ROUTE_LOSS_COEFFICIENT_CURVE)
```

The route pass reads:

```txt
cbp_us20_route_loss_coefficient_input =
    var:cbp_us20_route_loss_coefficient

goods_loss_quantity =
    trade_volume * cbp_us20_route_loss_coefficient_input
```

The US-20 route block must contain no Selling modifier read, baseline read, Define
lookup, denominator or division.

## Runtime order

```txt
cbp_refresh_us17_native_profit_modifiers_for_current_country
  -> read effective S, I, Ex and M
  -> reconstruct non-CBP baselines
  -> calculate and persist US-20 coefficient
  -> calculate US-17 reciprocal maintenance corrections
  -> persist Import, Export and Maintenance corrections
  -> persist four baselines
  -> remove stale Selling correction

cbp_run_monthly_country_trade_owner_cycle
  -> country refresh once
  -> every_trade
     -> zero-delta US-17 compatibility hook
     -> US-20 proportional goods reconciliation
```

## Persistence

```txt
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

The refresh and clear paths remove obsolete
`cbp_us17_native_selling_correction` state.

## Arithmetic fixture

```txt
S  = 0.10
I  = 0.20
Ex = 0.30
M  = 0.08
```

```txt
denominator = 3.54
reciprocal = 0.282486
maintenance_target = 0.717514
maintenance_correction = 0.637514

Selling effective = 0.10
Import effective = 0
Export effective = 0
```

US-20 remains:

```txt
coefficient = 0.025
trade_volume = 10
goods_loss = 0.25
```

## Runtime probe

Run:

```txt
event cbp_us17_owner_modifiers.1
```

Expected marker includes:

```txt
reciprocal_maintenance_formula=verified
selling=native_untouched
import_export_price_effect=zero
us20_coefficient=separate
route_money_delta=zero
proportional_goods_loss=verified
idempotence=passed
live_auto_modifier_application=passed
```

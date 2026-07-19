# TECH-01 addendum — US-17/US-20 shared coefficient inputs

## Purpose

Record the production accounting surface after replacing the previous
maintenance-reconstruction and route-treasury model with native country
price-efficiency residuals and proportional US-20 goods loss.

The architectural rule is:

```txt
calculate coefficient once
persist coefficient on country
consume the same variable in US-17 and US-20
```

## Confirmed engine surfaces

| Business input | EU5 exposure | Scope | Status |
|---|---|---|---|
| Import Efficiency | `modifier:import_efficiency` | country | Confirmed |
| Export Efficiency | `modifier:export_efficiency` | country | Confirmed |
| Selling Efficiency | `modifier:selling_efficiency` | country | Confirmed |
| Merchant Maintenance Efficiency | `modifier:merchant_maintenance_efficiency` | country | Confirmed |
| Native moved-goods quantity | `trade_volume` | trade | Confirmed |

The tested build rejects `modifier:buying_efficiency` and
`modifier:merchant_maintenance_cost`. They must not appear in executable code.

## Shared coefficient owner

Let:

```txt
S = reconstructed non-CBP Selling Efficiency
L_s = CBP_ROUTE_LOSS_COEFFICIENT_MAX
K_s = CBP_ROUTE_LOSS_COEFFICIENT_CURVE
```

The country helper calculates:

```txt
coefficient_result =
    L_s / (1 + S * K_s)
```

Temporary calculation output:

```txt
scope:cbp_us20_route_loss_coefficient_result
```

The country refresh immediately persists it:

```txt
var:cbp_us20_route_loss_coefficient =
    scope:cbp_us20_route_loss_coefficient_result
```

The calculation is owned by:

```txt
cbp_compute_us20_route_loss_coefficient_from_selling_baseline
```

Despite the `us20` name, the persisted variable is shared infrastructure. It is
created before the US-17 correction and before the route iterator.

## US-17 consumption

US-17 reads the persisted country variable:

```txt
Selling correction =
    -S - var:cbp_us20_route_loss_coefficient

Selling effective value =
    -var:cbp_us20_route_loss_coefficient
```

The US-17 Selling block must contain no route-loss max/curve define, denominator,
or division.

Import and Export retain independent curves:

```txt
I_effective  = -L_d / (1 + I * K_d)
Ex_effective = -L_d / (1 + Ex * K_d)

I_correction  = I_effective - I
Ex_correction = Ex_effective - Ex
```

Where:

```txt
L_d = CBP_TRADE_EFFICIENCY_COMPENSATION_MAX
K_d = CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE
```

Merchant Maintenance remains untouched. US-17 applies no route-level `add_gold`.

## US-20 consumption and units

US-20 reads the same persisted country value:

```txt
cbp_us20_route_loss_coefficient_input =
    var:cbp_us20_route_loss_coefficient
```

It calculates only:

```txt
goods_loss_quantity =
    trade_volume * cbp_us20_route_loss_coefficient_input
```

The US-20 route block must not contain:

```txt
modifier:selling_efficiency
var:cbp_us17_native_selling_baseline
CBP_ROUTE_LOSS_COEFFICIENT_MAX
CBP_ROUTE_LOSS_COEFFICIENT_CURVE
denominator calculation
divide
```

Unit distinction:

```txt
cbp_us20_route_loss_coefficient:
  unitless share, for example 0.025 = 2.5%

goods_loss_quantity:
  quantity of the traded good, for example 10 * 0.025 = 0.25
```

## Runtime order

Country refresh:

```txt
cbp_refresh_us17_native_profit_modifiers_for_current_country
  -> read effective Selling / Import / Export
  -> subtract previous CBP corrections
  -> reconstruct non-CBP baselines
  -> cbp_compute_us20_route_loss_coefficient_from_selling_baseline
  -> persist var:cbp_us20_route_loss_coefficient
  -> cbp_compute_us17_native_corrections_from_baselines
       Selling reads var:cbp_us20_route_loss_coefficient
  -> persist US-17 baselines and corrections
```

Route processing:

```txt
cbp_run_monthly_country_trade_owner_cycle
  -> shared country refresh once
  -> every_trade
     -> capture trade_volume
     -> US-17 compatibility hook: zero money delta
     -> cbp_compute_us20_route_loss_from_selling_efficiency
          historical name retained
          reads var:cbp_us20_route_loss_coefficient
          does not recalculate the curve
     -> goods_loss_quantity = trade_volume * coefficient
     -> centralized destination reconciliation
```

## Persistence

Persistent country state:

```txt
cbp_us17_native_selling_baseline
cbp_us17_native_import_baseline
cbp_us17_native_export_baseline

cbp_us17_native_selling_correction
cbp_us17_native_import_correction
cbp_us17_native_export_correction

cbp_us20_route_loss_coefficient
cbp_us17_native_modifier_state_version = 6
```

No route-level persistent state is required. Disabling the trade rework removes
the shared coefficient.

## Compatibility

Temporary define aliases remain for stacked branches and historical fixtures:

```txt
CBP_ROUTE_LOSS_MAX
CBP_ROUTE_LOSS_CURVE
CBD_TRADE_MAINTENANCE_MAX_IMPACT
```

Production coefficient calculation reads only:

```txt
CBP_ROUTE_LOSS_COEFFICIENT_MAX
CBP_ROUTE_LOSS_COEFFICIENT_CURVE
```

Production directional calculation reads only:

```txt
CBP_TRADE_EFFICIENCY_COMPENSATION_MAX
CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE
```

## Focused arithmetic fixture

```txt
S = 0.10
trade_volume = 10

coefficient_result =
    0.05 / (1 + 0.10 * 10)
  = 0.025

var:cbp_us20_route_loss_coefficient = 0.025
effective Selling Efficiency = -0.025

goods_loss_quantity = 10 * 0.025 = 0.25
target received = 9.75
```

## Runtime probe

Run:

```txt
event cbp_us17_owner_modifiers.1
```

Expected marker includes:

```txt
coefficient_calculated_upstream=verified
curve_formula=verified
maintenance=native_untouched
route_money_delta=zero
selling_us20_coefficient=shared
us20_recalculation=absent
proportional_goods_loss=verified
idempotence=passed
live_auto_modifier_application=passed
```

# US-17 — Reciprocal Merchant Maintenance reconciliation

## Business rule

US-17 leaves Selling Efficiency on its native price surface. Import and Export
Efficiency are removed from trade-price formation and transferred into Merchant
Maintenance.

Definitions:

```txt
S  = reconstructed non-CBP Selling Efficiency
I  = reconstructed non-CBP Import Efficiency
Ex = reconstructed non-CBP Export Efficiency
M  = reconstructed non-CBP Merchant Maintenance Efficiency

W = CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT = 0.5
K = CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE = 10
```

Target Merchant Maintenance Efficiency:

```txt
denominator = 1 + M*W + (I + Ex)*K*W

effective Merchant Maintenance Efficiency =
    1 - 1 / denominator
```

With the default Defines:

```txt
effective Merchant Maintenance Efficiency =
    1 - 1 / (1 + M/2 + (I + Ex)*5)
```

Persisted corrections:

```txt
Selling correction = none
Import correction  = -I
Export correction  = -Ex

Merchant Maintenance correction =
    -M + 1 - 1 / (1 + M/2 + (I + Ex)*5)
```

Resulting native surfaces:

```txt
effective Selling Efficiency = S
effective Import Efficiency  = 0
effective Export Efficiency  = 0
effective Merchant Maintenance Efficiency = reciprocal target
```

## Economic intent

Import and Export Efficiency no longer change absolute trade prices. Their value
is represented as logistics efficiency through Merchant Maintenance. A route with
the same price spread is therefore not penalized simply because both absolute
prices are higher.

Selling Efficiency remains Vanilla.

## US-20 separation

US-20 still calculates a physical-goods loss coefficient from Selling Efficiency,
but US-17 does not consume that coefficient and does not mirror it as a Selling
penalty.

```txt
route_loss_coefficient =
    CBP_ROUTE_LOSS_COEFFICIENT_MAX
    / (1 + S * CBP_ROUTE_LOSS_COEFFICIENT_CURVE)
```

The coefficient is persisted once per country before `every_trade` for US-20 only.

## Runtime placement

```txt
monthly country trade-owner cycle
  -> reconstruct S, I, Ex and M
  -> calculate and persist US-20 route-loss coefficient
  -> calculate US-17 Import, Export and Maintenance corrections
  -> persist corrections and baselines
  -> remove stale Selling-correction state
  -> every_trade
     -> US-17 compatibility hook returns zero money delta
     -> US-20 applies physical-goods loss
```

Policy and reform changes use the same country-governance refresh. Monthly
execution remains the fallback for research, temporary modifiers and reloads.

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

The migration removes the obsolete `cbp_us17_native_selling_correction` variable.

## Arithmetic fixture

```txt
S  = 0.10
I  = 0.20
Ex = 0.30
M  = 0.08
```

```txt
denominator = 1 + 0.08/2 + (0.20 + 0.30)*5
            = 3.54

reciprocal = 1 / 3.54
           = 0.282486

effective maintenance = 1 - 0.282486
                      = 0.717514

maintenance correction = 0.717514 - 0.08
                       = 0.637514
```

Expected effective values:

```txt
Selling = 0.10
Import  = 0
Export  = 0
Merchant Maintenance = 0.717514
```

## Acceptance contract

```txt
- Selling Efficiency is not modified by US-17;
- Import and Export effective values are zero;
- Merchant Maintenance follows the reciprocal formula exactly;
- the reciprocal denominator has a 0.01 safety floor;
- no US-17 add_gold route delta is applied;
- repeated refreshes reconstruct I, Ex and M without drift;
- state version is 7;
- US-20 remains separate and proportional to trade_volume.
```

## Focused test

Run:

```txt
event cbp_us17_owner_modifiers.1
```

Wait one in-game day. Expected final marker includes:

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

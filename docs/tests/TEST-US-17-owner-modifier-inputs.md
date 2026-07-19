# TEST-US-17 — Reciprocal Merchant Maintenance

## Objective

Validate the US-17 rule:

```txt
Selling Efficiency stays native
Import Efficiency effective value = 0
Export Efficiency effective value = 0

Merchant Maintenance effective value =
    1 - 1 / (1 + M/2 + (I + Ex)*5)
```

Also verify that US-20 remains a separate physical-goods path:

```txt
US-20 goods loss =
    trade_volume * var:cbp_us20_route_loss_coefficient
```

## Static preparation

```sh
./tools/generate_all.sh
python3 tools/validate_cmm_configuration.py
python3 tools/validate_ci_static_contracts.py
./tools/validate_cbp_script_safety.sh
git diff --check
```

The static contract rejects:

```txt
- a Selling auto-modifier;
- residual Import/Export price effects;
- a missing Merchant Maintenance auto-modifier;
- US-17 dependence on the US-20 coefficient;
- route-level add_gold reconciliation;
- per-route US-20 coefficient recalculation.
```

## Focused probe

Start EU5, load a campaign, and run:

```txt
event cbp_us17_owner_modifiers.1
```

Wait one in-game day.

Expected final marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 reciprocal_maintenance_formula=verified selling=native_untouched import_export_price_effect=zero us20_coefficient=separate route_money_delta=zero proportional_goods_loss=verified idempotence=passed live_auto_modifier_application=passed cmm_gate=open
```

## Arithmetic fixture

Defines:

```txt
CBP_TRADE_MAINTENANCE_COMPONENT_WEIGHT = 0.5
CBP_TRADE_MAINTENANCE_EFFICIENCY_SCALE = 10
CBP_ROUTE_LOSS_COEFFICIENT_MAX = 0.05
CBP_ROUTE_LOSS_COEFFICIENT_CURVE = 10
```

Inputs:

```txt
S = 0.10
I = 0.20
Ex = 0.30
M = 0.08
trade_volume = 10
```

### US-17 denominator

```txt
denominator =
    1 + 0.08/2 + (0.20 + 0.30)*5

denominator = 3.54
```

### US-17 target and correction

```txt
reciprocal = 1 / 3.54
           = 0.282486

maintenance target = 1 - 0.282486
                   = 0.717514

maintenance correction = 0.717514 - 0.08
                       = 0.637514
```

Expected effective modifiers:

```txt
Selling = 0.10
Import = 0
Export = 0
Merchant Maintenance = 0.717514
```

### US-20 separate coefficient

```txt
C = 0.05 / (1 + 0.10*10)
  = 0.025

goods_loss_quantity = 10*0.025
                    = 0.25

target_received = 9.75
```

US-17 must not read `C`. US-20 must not calculate `C` inside the route block.

## Runtime validation

1. Record the country’s effective Selling, Import, Export and Merchant Maintenance
   Efficiency values before the refresh.
2. Run the focused event and wait one day.
3. Confirm exactly three localized US-17 auto-modifiers are visible:
   - Import Efficiency to Maintenance;
   - Export Efficiency to Maintenance;
   - Reciprocal Trade Maintenance.
4. Confirm no CBP Selling modifier is present.
5. Confirm effective Selling equals the reconstructed native baseline.
6. Confirm effective Import and Export equal zero.
7. Confirm effective Merchant Maintenance matches the reciprocal formula.
8. Confirm no US-17 treasury delta is emitted.
9. Confirm `cbp_us20_route_loss_coefficient` exists separately on the country.
10. Confirm `goods_loss_quantity / trade_volume` equals that coefficient.
11. Let another refresh run unchanged and confirm no drift.
12. Save, reload, and repeat the probe.

## Failure conditions

Reject the run for any of these:

```txt
Selling Efficiency changes because of a CBP auto-modifier
Import or Export retains a non-zero price effect
Merchant Maintenance does not match the reciprocal target
US-17 reads cbp_us20_route_loss_coefficient
US-17 applies add_gold or a non-zero route money delta
US-20 recalculates the coefficient per route
US-20 fails to multiply trade_volume by the coefficient
an unchanged second refresh changes a reconstructed baseline
state version is not 7
script-system, unset-variable, or invalid-modifier error
```

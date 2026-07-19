# TEST-US-17 — Shared coefficient and proportional US-20 loss

## Objective

Validate that the Selling route-loss coefficient is calculated once, persisted on
the country, and then consumed by both US-17 and US-20.

```txt
shared coefficient C =
    CBP_ROUTE_LOSS_COEFFICIENT_MAX
    / (1 + Selling Efficiency * CBP_ROUTE_LOSS_COEFFICIENT_CURVE)

US-17 effective Selling Efficiency = -C
US-20 goods loss = trade_volume * C
```

Import and Export retain their independent compensation curves:

```txt
Import residual =
    -CBP_TRADE_EFFICIENCY_COMPENSATION_MAX
    / (1 + Import Efficiency * CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE)

Export residual =
    -CBP_TRADE_EFFICIENCY_COMPENSATION_MAX
    / (1 + Export Efficiency * CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE)
```

The test must prove:

```txt
- C is calculated before the US-17 Selling correction;
- C is persisted as country variable cbp_us20_route_loss_coefficient;
- US-17 Selling consumes C and does not calculate its own reciprocal curve;
- US-20 reads the persisted C and does not recalculate it;
- Merchant Maintenance remains on the native path;
- US-17 applies no route-level add_gold delta;
- US-20 multiplies C by trade_volume;
- repeated refresh reconstructs all three non-CBP baselines without drift;
- live auto-modifiers match the arithmetic fixture after one game day.
```

## Static preparation

```sh
./tools/generate_all.sh
python3 tools/validate_cmm_configuration.py
python3 tools/validate_ci_static_contracts.py
./tools/validate_cbp_script_safety.sh
git diff --check
```

The static contract must reject any define, division, Selling baseline read, or
Selling modifier read inside the US-20 route calculation block.

## Focused probe

Start EU5, load a campaign, and run:

```txt
event cbp_us17_owner_modifiers.1
```

Wait one in-game day.

Expected final marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 coefficient_calculated_upstream=verified curve_formula=verified maintenance=native_untouched route_money_delta=zero selling_us20_coefficient=shared us20_recalculation=absent proportional_goods_loss=verified idempotence=passed live_auto_modifier_application=passed cmm_gate=open
```

## Arithmetic fixture

Default defines:

```txt
CBP_ROUTE_LOSS_COEFFICIENT_MAX = 0.05
CBP_ROUTE_LOSS_COEFFICIENT_CURVE = 10
CBP_TRADE_EFFICIENCY_COMPENSATION_MAX = 0.05
CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE = 10
```

Inputs:

```txt
S = 0.10
I = 0.20
Ex = 0.30
M = 0.08
trade_volume = 10
```

### Step 1 — Calculate the shared coefficient upstream

```txt
C = 0.05 / (1 + 0.10 * 10)
C = 0.025
```

Expected temporary result:

```txt
cbp_us20_route_loss_coefficient_result = 0.025
```

Expected persisted country value after refresh:

```txt
var:cbp_us20_route_loss_coefficient = 0.025
```

### Step 2 — Feed C into US-17

```txt
Selling correction = -0.10 - 0.025 = -0.125
Selling effective value = 0.10 - 0.125 = -0.025
```

Directional values:

```txt
Import residual = -0.05 / (1 + 0.20 * 10) = -0.016667
Import correction = -0.20 - 0.016667 = -0.216667

Export residual = -0.05 / (1 + 0.30 * 10) = -0.0125
Export correction = -0.30 - 0.0125 = -0.3125
```

### Step 3 — Read C in US-20 without recalculation

```txt
cbp_us20_route_loss_coefficient_input =
    var:cbp_us20_route_loss_coefficient

cbp_us20_route_loss_coefficient_input = 0.025
```

US-20 result:

```txt
goods_loss_quantity = 10 * 0.025 = 0.25
target_received = 10 - 0.25 = 9.75
```

US-20 must not evaluate this formula again:

```txt
0.05 / (1 + Selling Efficiency * 10)
```

Merchant Maintenance remains:

```txt
effective Merchant Maintenance Efficiency = 0.08
```

US-17 route money delta remains:

```txt
0
```

## Runtime validation

1. Record the country's non-CBP Selling, Import, Export, and Merchant Maintenance
   Efficiency values.
2. Run the focused event and wait one day.
3. Confirm exactly three localized US-17 auto-modifiers are visible.
4. Confirm `cbp_us20_route_loss_coefficient` exists on the country.
5. Confirm the effective Selling Efficiency equals the negative coefficient.
6. Confirm Import and Export equal their documented residuals.
7. Confirm Merchant Maintenance is unchanged.
8. Confirm no US-17 treasury delta is emitted.
9. Confirm the US-20 transaction input equals the persisted country coefficient.
10. Confirm `goods_loss_quantity / trade_volume` equals the coefficient.
11. Let another refresh run without changing inputs and confirm no drift.
12. Save, reload, and repeat the focused probe.

## Failure conditions

Reject the run for any of these:

```txt
fewer or more than three US-17 auto-modifiers
a Merchant Maintenance auto-modifier remains
Merchant Maintenance changes after US-17 refresh
US-17 applies add_gold or a non-zero route money delta
cbp_us20_route_loss_coefficient is missing after refresh
US-17 Selling recalculates the route-loss curve
US-20 reads Selling Efficiency or the Selling baseline
US-20 reads CBP_ROUTE_LOSS_COEFFICIENT_MAX/CURVE
US-20 contains a denominator or division
US-20 subtracts the coefficient directly as a quantity
US-20 fails to multiply trade_volume by the coefficient
US-17 and US-20 consume different coefficient values
an unchanged second refresh changes a reconstructed baseline
state version is not 6
script-system, unset-variable, or invalid-modifier error
```

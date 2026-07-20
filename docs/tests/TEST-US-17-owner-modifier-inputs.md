# TEST-US-17 — Shared Selling coefficient and mixed-denominator maintenance

## Objective

Prove simultaneously that:

```txt
C = CBP_ROUTE_LOSS_COEFFICIENT_MAX
    / (1 + S * CBP_ROUTE_LOSS_COEFFICIENT_CURVE)

US-17 effective Selling Efficiency = -C
US-20 goods loss = trade_volume * C

effective Import Efficiency = 0
effective Export Efficiency = 0

effective Merchant Maintenance Efficiency =
    1 - 1 / (1 + M/2 + 5*(I + Ex))
```

The test must also prove that the Merchant Maintenance correction itself is:

```txt
-M + 1 - 1 / (1 + M/2 + 5*(I + Ex))
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
- recalculating the Selling curve inside US-17 or US-20;
- residual Import or Export price curves;
- the rejected average-of-two-maintenance-costs formula;
- use of separate Vanilla and directional weights in production;
- any US-20 division or Selling modifier read;
- any route-level add_gold mutation.
```

## Focused probe

Start EU5, load a campaign, and run:

```txt
event cbp_us17_owner_modifiers.1
```

Wait one in-game day.

Expected final marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 selling_shared_coefficient=verified mixed_denominator_formula=verified import_export_price_effect=zero route_money_delta=zero proportional_goods_loss=verified idempotence=passed live_auto_modifier_application=passed cmm_gate=open
```

## Arithmetic fixture

Inputs:

```txt
S = 0.10
I = 0.20
Ex = 0.30
M = 0.08
trade_volume = 10
```

### Shared Selling coefficient

```txt
C = 0.05 / (1 + 0.10*10)
C = 0.025

Selling correction = -0.10 - 0.025 = -0.125
effective Selling = -0.025
```

### Import and Export cancellation

```txt
Import correction = -0.20
effective Import = 0

Export correction = -0.30
effective Export = 0
```

### Merchant Maintenance

```txt
M/2 = 0.08 * 0.5 = 0.04
5*(I + Ex) = (0.20 + 0.30) * 10 * 0.5 = 2.50

denominator = 1 + 0.04 + 2.50 = 3.54
reciprocal = 1 / 3.54 = 0.282486

effective maintenance = 1 - 0.282486 = 0.717514
maintenance correction = 0.717514 - 0.08 = 0.637514
```

Expected assertion windows:

```txt
shared coefficient: 0.024 .. 0.026
Selling correction: -0.126 .. -0.124
M/2 term: 0.039 .. 0.041
5*(I+Ex) term: 2.499 .. 2.501
denominator: 3.539 .. 3.541
effective maintenance: 0.716 .. 0.719
maintenance correction: 0.636 .. 0.639
US-20 goods loss: 0.249 .. 0.251
```

### US-20

```txt
goods loss = 10 * 0.025 = 0.25
target received = 9.75
```

## Runtime validation

1. Record the non-CBP Selling, Import, Export, and Merchant Maintenance values.
2. Run the focused event and wait one day.
3. Confirm exactly four localized US-17 auto-modifiers are visible.
4. Confirm `cbp_us20_route_loss_coefficient` exists and Selling equals its negative.
5. Confirm Import and Export equal zero.
6. Confirm Merchant Maintenance equals the mixed-denominator target.
7. Confirm no US-17 treasury delta is emitted.
8. Confirm US-20 goods loss divided by trade volume equals the persisted coefficient.
9. Let another refresh run without changing inputs and confirm no baseline drift.
10. Save, reload, and repeat the focused probe.

## Failure conditions

```txt
Selling coefficient is recalculated or differs between US-17 and US-20
Import or Export keeps a residual price effect
Merchant Maintenance uses an average of two separate costs
maintenance denominator is not 1 + M/2 + 5*(I+Ex)
maintenance correction is not -M + 1 - reciprocal
US-17 applies add_gold or a non-zero route money delta
US-20 reads Selling Efficiency or recalculates the coefficient
US-20 fails to multiply trade_volume by the coefficient
an unchanged second refresh changes a reconstructed baseline
state version is not 7
script-system, unset-variable, or invalid-modifier error
```

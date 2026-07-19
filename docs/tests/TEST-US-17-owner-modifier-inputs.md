# TEST-US-17 — Shared Selling coefficient and 50/50 maintenance

## Objective

Prove simultaneously that:

```txt
1. Selling uses the persisted coefficient shared with US-20.
2. Import and Export no longer modify absolute prices.
3. Merchant Maintenance cost is 50% Vanilla and 50% Import+Export.
4. Repeated refreshes reconstruct all four baselines without drift.
```

## Static preparation

```sh
./tools/generate_all.sh
python3 tools/validate_cmm_configuration.py
python3 tools/validate_ci_static_contracts.py
./tools/validate_cbp_script_safety.sh
git diff --check
```

## Focused probe

```txt
event cbp_us17_owner_modifiers.1
```

Wait one in-game day.

Expected final marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 selling_shared_coefficient=verified maintenance_cost_split=50_50 import_export_price_effect=zero route_money_delta=zero proportional_goods_loss=verified idempotence=passed live_auto_modifier_application=passed cmm_gate=open
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

### Selling and US-20

```txt
C = 0.05 / (1 + 0.10*10) = 0.025

Selling correction = -0.10 - 0.025 = -0.125
effective Selling = -0.025

US-20 goods loss = 10 * 0.025 = 0.25
target received = 9.75
```

### Import and Export

```txt
Import correction = -0.20
effective Import = 0

Export correction = -0.30
effective Export = 0
```

### 50/50 maintenance cost

```txt
Vanilla maintenance factor = 1 - 0.08 = 0.92
Directional denominator = 1 + (0.20 + 0.30)*10 = 6
Directional factor = 1/6 = 0.166667

Final maintenance factor =
    0.5*0.92 + 0.5*0.166667
  = 0.543333

Effective Merchant Maintenance Efficiency =
    1 - 0.543333
  = 0.456667

Maintenance correction =
    0.456667 - 0.08
  = 0.376667
```

Equivalent efficiency-side calculation:

```txt
0.5*0.08 + 0.5*(1 - 1/6) = 0.456667
```

## Failure conditions

Reject the run when any of these occurs:

```txt
Selling does not equal the negative persisted coefficient
US-17 recalculates the Selling curve after persistence
US-20 recalculates or reads Selling in trade scope
Import or Export retains a non-zero effective price modifier
maintenance uses the mixed-denominator reciprocal formula
maintenance is not the exact sum of the two 50% cost components
one of the four baseline reconstructions drifts
state version is not 7
US-17 mutates treasury through add_gold
US-20 fails to multiply trade_volume by the persisted coefficient
```
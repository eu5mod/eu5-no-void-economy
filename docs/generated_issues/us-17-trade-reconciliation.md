# US-17 — Native trade-efficiency compensation

## Business rule

US-17 keeps the native trade-profit and Merchant Maintenance paths, but replaces
the three country price-efficiency inputs with diminishing residual effects.

Definitions:

```txt
S  = reconstructed non-CBP Selling Efficiency
I  = reconstructed non-CBP Import Efficiency
Ex = reconstructed non-CBP Export Efficiency

L_s = define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_MAX
K_s = define:NCountry|CBP_ROUTE_LOSS_COEFFICIENT_CURVE

L_d = define:NCountry|CBP_TRADE_EFFICIENCY_COMPENSATION_MAX
K_d = define:NCountry|CBP_TRADE_EFFICIENCY_COMPENSATION_CURVE
```

## Shared coefficient calculated and persisted upstream

The Selling curve is calculated once per country:

```txt
coefficient_result =
    L_s / (1 + S * K_s)
```

The result is persisted immediately:

```txt
var:cbp_us20_route_loss_coefficient = coefficient_result
```

This country variable is the single source of truth for US-17 and US-20.

US-17 then reads the persisted value:

```txt
Selling correction =
    -S - var:cbp_us20_route_loss_coefficient

Import correction =
    -I - L_d / (1 + I * K_d)

Export correction =
    -Ex - L_d / (1 + Ex * K_d)
```

The resulting native effective values are:

```txt
effective Selling Efficiency =
    -var:cbp_us20_route_loss_coefficient

effective Import Efficiency =
    -L_d / (1 + I * K_d)

effective Export Efficiency =
    -L_d / (1 + Ex * K_d)
```

The US-17 Selling correction contains no route-loss define lookup, denominator,
or division. It consumes the already-persisted country coefficient.

## Merchant Maintenance and money

Merchant Maintenance is not cancelled, reconstructed, or replaced:

```txt
effective merchant_maintenance_efficiency
    = Vanilla / non-CBP merchant_maintenance_efficiency
```

US-17 applies no route-level `add_gold` reconciliation. The historical route
hook remains only as a zero-delta compatibility surface.

## Coupling with US-20

US-20 reads exactly the same persisted country variable:

```txt
goods_loss_quantity =
    trade_volume * var:cbp_us20_route_loss_coefficient
```

The two stories therefore consume the same value:

```txt
US-17:
  effective selling_efficiency
    = -var:cbp_us20_route_loss_coefficient

US-20:
  goods_loss_quantity
    = trade_volume * var:cbp_us20_route_loss_coefficient
```

Import and Export use a separate max/curve pair, so their economic residual can
be balanced independently from physical transit losses.

## Runtime placement

```txt
monthly_country_pulse(country)
  -> cbp_run_monthly_country_trade_owner_cycle
     -> reconstruct non-CBP Selling / Import / Export baselines
     -> calculate coefficient_result once
     -> persist var:cbp_us20_route_loss_coefficient
     -> calculate US-17 corrections from the persisted variable
     -> persist US-17 corrections and baselines
     -> every_trade
        -> US-17 compatibility hook returns zero money delta
        -> US-20 reads var:cbp_us20_route_loss_coefficient
        -> goods loss = trade_volume × coefficient
```

Policy and reform changes use the same country-governance refresh. Monthly
execution remains the fallback for research and temporary modifiers.

## Baseline reconstruction and persistence

Country `modifier:*` reads include active CBP auto-modifiers. Each refresh
subtracts the previous persisted Selling, Import, and Export corrections before
reconstructing the non-CBP baselines.

Persistent country state:

```txt
cbp_us17_native_selling_correction
cbp_us17_native_import_correction
cbp_us17_native_export_correction
cbp_us17_native_selling_baseline
cbp_us17_native_import_baseline
cbp_us17_native_export_baseline
cbp_us20_route_loss_coefficient
cbp_us17_native_modifier_state_version = 6
```

Disabling the trade rework removes `cbp_us20_route_loss_coefficient` and clears
the three US-17 corrections. State from the previous maintenance-reconstruction
implementation is also removed.

The reciprocal denominators have a safety floor of `0.01`, inactive for the
normal non-negative efficiency range.

## Acceptance contract

```txt
- the Selling coefficient is calculated exactly once per country refresh;
- the coefficient is persisted before the US-17 correction is calculated;
- US-17 Selling reads var:cbp_us20_route_loss_coefficient;
- US-17 Selling does not recalculate the route-loss curve;
- US-20 reads the same persisted country variable;
- US-20 contains no route-loss define lookup, denominator, or division;
- Import and Export retain their independent reciprocal curves;
- Merchant Maintenance Efficiency remains untouched;
- no US-17 add_gold route delta is applied;
- repeated refreshes reconstruct the non-CBP baselines without drift;
- the shared refresh occurs once before every_trade;
- disabled trade rework removes the shared coefficient;
- all three auto-modifiers remain visible and gated.
```

## Focused test

Run:

```txt
event cbp_us17_owner_modifiers.1
```

With the default fixture:

```txt
S = 0.10
trade_volume = 10

coefficient_result = 0.025
var:cbp_us20_route_loss_coefficient = 0.025
effective Selling Efficiency = -0.025
US-20 goods loss = 10 × 0.025 = 0.25
target received = 9.75
```

Expected final marker includes:

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

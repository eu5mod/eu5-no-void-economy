# US-17 - Operation-aware trade-profit reconciliation

## Business rule

Vanilla applies Selling Efficiency to the destination price and applies exactly
one origin-price efficiency according to route direction:

```txt
trade_operation_efficiency = Import Efficiency for an import
trade_operation_efficiency = Export Efficiency for an export
```

CBP removes Import, Export, and Selling Efficiency from the price margins. It
also removes native Merchant Maintenance Efficiency, then applies the selected
operation efficiency plus Selling Efficiency to merchant maintenance.

For non-CBP baselines `I`, `Ex`, `S`, and `M`:

```txt
E_D = I for an import; Ex for an export
D = define:NCountry|MERCHANT_MAINTENANCE_COST
C = min(E_D + S, D)

CBP import correction      = -I
CBP export correction      = -Ex
CBP selling correction     = -S
CBP maintenance correction = C_import - M
C_import = min(-CBP selling correction - CBP import correction, D)
import treasury delta      = 0
export treasury delta      = D * (C_export - C_import)
```

The sum is not averaged and has no lower clamp. Negative efficiency therefore
increases maintenance, while positive efficiency is capped by `D`.

## Runtime placement

```txt
monthly_country_pulse(country)
  -> cbp_run_monthly_country_trade_owner_cycle
     -> refresh four non-CBP country baselines
     -> every_trade
        -> Trade.IsExport selects Import or Export Efficiency
        -> keep the native import-reference maintenance result
        -> apply the export difference when Trade.IsExport
        -> run unchanged US-20 goods reconciliation
```

Policy and reform on-actions use the shared country-governance dispatcher.
Monthly execution remains the fallback for research and temporary modifiers.

## Baseline reconstruction

Country `modifier:*` reads include active CBP auto-modifiers. Each refresh
subtracts its four previous persisted corrections before recalculation. This
reconstructs the non-CBP values and prevents drift across monthly ticks and
save reloads. The revised maintenance formula writes state version `3`; the
first refresh also reconstructs version `2` saves without carrying forward the
old full-maintenance cancellation.

## Ownership and boundaries

```txt
US-17 owner: current country in the country trade-owner pass
US-17 direction: current trade via Trade.IsExport / is_export
US-17 money mutation: one add_gold route delta
US-20 owner: route-local goods reconciliation
US-20 stock mutation: unchanged centralized stock/goods path
```

EU5 exposes no trade-scope modifier able to replace Import or Export Efficiency
inside native route-profit projection. The operation-aware delta is exact for
treasury but is not represented in Vanilla route-profit UI or AI projection.

## Acceptance contract

```txt
- three price auto-modifiers cancel Import, Export, and Selling;
- the fourth auto-modifier replaces Maintenance with the import reference;
- import routes select Import Efficiency;
- export routes select Export Efficiency;
- one route never applies both directional efficiencies;
- C is a sum without division and is capped by D;
- negative C remains negative;
- repeated refreshes do not drift;
- monthly refresh occurs once before every_trade;
- US-17 money is applied once before US-20 goods reconciliation;
- all four auto-modifiers have visible localization.
```

## Focused test

Run `event cbp_us17_owner_modifiers.1`, wait one in-game day, and expect:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 operation_input=import_or_export_by_Trade.IsExport native_price_inputs_cancelled=selling_import_export maintenance=import_reference_plus_export_delta maintenance_formula=verified clamp=merchant_maintenance_cost_define negative_efficiency=preserved idempotence=passed live_auto_modifier_application=passed cmm_gate=open
```

Full runtime protocol:

```txt
docs/tests/TEST-US-17-owner-modifier-inputs.md
```

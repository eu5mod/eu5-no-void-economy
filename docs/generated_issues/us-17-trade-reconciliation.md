# US-17 — Trade maintenance and import/selling efficiency in the Q8.7 route loop

## Source mapping

```txt
#105 defines the trade-maintenance-efficiency model.
#120 defines the import/selling-efficiency reinterpretation.
#161 defines the Q8.7 country trade-owner route-loop placement.
```

## Runtime placement

```txt
cbp_run_monthly_stock_cycle_q8_7_owner_switch
  -> cbp_run_monthly_country_trade_owner_cycle
     -> every_trade
        -> save trade owner
        -> save source market
        -> save target market
        -> save traded good
        -> capture trade_volume
        -> capture confirmed moved-goods quantity
        -> enter saved trade-owner country scope
        -> capture country modifier and define-derived maintenance inputs
        -> run US-17 / US-20 route reconciliation
```

The live insertion point is:

```txt
scope:cbp_trade_owner_country = {
  cbp_capture_trade_owner_country_modifier_inputs = yes
  cbp_run_us17_us20_route_reconciliation_from_owner_modifiers = yes
}
```

US-17 must not add a second route-discovery pass and must not run inside the
market-local `every_market_in_world` body.

## Correct engine inputs

The tested EU5 build exposes:

```txt
modifier:import_efficiency
modifier:selling_efficiency
modifier:merchant_maintenance_efficiency
define:NCountry|MERCHANT_MAINTENANCE_COST
```

The former candidate names below are invalid modifier types and must not appear
in executable script:

```txt
modifier:buying_efficiency
modifier:merchant_maintenance_cost
```

US-17 keeps the semantic field name `buying_efficiency`, but its engine source
is `import_efficiency`.

The three country modifiers are read only from:

```txt
scope:cbp_trade_owner_country
```

They must never be read from the scheduler country, market-center owner, source
market owner, or target market owner unless that scope independently resolves
to the saved trade owner.

## Base merchant maintenance

The base cost is a define, not a country modifier:

```txt
base_maintenance_unit_cost =
    define:NCountry|MERCHANT_MAINTENANCE_COST
```

NVE already overrides this define. The script reads the effective loaded value
rather than duplicating or hardcoding it.

The route base amount is:

```txt
base_maintenance_amount =
    trade_volume * base_maintenance_unit_cost
```

`trade_volume` is the merchant-capacity route value. The moved-goods quantity,
which is derived through the existing literal-good transport-cost helper, is a
separate input and must not replace `trade_volume` in this formula.

## Existing merchant-maintenance efficiency

The country modifier is beneficial and reduces base maintenance:

```txt
merchant_maintenance_factor =
    max(0, 1 - merchant_maintenance_efficiency)

adjusted_base_maintenance =
    base_maintenance_amount * merchant_maintenance_factor
```

The factor is lower-bounded at zero so an efficiency above 100% does not create
negative base maintenance.

## Maximum-only import/selling cap

The repurposed average is capped only above `1`:

```txt
average_efficiency =
    (import_efficiency + selling_efficiency) / 2

capped_average_efficiency =
    min(average_efficiency, 1)
```

EU5 bound-oriented syntax:

```txt
divide = 2
max = 1
```

There is deliberately no `min = 0`. A negative average remains negative and
therefore creates an added maintenance cost.

## Maintenance-side saving

```txt
maintenance_saving =
    adjusted_base_maintenance * capped_average_efficiency
```

The complete intended route reconciliation remains:

```txt
old_price_side_bonus =
    quantity * sell_price * selling_efficiency
  + quantity * buy_price * import_efficiency * (1 + export_cost_modifier)

route_reconciliation_delta =
    -old_price_side_bonus
    + maintenance_saving
    + new_import_selling_efficiency_effect
```

The current implementation leaves `new_import_selling_efficiency_effect` at
zero because the reinterpretation is represented through old bonus removal and
the maintenance-side saving. It remains a distinct debug field.

## Money owner and application boundary

The route delta belongs to:

```txt
scope:cbp_trade_owner_country
```

The confirmed cash surface is:

```txt
add_gold = route_reconciliation_delta
```

This proves signed treasury mutation only. It does not prove that the vanilla
trade-route profit display or country trade-income ledger changes by the same
amount.

Until the route-profit/country-income relationship is confirmed in TECH-01:

```txt
- ModeU5 may calculate and accumulate the route delta;
- ModeU5 may exercise add_gold in deterministic tests;
- visible route-profit and country-income accounting remains blocked;
- the missing accounting surface remains visible in diagnostics.
```

## Current live-input boundary

Confirmed and captured:

```txt
trade_volume
import_efficiency
selling_efficiency
merchant_maintenance_efficiency
MERCHANT_MAINTENANCE_COST define
base_maintenance_amount = trade_volume × define
```

Still blocked pending route-safe exposure:

```txt
sell price
buy price
export cost modifier
trade-route profit read/write surface
country trade-income accounting surface
```

Therefore the live route-money path still fails closed when the price inputs are
unavailable, but it must not report owner modifiers or base maintenance as
unavailable.

## US-20 separation

US-20 retains its separate route-maintenance input for received-goods loss:

```txt
cbp_us20_trade_maintenance
```

Do not substitute `merchant_maintenance_efficiency` or the merchant-maintenance
define for the US-20 preserved route-maintenance value. US-17 is money-side
reconciliation; US-20 is received-goods reconciliation.

## Debug contract

```txt
trade_owner
source_market
target_market
traded_good
trade_volume
moved_goods_quantity
import_efficiency
selling_efficiency
merchant_maintenance_efficiency
base_maintenance_unit_cost
base_maintenance_amount
merchant_maintenance_factor
adjusted_base_maintenance
capped_average_efficiency
maintenance_saving
sell_price
buy_price
export_cost_modifier
old_price_side_bonus
route_reconciliation_delta
trade_owner_accumulated_delta
accounting_mode_detailed_or_fallback
```

## Deterministic probe

Run:

```txt
event cbp_us17_owner_modifiers.1
```

The probe validates:

```txt
- import_efficiency is read from the trade-owner country;
- selling_efficiency is read from the trade-owner country;
- merchant_maintenance_efficiency is read from the trade-owner country;
- the loaded MERCHANT_MAINTENANCE_COST define is read;
- base maintenance equals trade_volume × loaded define;
- (-0.4 + -0.2) / 2 remains -0.3;
- (1.4 + 1.2) / 2 is capped at 1;
- with base 20 and maintenance efficiency 0.20, adjusted maintenance is 16;
- with average 0.15, maintenance saving is 2.40;
- with old price-side bonus 35, route delta is -32.60.
```

Expected marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 owner_inputs=import_selling_merchant_maintenance_efficiency base_cost=define_NCountry_MERCHANT_MAINTENANCE_COST clamp=maximum_only
```

Runbook:

```txt
docs/tests/TEST-US-17-owner-modifier-inputs.md
```

## Acceptance checks

```txt
- The route hook runs from the country trade-owner every_trade loop.
- No second every_market_center_in_country route pass is added.
- No US-17 route hook runs in the every_market_in_world market-local body.
- Semantic buying efficiency is sourced from modifier:import_efficiency.
- Selling efficiency is sourced from modifier:selling_efficiency.
- Maintenance efficiency is sourced from modifier:merchant_maintenance_efficiency.
- Base cost is sourced from define:NCountry|MERCHANT_MAINTENANCE_COST.
- Base maintenance is trade_volume × the effective loaded define.
- The import/selling average has max = 1 and no min = 0.
- Negative average efficiency remains negative.
- Maintenance efficiency contributes through max(0, 1 - efficiency).
- Old price-side import/selling bonus is removed in the route formula.
- Delta is accumulated on the saved trade owner.
- No stock-side mutation is introduced by US-17.
- Missing route price and accounting surfaces remain explicit.
- The focused probe passes without parser, unset-scope, or localization errors.
```

## Coverage conclusion

```txt
Implemented statically:
  Q8.7 placement
  trade-owner attribution
  import_efficiency country read
  selling_efficiency country read
  merchant_maintenance_efficiency country read
  effective maintenance define read
  trade_volume × define base maintenance
  maximum-only import/selling cap
  maintenance-factor arithmetic
  deterministic formula probe
  signed treasury test surface

Runtime rerun required:
  corrected owner-input and define probe

Still not production-complete:
  live route price reads
  live export-cost read
  visible route-profit mutation
  visible country trade-income accounting
```

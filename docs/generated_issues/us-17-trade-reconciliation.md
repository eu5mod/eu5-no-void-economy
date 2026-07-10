# US-17 — Trade maintenance and buying/selling efficiency in the Q8.7 route loop

## Source mapping

```txt
#105 defines the trade-maintenance-efficiency model.
#120 defines the buying/selling-efficiency model.
#161 defines the Q8.7 country trade-owner route-loop placement.
```

The three country modifier inputs are owned by the country that owns the trade:

```txt
buying_efficiency
selling_efficiency
merchant_maintenance_cost
```

They must never be read from the scheduler country, market-center owner, source
market, or target market unless that scope is independently the saved trade owner.

## Runtime placement

```txt
modeu5_run_monthly_stock_cycle_q8_7_owner_switch
  -> modeu5_run_monthly_country_trade_owner_cycle
     -> every_trade
        -> save trade owner
        -> save source market
        -> save target market
        -> save traded good
        -> capture confirmed moved-goods quantity
        -> enter saved trade-owner country scope
        -> capture country modifier inputs
        -> run US-17 / US-20 route reconciliation
```

The live insertion point is:

```txt
scope:modeu5_trade_owner_country = {
  modeu5_capture_trade_owner_country_modifier_inputs = yes
  modeu5_run_us17_us20_route_reconciliation_from_owner_modifiers = yes
}
```

US-17 must not add a second route-discovery pass and must not run inside the
market-local `every_market_in_world` body.

## Confirmed country modifier reads

The modifier-value script surface returns the summed modifier value affecting the
current country scope. ModeU5 reads the values only after switching to the saved
trade-owner country:

```txt
modeu5_trade_owner_buying_efficiency = {
  value = modifier:buying_efficiency
}

modeu5_trade_owner_selling_efficiency = {
  value = modifier:selling_efficiency
}

modeu5_trade_owner_merchant_maintenance_cost = {
  value = modifier:merchant_maintenance_cost
}
```

The capture effect stores transaction-local route inputs:

```txt
modeu5_trade_efficiency_buying_efficiency
modeu5_trade_efficiency_selling_efficiency
modeu5_trade_efficiency_merchant_maintenance_cost
modeu5_trade_efficiency_country_modifier_inputs_available
```

No persistent per-route or multidimensional record is created.

## Maximum-only buying/selling cap

The average buying/selling efficiency is capped only above `1`:

```txt
average_efficiency =
    (buying_efficiency + selling_efficiency) / 2

capped_average_efficiency =
    min(average_efficiency, 1)
```

EU5 script-value form:

```txt
modeu5_buying_selling_efficiency_clamped = {
  value = modifier:buying_efficiency
  add = modifier:selling_efficiency
  divide = 2
  max = 1
}
```

There is deliberately no `min = 0` lower bound.

Consequences:

```txt
average = 0.15  -> 0.15
average = 1.30  -> 1.00
average = -0.30 -> -0.30
```

A negative value must increase maintenance rather than being silently converted
to zero.

## Maintenance-side formula

The country maintenance modifier is applied before the buying/selling efficiency
benefit:

```txt
maintenance_factor =
    1 + merchant_maintenance_cost

adjusted_base_maintenance =
    base_maintenance_amount * maintenance_factor

maintenance_saving =
    adjusted_base_maintenance * capped_average_efficiency
```

Because negative average efficiency is retained:

```txt
negative average
  -> negative maintenance_saving
  -> additional route cost
```

The complete intended route reconciliation remains:

```txt
old_price_side_bonus =
    quantity * sell_price * selling_efficiency
  + quantity * buy_price * buying_efficiency * (1 + export_cost_modifier)

route_reconciliation_delta =
    -old_price_side_bonus
    + maintenance_saving
    + new_buying_selling_efficiency_effect
```

The current implementation leaves `new_buying_selling_efficiency_effect` at zero
because the buying/selling reinterpretation is already represented through old
bonus removal and the maintenance-side saving. It remains a distinct debug field
so the #105 and #120 concepts are not silently collapsed.

## Money owner and application boundary

The route delta belongs to:

```txt
scope:modeu5_trade_owner_country
```

The confirmed cash surface is:

```txt
add_gold = route_reconciliation_delta
```

This proves signed treasury mutation only. It does not prove that the vanilla
trade-route profit display or the country trade-income ledger changes by the same
amount.

Until the route-profit/country-income relationship is confirmed in TECH-01:

```txt
- ModeU5 may calculate and accumulate the route delta;
- ModeU5 may exercise the confirmed add_gold cash surface in deterministic tests;
- production-visible route-profit and country-income accounting remains blocked;
- the missing accounting surface must remain visible in diagnostics.
```

## Current live-input boundary

The following inputs are now live country reads and are no longer fail-closed:

```txt
buying_efficiency
selling_efficiency
merchant_maintenance_cost
```

The following remain route-specific engine boundaries:

```txt
sell price
buy price
export cost modifier
base maintenance amount
trade-route profit read/write surface
country trade-income accounting surface
```

Therefore the live route-money path still fails closed when those route inputs are
unavailable, but it must not describe the three country modifiers as unavailable.

## US-20 separation

US-20 retains a separate route-maintenance input for received-goods loss:

```txt
modeu5_us20_trade_maintenance
```

Do not substitute `merchant_maintenance_cost` directly for the US-20 preserved
route-maintenance value. The country modifier contributes to the US-17 maintenance
cost formula; the US-20 goods-delivery formula remains a distinct route surface.

## Debug contract

```txt
trade_owner
source_market
target_market
traded_good
quantity
buying_efficiency
selling_efficiency
merchant_maintenance_cost
capped_average_efficiency
base_maintenance_amount
maintenance_factor
adjusted_base_maintenance
maintenance_saving
sell_price
buy_price
export_cost_modifier
old_price_side_bonus
new_buying_selling_efficiency_effect
route_reconciliation_delta
trade_owner_accumulated_delta
accounting_mode_detailed_or_fallback
```

## Deterministic probe

Run:

```txt
event modeu5_us17_owner_modifiers.1
```

The probe validates:

```txt
- all three values are read from the trade-owner country modifier surface;
- (-0.4 + -0.2) / 2 remains -0.3;
- (1.4 + 1.2) / 2 is capped at 1;
- merchant_maintenance_cost participates in the maintenance factor;
- seeded formula result matches the expected route delta.
```

Expected marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 owner_inputs=buying_selling_merchant_maintenance clamp=maximum_only
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
- buying_efficiency is read from the saved trade-owner country.
- selling_efficiency is read from the saved trade-owner country.
- merchant_maintenance_cost is read from the saved trade-owner country.
- The buying/selling average has max = 1 and no min = 0.
- Negative average efficiency remains negative.
- merchant_maintenance_cost contributes through 1 + modifier value.
- Old price-side buy/sell bonus is removed in the route formula.
- Delta is accumulated on the saved trade owner.
- No stock-side mutation is introduced by US-17.
- Missing route price/base-maintenance/income surfaces remain explicit.
- The focused owner-modifier probe passes without parser or localization errors.
```

## Coverage conclusion

```txt
Implemented:
  Q8.7 placement
  trade-owner attribution
  buying_efficiency country read
  selling_efficiency country read
  merchant_maintenance_cost country read
  maximum-only average cap
  maintenance-factor arithmetic
  deterministic formula probe
  signed treasury test surface

Still not production-complete:
  live route price reads
  live export-cost read
  live base-maintenance amount read
  visible route-profit mutation
  visible country trade-income accounting
```

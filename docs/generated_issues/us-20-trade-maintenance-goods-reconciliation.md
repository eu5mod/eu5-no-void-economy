# US-20 — Trade maintenance as received-goods loss factor

## Correct source mapping

Use this corrected mapping:

```txt
#105 defines the new trade maintenance efficiency model.
#120 defines the buying/selling trade efficiency model.
#161 defines where both route-level hooks belong.
US-20 defines how trade maintenance affects received goods.
```

#105 and #120 are complementary. #120 does not replace #105.

## Functional objective

US-20 extends the route economics by assigning separate meanings:

```txt
#105 trade maintenance efficiency
  -> maintenance-side route economics

#120 buying/selling efficiency
  -> buy/sell route economics after old price-side bonus removal

US-20 trade maintenance
  -> received-goods loss factor
```

The old vanilla price-side buying/selling bonus still must be removed so that the #120 buy/sell model does not stack on top of vanilla.

## Money-side rule

The old price-side bonus to remove is:

```txt
old_price_side_bonus =
    quantity * sell_price * selling_efficiency
  + quantity * buy_price * buying_efficiency * (1 + export_cost_modifier)
```

The corrected money delta combines the separate #105 and #120 effects:

```txt
money_reconciliation_delta =
    - old_price_side_bonus
    + new_trade_maintenance_efficiency_effect
    + new_buying_selling_efficiency_effect
```

Where:

```txt
new_trade_maintenance_efficiency_effect
  comes from #105

new_buying_selling_efficiency_effect
  comes from #120
```

Do not collapse both into one generic `trade_efficiency_money_effect` in documentation or debug output.

## Buying/selling efficiency support value

The #120 buy/sell side may use a clamped average read from the saved trade owner country:

```txt
modeu5_clamped_buying_selling_efficiency = {
  value = scope:modeu5_trade_owner_country.modifier:buying_efficiency
  add = scope:modeu5_trade_owner_country.modifier:selling_efficiency
  divide = 2

  min = 0
  max = 1
}
```

This belongs to #120. It is not the #105 trade-maintenance-efficiency definition.

## Goods-side rule

US-20 preserves the route's vanilla/current `trade_maintenance` value and uses it for goods delivery.

The amount sent is unchanged:

```txt
goods_amount_sent = goods_amount_sent
```

Target received goods:

```txt
target_goods_amount_received =
    goods_amount_sent
  - 0.1 * clamp((1 - trade_maintenance), 0, 1)
```

Safety floor:

```txt
target_goods_amount_received =
    max(target_goods_amount_received, 0)
```

If the engine already produced a received amount, apply only the difference:

```txt
goods_reconciliation_delta =
    target_goods_amount_received
  - engine_goods_amount_received
```

## Q8.7 runtime placement

US-20 belongs in the same route loop as the US-17 money-side route economics:

```txt
modeu5_run_monthly_country_trade_owner_cycle
  -> every_trade
     -> save owner / source / target / good
     -> capture quantity
     -> #105 maintenance-efficiency money-side route effect
     -> #120 buying/selling-efficiency money-side route effect
     -> US-20 goods-received reconciliation
```

It must not run inside the `every_market_in_world` market-local body, and it must not add a second `every_market_center_in_country -> every_trade` discovery pass.

Required local shape:

```txt
every_trade = {
  save_temporary_scope_as = modeu5_trade_owner_trade

  owner = { save_temporary_scope_as = modeu5_trade_owner_country }
  from_market = { save_temporary_scope_as = modeu5_trade_owner_source_market }
  to_market = { save_temporary_scope_as = modeu5_trade_owner_target_market }
  traded_goods = { save_temporary_scope_as = modeu5_trade_owner_good }

  modeu5_capture_country_trade_owner_trade_quantity = yes

  modeu5_compute_trade_maintenance_efficiency_delta = yes
  modeu5_compute_buying_selling_efficiency_delta = yes
  modeu5_add_trade_money_delta_to_trade_owner = yes

  modeu5_compute_us20_goods_received_delta = yes
  modeu5_apply_us20_goods_delta_to_target_market_good = yes
}
```

Money owner:

```txt
scope:modeu5_trade_owner_country
```

Goods owner:

```txt
scope:modeu5_trade_owner_target_market
scope:modeu5_trade_owner_good
```

## PERF-14 / CMM accounting rule

The route hook must respect PERF-14 accounting mode plumbing.

```txt
Detailed route accounting available:
  compute money delta in every_trade
  compute goods delta in every_trade
  apply money delta to saved trade owner
  apply goods delta to target market/good through the approved central operator

Detailed accounting unavailable or blocked:
  emit explicit fallback/block diagnostics
  do not silently drop the route economics or goods-received effect
```

If detailed Market x Country x Good accounting is unavailable, US-20 must either use a confirmed market-level fallback or emit a blocked diagnostic. It must not pretend country-level goods reconciliation happened.

## Storage rule

US-20 should remain transaction-local for MVP.

```txt
Route-local calculated fields:
  trade_maintenance_efficiency_inputs
  buying_efficiency
  selling_efficiency
  clamped_buying_selling_efficiency
  old_price_side_bonus
  new_trade_maintenance_efficiency_effect
  new_buying_selling_efficiency_effect
  money_reconciliation_delta
  preserved_trade_maintenance
  goods_amount_sent
  engine_goods_amount_received
  target_goods_amount_received
  goods_reconciliation_delta

Persistent route-level state:
  none
```

## Expected implementation files

```txt
docs/generated_issues/us-20-trade-maintenance-goods-reconciliation.md

in_game/common/script_values/
  modeu5_us20_trade_goods_reconciliation_values.txt

in_game/common/scripted_effects/
  modeu5_us20_trade_goods_reconciliation_effects.txt
  modeu5_country_trade_owner_effects.txt

docs/tests/
  TEST-US-20-trade-maintenance-goods-reconciliation.md
```

## Debug contract

```txt
trade_owner
source_market
target_market
traded_good
quantity_sent
engine_goods_amount_received
preserved_trade_maintenance
target_goods_amount_received
goods_reconciliation_delta
trade_maintenance_efficiency_inputs
buying_efficiency
selling_efficiency
clamped_buying_selling_efficiency
old_price_side_bonus
new_trade_maintenance_efficiency_effect
new_buying_selling_efficiency_effect
money_reconciliation_delta
accounting_mode_detailed_or_fallback
```

## Acceptance checks

```txt
- #105 is documented as the trade maintenance efficiency source.
- #120 is documented as the buying/selling trade efficiency source.
- #161 defines only the route-loop placement.
- US-20 runs inside the country trade-owner every_trade loop.
- US-20 does not run in the every_market_in_world market-local body.
- US-20 does not add a second market-center trade loop.
- Money delta is owned by the saved trade owner.
- Goods delta is owned by target market/good.
- #105 and #120 effects are separate in debug output.
- Missing detailed accounting is visible as fallback/block diagnostics.
- No silent money or goods adjustment occurs.
```

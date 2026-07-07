# US-20 — Trade maintenance as received-goods loss factor

## Supersession rule

US-20 stacks over the trade-efficiency redefinition from #120.

```txt
#120 defines the new meaning of trade efficiency.
#161 defines the route-loop placement.
US-20 defines the goods-received role of trade maintenance.
```

Older #105 / early #107 wording is not authoritative for the meaning of trade efficiency.

## Functional objective

Under US-20:

```txt
buying_efficiency + selling_efficiency
  -> money-side route reconciliation

vanilla/current trade_maintenance
  -> received-goods loss factor
```

This means US-20 changes the US-17 money replacement rule and gives `trade_maintenance` a goods-delivery role.

## Money-side rule

US-20 keeps the removal of the old price-side bonus:

```txt
old_price_side_bonus =
    quantity * sell_price * selling_efficiency
  + quantity * buy_price * buying_efficiency * (1 + export_cost_modifier)
```

The corrected efficiency input is:

```txt
clamped_average_efficiency =
    clamp((buying_efficiency + selling_efficiency) / 2, 0, 1)
```

EU5 bound notation:

```txt
modeu5_us20_clamped_average_efficiency = {
  value = scope:modeu5_trade_owner_country.modifier:buying_efficiency
  add = scope:modeu5_trade_owner_country.modifier:selling_efficiency
  divide = 2

  min = 0
  max = 1
}
```

US-20 money delta:

```txt
money_reconciliation_delta =
    - old_price_side_bonus
    + modeu5_trade_efficiency_money_effect
```

`modeu5_trade_efficiency_money_effect` is the #120-defined replacement effect. Do not restore pre-#120 maintenance-saving assumptions.

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

US-20 belongs in the same route loop as US-17:

```txt
modeu5_run_monthly_country_trade_owner_cycle
  -> every_trade
     -> save owner / source / target / good
     -> capture quantity
     -> US-17 or US-20 money-side reconciliation
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

  modeu5_compute_us20_money_delta = yes
  modeu5_add_us20_money_delta_to_trade_owner = yes

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

US-20 must respect #120 accounting decisions.

```txt
Detailed route accounting available:
  compute money delta in every_trade
  compute goods delta in every_trade
  apply money delta to saved trade owner
  apply goods delta to target market/good through the approved central operator

Detailed accounting unavailable or blocked:
  emit explicit fallback/block diagnostics
  do not silently drop the trade-efficiency or goods-received effect
```

If detailed Market x Country x Good accounting is unavailable, US-20 must either use a confirmed market-level fallback or emit a blocked diagnostic. It must not pretend country-level goods reconciliation happened.

## Storage rule

US-20 should remain transaction-local for MVP.

```txt
Route-local calculated fields:
  clamped_average_efficiency
  old_price_side_bonus
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
buying_efficiency
selling_efficiency
clamped_average_efficiency
old_price_side_bonus
modeu5_trade_efficiency_money_effect
money_reconciliation_delta
accounting_mode_detailed_or_fallback
```

## Acceptance checks

```txt
- US-20 stacks over the #120 trade-efficiency redefinition.
- #161 defines only the route-loop placement.
- US-20 runs inside the country trade-owner every_trade loop.
- US-20 does not run in the every_market_in_world market-local body.
- US-20 does not add a second market-center trade loop.
- Money delta is owned by the saved trade owner.
- Goods delta is owned by target market/good.
- Missing detailed accounting is visible as fallback/block diagnostics.
- No silent money or goods adjustment occurs.
```

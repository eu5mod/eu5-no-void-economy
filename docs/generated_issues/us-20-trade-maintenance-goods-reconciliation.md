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

## Vanilla income / trade-profit application probe

The money-side formula is not sufficient by itself. The implementation must prove how EU5 links route profit and country income before applying the delta to vanilla.

The required probe matrix is:

```txt
1. Read old trade-owner country income.
2. Read old trade route profit.
3. Add the route reconciliation delta to trade route profit.
4. Read new trade route profit.
5. Read new trade-owner country income.
6. Test:

   old_country_income =
       new_country_income
     - added_trade_route_profit
```

Interpretation:

```txt
If the equality holds:
  route profit feeds country income.
  Apply the delta to route profit only.

If the equality does not hold:
  route profit and country income are separate surfaces.
  Decide whether to apply the delta to country income, route profit, or both.

If any read/write surface is unavailable:
  block income application and log the missing API surface.
```

Required probe surfaces:

```txt
read_country_income
read_trade_route_profit
add_trade_route_profit
verify_country_income_after_route_profit_delta
```

Until those are confirmed in TECH-01, only the ModeU5 accumulator may be updated; vanilla income/profit must remain blocked.

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

When the delta is negative, it is a loss:

```txt
goods_loss_quantity =
    -goods_reconciliation_delta
```

The loss must not be treated as a transfer. US-20 separates:

```txt
base goods movement:
  add at destination, or transfer country-market to country-market

loss reconciliation:
  remove the delivery loss at destination
```

## Confirmed market-level destination loss surface

Public EU5 script documentation lists `add_goods_supply` as a market-scope effect that adds goods to a market stockpile and accepts `goods` and `amount` parameters.

US-20 uses this market-stockpile surface with a negative amount for delivery loss:

```txt
market_loss_delta = -goods_loss_quantity

scope:target_market = {
  add_goods_supply = {
    goods = scope:route_good
    amount = market_loss_delta
  }
}
```

Therefore the previous `remove_good` probe is no longer required. The implementation should track this as market-stockpile loss application, not as a blocked missing surface.

Runtime note: public docs confirm the market mutation surface, but the in-game fixture must still confirm that the engine accepts a negative `amount` as stockpile removal.

## Four-case market-accounting matrix

US-20 must classify both sides of the route:

```txt
is origin market promoted?
is destination market promoted?
```

The resulting four cases are:

```txt
1. Origin market non-promoted + destination market non-promoted

   Base movement:
     no country-market transfer is available.

   Loss reconciliation:
     remove at destination market through add_goods_supply with a negative amount.

2. Origin market promoted + destination market non-promoted

   Base movement:
     origin has country-market detail, destination does not.

   Loss reconciliation:
     remove at destination market through add_goods_supply with a negative amount.

3. Origin market non-promoted + destination market promoted

   Base movement:
     add at destination country x market only.

   Loss reconciliation:
     remove the loss at destination:
       - destination market through add_goods_supply with a negative amount
       - destination country x market through remove_stock

4. Origin market promoted + destination market promoted

   Base movement:
     transfer country x market -> country x market.

   Loss reconciliation:
     remove the loss at destination:
       - destination market through add_goods_supply with a negative amount
       - destination country x market through remove_stock
```

This means destination promotion decides whether a detailed receiver country can exist. Origin promotion decides whether the base receipt path is an add-at-destination or a country-market transfer.

## Receiver-country selection for promoted destinations

The target is:

```txt
destination_market x selected_receiver_country x good
```

Selection rules:

```txt
1. If the earlier transfer / demand-resolution path stored a receiving country,
   use that country.

2. Else, if the trade owner is present in the destination market, use the trade owner.

3. Else, reuse or extend US-10 candidate-selection machinery, but with receiver
   eligibility thresholds rather than supplier-protection thresholds.
```

Important distinction from US-10 supplier selection:

```txt
US-10 supplier selection answers:
  Which country should goods be taken from?

US-20 receiver allocation answers:
  Which country should goods arrive to / be reconciled against?
```

US-20 should reuse the same US-10 bucket sorting and tie-break ordering. The receiver-specific change is eligibility, not ordering.

### Inverted threshold logic

Supplier protection thresholds should be ignored:

```txt
modeu5_us10_minimum_stock_to_consider
modeu5_us10_supplier_min_stock_ratio
modeu5_us10_supplier_negative_balance_reserve_ratio
```

Reason:

```txt
These thresholds prevent supplier stock collapse.
US-20 is not selecting a supplier.
Low-stock countries may be eligible receivers, but they are not preferred by a new fill-ratio ordering.
```

### Smooth maximal threshold / capacity logic

Receiver eligibility should be based on whether the country is under capacity before receipt:

```txt
eligible_receiver =
    current_stock < capacity
```

The quantity should not be clipped to available capacity for the MVP:

```txt
current_stock = 99
capacity = 100
received_quantity = 10

post_receipt_stock = 109 / 100
```

This means:

```txt
- countries already at or above capacity are not eligible receivers;
- countries below capacity remain eligible;
- once selected, the receiver may temporarily exceed capacity;
- follow-up capacity/decay/reconciliation logic can correct over-capacity later;
- capacity/fill is an eligibility filter, not a priority sort key.
```

Fallback receiver ordering:

```txt
1. apply receiver eligibility filters;
2. use the same US-10 bucket sorting and tie-break ordering;
3. use deterministic fallback ordering when the US-10 order still ties.
```

For MVP, once the best receiver is selected by the US-10 ordering after receiver eligibility filtering, allocate the whole goods receipt/loss to that receiver rather than splitting across candidates.

If no selected receiver can be determined, US-20 must block the country-stock part of the goods application and log the receiver-selection failure. It must not silently remove from the trade owner if the trade owner is not present in the destination market.

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
  modeu5_accumulate_trade_efficiency_route_delta_to_trade_owner = yes
  modeu5_apply_trade_efficiency_income_reconciliation_to_trade_owner = yes

  modeu5_compute_us20_goods_received_delta = yes
  modeu5_apply_us20_goods_delta_to_target_market_good = yes
}

# remainder unchanged
```

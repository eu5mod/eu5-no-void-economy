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
     remove at destination:
       - destination market surface
       - destination country x market surface if/when available

2. Origin market promoted + destination market non-promoted

   Base movement:
     origin has country-market detail, destination does not.

   Loss reconciliation:
     remove at destination:
       - destination market surface
       - destination country x market surface if/when available

3. Origin market non-promoted + destination market promoted

   Base movement:
     add at destination country x market only.

   Loss reconciliation:
     remove the loss at destination:
       - destination market surface
       - destination country x market surface

4. Origin market promoted + destination market promoted

   Base movement:
     transfer country x market -> country x market.

   Loss reconciliation:
     remove the loss at destination:
       - destination market surface
       - destination country x market surface
```

This means destination promotion decides whether a detailed receiver country can exist. Origin promotion decides whether the base receipt path is an add-at-destination or a country-market transfer.

`remove_good` remains the market-level semantics for destination-market removal if no concrete central operator is confirmed yet. `remove_stock` remains the country-market loss operator when a selected destination receiver exists.

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

3. Else, reuse or extend US-10 candidate-selection machinery, but with a receiver
   allocation profile rather than the current supplier-selection profile.
```

Important distinction from US-10 supplier selection:

```txt
US-10 supplier selection answers:
  Which country should goods be taken from?

US-20 receiver allocation answers:
  Which country should goods arrive to / be reconciled against?
```

That means US-10 cannot be reused blindly. The receiver profile must invert several assumptions.

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
Low-stock countries should generally benefit from receiving goods.
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
- follow-up capacity/decay/reconciliation logic can correct over-capacity later.
```

Preferred receiver ordering for the fallback selector:

```txt
1. trade owner if present in destination market
2. lower fill ratio / more need for stock
3. relation / subject / market-owner / foreign buckets as tie-breakers
4. deterministic fallback ordering
```

For MVP, once the best receiver is selected, allocate the whole goods receipt/loss to that receiver rather than splitting across candidates.

If no selected receiver can be determined, US-20 must block the goods application and log the receiver-selection failure. It must not silently remove from the trade owner if the trade owner is not present in the destination market.

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
```

Money owner:

```txt
scope:modeu5_trade_owner_country
```

Goods loss owner when destination is promoted:

```txt
scope:modeu5_trade_owner_target_market
scope:modeu5_us20_goods_loss_target_country
scope:modeu5_trade_owner_good
```

Goods loss owner when destination is not promoted:

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
  classify origin/destination promotion
  apply money delta only after the income/profit API probe confirms the surface
  apply goods loss through the four-case destination reconciliation matrix

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
  goods_loss_quantity
  origin_market_promoted
  destination_market_promoted
  selected_goods_loss_country

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
origin_market_promoted
destination_market_promoted
four_case_accounting_path
traded_good
quantity_sent
engine_goods_amount_received
preserved_trade_maintenance
target_goods_amount_received
goods_reconciliation_delta
goods_loss_quantity
selected_goods_loss_country
receiver_selection_source
receiver_capacity_before
receiver_stock_before
receiver_fill_ratio_before
trade_maintenance_efficiency_inputs
buying_efficiency
selling_efficiency
clamped_buying_selling_efficiency
old_price_side_bonus
new_trade_maintenance_efficiency_effect
new_buying_selling_efficiency_effect
money_reconciliation_delta
read_country_income_probe
read_trade_route_profit_probe
add_trade_route_profit_probe
country_income_after_route_profit_delta_probe
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
- Vanilla money application remains blocked until country-income / trade-profit probes are confirmed.
- Probe matrix covers read country income, read route profit, add route profit, and the country-income relation test.
- US-20 classifies both origin-market promotion and destination-market promotion.
- Case 1 origin non-promoted / destination non-promoted removes loss at destination.
- Case 2 origin promoted / destination non-promoted removes loss at destination.
- Case 3 origin non-promoted / destination promoted adds at destination country-market, then removes destination loss.
- Case 4 origin promoted / destination promoted transfers country-market to country-market, then removes destination loss.
- Stored receiving country wins when available.
- Trade owner is selected only if present in destination market.
- If trade owner is not present, the receiver allocator extends US-10 but uses receiver-oriented capacity logic.
- Receiver allocation ignores supplier-protection thresholds.
- Receiver allocation uses under-capacity eligibility but does not cap the whole receipt to free capacity for MVP.
- Goods loss uses destination removal semantics, not transfer semantics.
- #105 and #120 effects are separate in debug output.
- Missing detailed accounting is visible as fallback/block diagnostics.
- No silent money or goods adjustment occurs.
```

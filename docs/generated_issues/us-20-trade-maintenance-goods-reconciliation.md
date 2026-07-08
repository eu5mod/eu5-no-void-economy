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
```

Money owner:

```txt
scope:modeu5_trade_owner_country
```

Market-level goods loss owner:

```txt
scope:modeu5_trade_owner_target_market
scope:modeu5_trade_owner_good
```

Country-stock goods loss owner when destination is promoted:

```txt
scope:modeu5_trade_owner_target_market
scope:modeu5_us20_goods_loss_target_country
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
  apply market-level goods loss through add_goods_supply with a negative amount
  apply promoted-destination country-stock loss through remove_stock

Detailed accounting unavailable or blocked:
  emit explicit fallback/block diagnostics
  do not silently drop the route economics or goods-received effect
```

If detailed Market x Country x Good accounting is unavailable, US-20 must still apply the market-level destination loss if the target market and route good are saved. It must block only the missing country-stock part.

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
  market_goods_supply_delta
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
market_goods_supply_delta
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

## Specification vs implementation status

Status legend:

```txt
Implemented        = code path exists and is covered by static CI and/or deterministic in-game fixture surface
Partial            = scaffold/classification exists, but at least one runtime operator or generic dispatcher is missing
Specified only     = written contract exists, no concrete runtime code yet
Blocked TECH-01    = requires confirmed EU5 API/operator before safe implementation
```

| Area | Specification | Current implementation | Status | Gap / next action |
| --- | --- | --- | --- | --- |
| Source ownership | #105 = maintenance efficiency, #120 = buy/sell efficiency, #161 = route placement, US-20 = goods received loss | Documented in US-20 and separated in function names/comments | Implemented | Keep cross-issue wording aligned if #105/#120 change. |
| Q8.7 placement | Run inside country trade-owner `every_trade`; no second market-center loop | Route reconciliation effect is called from the country trade-owner route loop and keeps the anti-second-loop guard | Implemented | Static only; still needs in-game monthly trace. |
| CMM gate | Trade rework runs only when CMM setting is enabled | Parent and route effect are gated by `modeu5_trade_rework_enabled_trigger`; deterministic fixture tests disabled gate dormancy | Implemented | None for static PR; runtime CMM toggle should be tested in-game. |
| Money formula | Remove old price-side bonus and add separate #105/#120 effects | Deterministic formula kernel computes old bonus, clamped average, and route money delta | Implemented | Current #120 side is zero placeholder pending final #120 runtime model. |
| Money accumulator | Accumulate route-local money delta to trade owner | ModeU5-only country accumulator is updated | Implemented | This is not vanilla income/profit application. |
| Vanilla income/profit application | Probe country income, route profit, add route profit, then test country-income relation | Probe matrix exists as blocked counters/logs; no speculative API calls are used | Blocked TECH-01 | Identify confirmed EU5 read/write APIs for country income and route profit. |
| Goods received formula | `target = sent - 0.1 * clamp(1 - trade_maintenance, 0, 1)` | Formula kernel computes target, delta, and loss quantity | Implemented | Confirm if formula is absolute loss, not percentage-of-sent; current implementation follows written spec. |
| Market-level destination loss | Remove delivery loss from destination market stockpile | Uses documented market-scope `add_goods_supply` with negative amount and route-good scope | Implemented | Needs in-game confirmation that negative amount is accepted as stockpile removal. |
| Base movement vs loss | Base add/transfer is separate from destination loss removal | Code comments and status matrix separate receipt path from loss reconciliation | Partial | Implement generated-good base receipt operators separately. |
| Four-case classification | Classify origin promoted and destination promoted | Runtime computes `modeu5_us20_origin_market_is_promoted` and `modeu5_us20_target_market_is_promoted`; counters exist for all four cases | Implemented | Deterministic fixture currently covers case 4 only. |
| Case 1: origin non-promoted / destination non-promoted | Remove loss at destination market | Branch classified; destination market loss goes through `add_goods_supply` | Partial | Add deterministic case-1 fixture and run in-game. |
| Case 2: origin promoted / destination non-promoted | Remove loss at destination market | Branch classified; destination market loss goes through `add_goods_supply` | Partial | Add deterministic case-2 fixture and run in-game. |
| Case 3: origin non-promoted / destination promoted | Add received goods at destination country-market; then remove destination market + country-stock loss | Branch classified; market loss is implemented; receiver/country loss path exists for explicit receiver + wheat fixture; base add is not implemented | Partial | Generate literal-good add-at-destination operator and test case 3. |
| Case 4: origin promoted / destination promoted | Transfer country-market to country-market; then remove destination market + country-stock loss | Branch classified; deterministic fixture asserts case 4, market loss, and country loss with explicit receiver + wheat | Partial | Generate literal-good transfer receipt operator; generic country-stock route-good dispatcher still missing. |
| Stored receiving country | If earlier transfer/demand resolution stored receiver, use it | Implemented: `scope:modeu5_us20_receiving_country` wins | Implemented | Need actual upstream storage when base movement operator is implemented. |
| Trade owner as receiver | If trade owner is present in destination market, use trade owner | Scaffolded behind `modeu5_us20_trade_owner_present_in_target_market` scope flag | Partial | Implement live presence detection against destination market country list/cache. |
| US-10 receiver fallback | Reuse/extend US-10 candidate machinery for receiver allocation | Specified; blocked counter/log when explicit receiver and trade-owner-present path are unavailable | Specified only | Build generated literal-good receiver allocator that preserves US-10 bucket/tie-break ordering. |
| Receiver thresholds | Ignore supplier protection thresholds; apply receiver eligibility before US-10 ordering | Documented only | Specified only | Add receiver profile flag or separate resolver mode that changes eligibility only. |
| Receiver capacity rule | Eligible if `current_stock < capacity`; do not clip full receipt to free capacity | Documented only | Specified only | Needs stock/capacity eligibility reads per candidate; do not introduce a lower-fill priority sort. |
| Generic good support | Apply US-20 to route good, not hard-coded wheat | Market-level loss uses saved route good; country-stock `remove_stock` fixture is still wheat-only | Partial | Generate route good -> literal-good dispatcher for country-stock removal. |
| Destination country-stock loss removal | Promoted-destination country-stock loss uses destination removal semantics, not transfer semantics | Deterministic wheat path calls `modeu5_remove_stock` with `reason = stock_loss` | Partial | Generic country-stock remove path pending literal-good dispatcher and receiver selection. |
| Debug visibility | Expose classification, blocked routes, market-loss routes, probe states, loss values | Globals/logs exist for money probe, goods block, case counters, market-loss counter, receiver-selection block | Implemented | Add UI/debug event summary if desired. |
| Test coverage | Deterministic fixture should cover formula, CMM gate, probe blocking, market loss, and country-stock loss | Fixture covers disabled gate, formula, income-probe blocking, explicit receiver, case 4, market loss, and wheat `remove_stock` loss | Partial | Add deterministic fixtures for cases 1, 2, and 3. |
| Static CI | Generated files and validation must pass | CI currently validates parser/generator/static surfaces | Implemented | Does not prove EU5 runtime execution; needs in-game debug event run. |

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
- Destination market loss uses add_goods_supply with a negative amount.
- Case 1 origin non-promoted / destination non-promoted removes loss at destination market.
- Case 2 origin promoted / destination non-promoted removes loss at destination market.
- Case 3 origin non-promoted / destination promoted adds at destination country-market, then removes destination market + country-stock loss.
- Case 4 origin promoted / destination promoted transfers country-market to country-market, then removes destination market + country-stock loss.
- Stored receiving country wins when available.
- Trade owner is selected only if present in destination market.
- If trade owner is not present, the receiver allocator extends US-10 while preserving bucket sorting and tie-break ordering.
- Receiver allocation changes eligibility thresholds only; it does not add a lower-fill priority sort.
- Receiver allocation ignores supplier-protection thresholds.
- Receiver allocation uses under-capacity eligibility but does not cap the whole receipt to free capacity for MVP.
- Country-stock goods loss uses destination removal semantics, not transfer semantics.
- #105 and #120 effects are separate in debug output.
- Missing detailed country-stock accounting is visible as fallback/block diagnostics.
- No silent money or country-stock goods adjustment occurs.
```

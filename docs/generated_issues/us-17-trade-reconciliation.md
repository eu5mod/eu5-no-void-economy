# US-17 — Trade maintenance efficiency and buying/selling efficiency in Q8.7 route loop

## Correct source mapping

The previous wording in this PR mixed up which source owns which semantic change.

Use this corrected mapping:

```txt
#105 defines the new trade maintenance efficiency model.
#120 defines the buying/selling trade efficiency model.
#161 defines where both route-level hooks belong.
```

#105 and #120 are therefore complementary. #120 does not replace #105. It defines the buying/selling efficiency side of the trade-route economics, while #105 defines the trade-maintenance-efficiency side.

## Corrected economic model

The route has two separate concepts:

```txt
Trade maintenance efficiency:
  defined by #105
  controls the new maintenance-side trade effect

Buying/selling efficiency:
  defined by #120
  controls the reinterpreted buy/sell efficiency contribution
```

The old vanilla price-side buy/sell bonus must not stack with the new ModeU5 route economics. It must be removed explicitly.

The engine result is adjusted by delta, not replaced wholesale:

```txt
final_trade_owner_income =
    engine_trade_owner_income
  + route_reconciliation_delta
```

The route delta combines the two corrected pieces:

```txt
route_reconciliation_delta =
    - old_price_side_bonus
    + new_trade_maintenance_efficiency_effect
    + new_buying_selling_efficiency_effect
```

Where:

```txt
old_price_side_bonus =
    quantity * sell_price * selling_efficiency
  + quantity * buy_price * buying_efficiency * (1 + export_cost_modifier)
```

The precise implementation of:

```txt
new_trade_maintenance_efficiency_effect
new_buying_selling_efficiency_effect
```

must follow #105 and #120 respectively.

## Q8.7 runtime placement

#161 introduces the live monthly owner split:

```txt
modeu5_monthly_stock_cycle_pulse
  -> modeu5_run_monthly_stock_cycle_q8_7_owner_switch
     -> every_market_in_world market-local pass
     -> country trade-owner pass
     -> optional audit reconciliation
```

US-17 route economics must not run inside the `every_market_in_world` market-local body.

They belong inside the country trade-owner route loop:

```txt
modeu5_run_monthly_country_trade_owner_cycle
  -> every_trade
     -> save route scopes
     -> capture route quantity
     -> apply #105 maintenance-efficiency economics
     -> apply #120 buying/selling-efficiency economics
     -> add route delta to saved trade owner
```

Required insertion point:

```txt
every_trade = {
  save_temporary_scope_as = modeu5_trade_owner_trade

  owner = { save_temporary_scope_as = modeu5_trade_owner_country }
  from_market = { save_temporary_scope_as = modeu5_trade_owner_source_market }
  to_market = { save_temporary_scope_as = modeu5_trade_owner_target_market }
  traded_goods = { save_temporary_scope_as = modeu5_trade_owner_good }

  modeu5_capture_country_trade_owner_trade_quantity = yes

  # #105 maintenance-efficiency hook
  modeu5_compute_trade_maintenance_efficiency_delta = yes

  # #120 buying/selling-efficiency hook
  modeu5_compute_buying_selling_efficiency_delta = yes

  modeu5_add_trade_efficiency_route_delta_to_trade_owner = yes
}
```

The money owner is:

```txt
scope:modeu5_trade_owner_country
```

Do not use the scheduler country, the market-center owner, or a separate market-center route pass.

## Buying/selling efficiency support values

Buying/selling efficiency should be read from the saved trade owner country.

```txt
modeu5_clamped_buying_selling_efficiency = {
  value = scope:modeu5_trade_owner_country.modifier:buying_efficiency
  add = scope:modeu5_trade_owner_country.modifier:selling_efficiency
  divide = 2

  min = 0
  max = 1
}
```

This value belongs to the #120 buy/sell efficiency side. Do not use it as a replacement for the #105 trade-maintenance-efficiency model unless the #105 specification explicitly says so.

## PERF-14 / CMM accounting rule

The route hook must still respect the PERF-14 accounting mode plumbing.

```txt
Detailed route accounting available:
  compute route-level delta in every_trade
  add route delta to saved trade owner

Detailed accounting unavailable or blocked:
  emit explicit fallback/block diagnostics
  use the approved fallback only
  do not silently drop the route economics
```

## Current PR scaffold

Current files in #107:

```txt
docs/generated_issues/us-17-trade-reconciliation.md
in_game/common/script_values/zzz_trade_reconciliation_values.txt
in_game/common/scripted_effects/zzz_trade_reconciliation_effects.txt
```

Before live implementation:

```txt
- rename zzz_* files/effects into ModeU5 naming;
- remove the old every_market_center_in_country route scaffold;
- insert route hooks into modeu5_run_monthly_country_trade_owner_cycle;
- split #105 maintenance-efficiency logic from #120 buy/sell-efficiency logic;
- replace TODO route values with confirmed script-doc values or blocked diagnostics;
- add route-level debug output;
- update TECH-01 for confirmed/blocked exposures.
```

## Debug contract

```txt
trade_owner
source_market
target_market
traded_good
quantity
sell_price
buy_price
export_cost_modifier
trade_maintenance_efficiency_inputs
buying_efficiency
selling_efficiency
clamped_buying_selling_efficiency
old_price_side_bonus
new_trade_maintenance_efficiency_effect
new_buying_selling_efficiency_effect
route_reconciliation_delta
trade_owner_accumulated_delta
accounting_mode_detailed_or_fallback
```

## Acceptance checks

```txt
- #105 is documented as the trade maintenance efficiency source.
- #120 is documented as the buying/selling trade efficiency source.
- #161 defines only the runtime insertion point.
- The route hook runs from the country trade-owner every_trade loop.
- No second every_market_center_in_country route pass is added.
- No US-17 route hook runs in the every_market_in_world market-local body.
- Old price-side buy/sell bonus is removed.
- #105 maintenance-efficiency effect and #120 buy/sell-efficiency effect remain separate in debug.
- Delta is accumulated on the saved trade owner.
- No stock-side mutation is introduced by US-17.
- PERF-14 fallback/block state is visible in diagnostics.
```

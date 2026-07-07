# US-17 — Trade-efficiency redefinition inside Q8.7 trade-owner loop

## Supersession rule

The old #105 / early #107 text is superseded by the trade-efficiency redefinition carried by #120.

Use this document as the corrected US-17 contract for this PR.

```txt
#120 defines the meaning of trade efficiency.
#161 defines where the route-level hook belongs.
```

Older wording remains useful only as historical context for the problem being solved: vanilla `buying_efficiency` and `selling_efficiency` create a price-side bonus that must not survive once ModeU5 redefines trade efficiency.

## Redefined trade-efficiency meaning

Under the corrected model, `buying_efficiency` and `selling_efficiency` are no longer treated as a direct vanilla price-side profit amplifier.

They become an explicit ModeU5 route-level reconciliation input:

```txt
buying_efficiency + selling_efficiency
  -> clamped_average_efficiency
  -> explicit trade-owner money reconciliation
```

The implementation must therefore:

```txt
1. identify the old vanilla price-side bonus;
2. remove that old bonus from the engine result;
3. add only the new ModeU5-defined money-side effect;
4. attribute the route delta to the saved trade owner.
```

The engine result is not replaced wholesale. The mod applies a delta:

```txt
final_trade_owner_income =
    engine_trade_owner_income
  + money_reconciliation_delta
```

## Q8.7 runtime placement

#161 introduces the live monthly owner split:

```txt
modeu5_monthly_stock_cycle_pulse
  -> modeu5_run_monthly_stock_cycle_q8_7_owner_switch
     -> every_market_in_world market-local pass
     -> country trade-owner pass
     -> optional audit reconciliation
```

US-17 must not run inside the `every_market_in_world` market-local body.

US-17 must run inside the country trade-owner route loop:

```txt
modeu5_run_monthly_country_trade_owner_cycle
  -> every_trade
     -> save route scopes
     -> capture route quantity
     -> compute US-17 money reconciliation
     -> add delta to saved trade owner
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

  # US-17 starts here
  modeu5_compute_us17_trade_efficiency_money_delta = yes
  modeu5_add_us17_money_delta_to_trade_owner = yes
}
```

The money owner is:

```txt
scope:modeu5_trade_owner_country
```

Do not use the scheduler country, the market-center owner, or a separate market-center route pass.

## Money-side formula

The old bonus to remove remains the vanilla price-side bonus:

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
modeu5_us17_clamped_average_efficiency = {
  value = scope:modeu5_trade_owner_country.modifier:buying_efficiency
  add = scope:modeu5_trade_owner_country.modifier:selling_efficiency
  divide = 2

  min = 0
  max = 1
}
```

US-17 money delta:

```txt
money_reconciliation_delta =
    - old_price_side_bonus
    + modeu5_trade_efficiency_money_effect
```

`modeu5_trade_efficiency_money_effect` is the #120-defined replacement effect. Do not revert to pre-#120 assumptions unless #120 explicitly says so.

## PERF-14 / CMM accounting rule

US-17 must respect #120 accounting decisions.

```txt
Detailed route accounting available:
  compute route-level money delta in every_trade
  add route delta to saved trade owner

Detailed accounting unavailable or blocked:
  emit explicit fallback/block diagnostics
  use the approved fallback only
  do not silently drop the trade-efficiency redefinition
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
- rename zzz_* files/effects into modeu5_us17_* naming;
- remove the old every_market_center_in_country route scaffold;
- insert the US-17 hook into modeu5_run_monthly_country_trade_owner_cycle;
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
buying_efficiency
selling_efficiency
clamped_average_efficiency
old_price_side_bonus
modeu5_trade_efficiency_money_effect
money_reconciliation_delta
trade_owner_accumulated_delta
accounting_mode_detailed_or_fallback
```

## Acceptance checks

```txt
- #120 trade-efficiency redefinition supersedes old #105/#107 wording.
- #161 defines only the runtime insertion point.
- US-17 runs from the country trade-owner every_trade loop.
- US-17 does not add a second every_market_center_in_country route pass.
- US-17 does not run in the every_market_in_world market-local body.
- Old price-side bonus is removed.
- New ModeU5 trade-efficiency money effect is added.
- Delta is accumulated on the saved trade owner.
- No stock-side mutation is introduced by US-17.
- PERF-14 fallback/block state is visible in diagnostics.
```

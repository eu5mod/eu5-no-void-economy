# US-17 — Trade-efficiency reconciliation inside Q8.7 trade-owner loop

## Status of older text

The old #105 / early #107 wording is superseded by the PERF-14 / CMM accounting-mode baseline from #120.

Keep from the older story only the business goal:

```txt
remove the old price-side buying/selling efficiency bonus
and replace it with an explicit reconciliation effect
```

Do not keep the old runtime shape:

```txt
every_market_center_in_country -> every_trade
```

Do not keep old comments that say positive efficiency increases maintenance. Positive efficiency is beneficial.

## Authoritative runtime baseline

#120 establishes the CMM / Performance Mode accounting baseline:

```txt
- main mode is resolved by parser-safe runtime helpers;
- Performance Mode discovers human-relevant markets;
- detailed accounting is gated by accounting-mode decisions;
- skipped detailed work must use an explicit fallback path, not silently disappear;
- PERF-14 probes are read-only unless a later PR wires mutation through the gate.
```

#161 then changes the live monthly owner shape:

```txt
modeu5_monthly_stock_cycle_pulse
  -> modeu5_run_monthly_stock_cycle_q8_7_owner_switch
     -> once-per-month market-local owner pass
     -> country trade-owner pass
     -> optional audit reconciliation
```

The market-local owner pass is:

```txt
modeu5_run_monthly_q8_7_global_market_local_cycle_once
  -> every_market_in_world
     -> modeu5_prepare_market_runtime_accounting_mode
     -> modeu5_run_promoted_market_live_local_branch_market_all_goods
```

US-17 must not run in that `every_market_in_world` body. That body is for market-local stock and demand processing.

## Correct US-17 insertion point

US-17 belongs inside the #161 country trade-owner route loop:

```txt
modeu5_run_monthly_country_trade_owner_cycle
  -> every_trade
     -> save trade route scopes
     -> capture route quantity
     -> US-17 route reconciliation
```

Required local shape:

```txt
modeu5_run_monthly_country_trade_owner_cycle = {
  save_temporary_scope_as = modeu5_trade_owner_controller_country
  modeu5_note_country_trade_owner_pass_run = yes

  every_trade = {
    save_temporary_scope_as = modeu5_trade_owner_trade
    modeu5_note_country_trade_owner_trade_seen = yes

    owner = { save_temporary_scope_as = modeu5_trade_owner_country }
    from_market = { save_temporary_scope_as = modeu5_trade_owner_source_market }
    to_market = { save_temporary_scope_as = modeu5_trade_owner_target_market }
    traded_goods = { save_temporary_scope_as = modeu5_trade_owner_good }

    modeu5_capture_country_trade_owner_trade_quantity = yes

    # US-17 hook
    modeu5_compute_us17_trade_efficiency_delta = yes
    modeu5_add_us17_trade_efficiency_delta_to_trade_owner = yes

    modeu5_note_country_trade_owner_inter_market_trade = yes
  }
}
```

The route owner is:

```txt
scope:modeu5_trade_owner_country
```

not the scheduler country and not the market-center owner.

## Business formula

The engine is assumed to have already calculated vanilla trade income. US-17 therefore applies a delta:

```txt
final_trade_owner_income =
    engine_trade_owner_income
  + reconciliation_delta
```

The old price-side bonus to remove is:

```txt
old_price_side_bonus =
    quantity * sell_price * selling_efficiency
  + quantity * buy_price * buying_efficiency * (1 + export_cost_modifier)
```

Average efficiency is clamped:

```txt
clamped_average_efficiency =
    clamp((buying_efficiency + selling_efficiency) / 2, 0, 1)
```

EU5 value syntax should use bounds:

```txt
modeu5_us17_clamped_average_efficiency = {
  value = scope:modeu5_trade_owner_country.modifier:buying_efficiency
  add = scope:modeu5_trade_owner_country.modifier:selling_efficiency
  divide = 2

  min = 0
  max = 1
}
```

US-17 maintenance-side saving:

```txt
new_maintenance_saving =
    current_trade_maintenance
  * clamped_average_efficiency
```

Route reconciliation:

```txt
reconciliation_delta =
    - old_price_side_bonus
    + new_maintenance_saving
```

## PERF-14 / Performance Mode rule

US-17 must respect #120 accounting decisions.

```txt
Detailed route accounting available:
  calculate route-level delta inside every_trade
  add money delta to scope:modeu5_trade_owner_country

Detailed route accounting unavailable / blocked:
  emit blocked or fallback diagnostics
  use only the approved fallback path
  do not silently skip the economic effect
```

If a direct formula override is later confirmed, do not also apply the delta fallback.

## Current PR scaffold

Current files in #107:

```txt
docs/generated_issues/us-17-trade-reconciliation.md
in_game/common/script_values/zzz_trade_reconciliation_values.txt
in_game/common/scripted_effects/zzz_trade_reconciliation_effects.txt
```

Before making this live:

```txt
- rename zzz_* files/effects into modeu5_us17_* naming;
- remove the old market-center route loop scaffold;
- insert the US-17 hook into modeu5_run_monthly_country_trade_owner_cycle;
- replace TODO trade price / quantity / maintenance values with confirmed exposure or blocked diagnostics;
- add route-level debug output;
- update TECH-01 for each confirmed or blocked exposure.
```

## Debug contract

Route debug should include:

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
current_trade_maintenance
new_maintenance_saving
reconciliation_delta
trade_owner_accumulated_delta
accounting_mode_detailed_or_fallback
```

## Acceptance checks

```txt
- US-17 runs from the country trade-owner every_trade loop.
- US-17 does not add a second every_market_center_in_country route pass.
- US-17 does not run in the every_market_in_world market-local body.
- Positive efficiency reduces/offsets cost through the approved money reconciliation.
- Old price-side bonus is removed.
- Delta is accumulated on the saved trade owner.
- No stock mutation is introduced by US-17.
- PERF-14 blocked/fallback accounting emits diagnostics.
- error.log has no new blocking diagnostics.
```

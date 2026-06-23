EU5 trade reconciliation generated files
=======================================

Purpose
-------
These files implement a reconciliation approach for the transition from the old price-side buying/selling efficiency formula to a new maintenance-side formula.

Core idea
---------
The game/engine is assumed to already pay the old trade income:

  engine_income = old_formula_profit

The mod calculates and applies only the difference:

  correction = new_formula_profit - old_formula_profit
  final_income = engine_income + correction

This is important: do NOT replace income with new - old. Add the delta to the country/trade_owner after the normal engine result.

Your intended new formula
-------------------------

  trade_maintenance =
      base_trade_maintenance
    * (1 + trade_maintenance_modifier)
    * (1 - min(1, max(0, (buying_efficiency + selling_efficiency) / 2)))

This means positive buying/selling efficiency increases maintenance. If instead you want positive efficiency to reduce maintenance, change the sign in zzz_trade_reconciliation_delta.txt where marked.

File map
--------

1. common/script_values/zzz_trade_reconciliation_values.txt
   Contains the actual math:
   - trade_owner average efficiency
   - old price-side bonus to nullify
   - current maintenance
   - new extra maintenance cost
   - final reconciliation delta

2. common/scripted_effects/zzz_trade_reconciliation_effects.txt
   Contains effects to:
   - reset reconciliation variables
   - loop every_market_center_in_country -> every_trade
   - aggregate delta onto trade_owner
   - apply/consume the delta

3. common/static_modifiers/zzz_trade_reconciliation_static_modifiers.txt
   Optional placeholder static modifier if you choose to apply the delta through a country modifier rather than direct income/treasury scripting.

Important TODOs
---------------
The public wiki does not expose the exact trade-scope script value names for all required route values. Search your generated script_docs for these and replace the TODO_* names:

  TODO_trade_goods_quantity
  TODO_trade_sell_price
  TODO_trade_buy_price
  TODO_trade_export_cost_modifier
  TODO_trade_base_maintenance
  TODO_trade_maintenance_modifier

Also replace the final delta application hook in the scripted effect:

  TODO_apply_delta_to_trade_owner_income_or_treasury

Recommended integration
-----------------------
Run the reconciliation effect wherever your previous every_market_center_in_country / every_trade loop runs, after normal trade income has been computed or immediately before your mod's income settlement tick.


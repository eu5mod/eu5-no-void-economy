# DEBUG CONVENTIONS — ModeU5

## Purpose

ModeU5 must be testable without relying on a complete custom UI.

Every feature must expose enough debug information to validate:

```txt
which scope was used
which quantities were calculated
which mutation effect was called
which values changed
whether the stock invariant still holds
whether a fallback was used
whether an economic reconciliation was applied
```

## Debug naming convention

Use the prefix:

```txt
modeu5_debug_
```

Examples:

```txt
modeu5_debug_last_country
modeu5_debug_last_market
modeu5_debug_last_good
modeu5_debug_last_quantity_added
modeu5_debug_last_quantity_removed
modeu5_debug_last_rejected_quantity
modeu5_debug_last_unsatisfied_quantity
modeu5_debug_last_transferred_quantity
modeu5_debug_last_stock_difference
modeu5_debug_last_inconsistency_detected
modeu5_debug_last_fallback_used
modeu5_debug_last_imputation_mode
```

## Debug output levels

| Level | Use |
|---|---|
| OFF | No debug output. |
| BASIC | Key stock, void-economy, and reconciliation values only. |
| VERBOSE | Candidate lists, excluded scopes, formulas, fallbacks, payer decisions. |
| TEST | Deterministic values for manual tests. |

Recommended variable:

```txt
modeu5_debug_level
```

## Mandatory debug per stock mutation

Every call to a centralized stock mutation effect must expose:

```txt
operation
country
market
good
quantity_requested
quantity_actual
quantity_rejected_or_unsatisfied
country_stock_before
country_stock_after
market_stock_before
market_stock_after
country_stock_cap
available_capacity
stock_difference_after
mutation_effect_called
```

For `modeu5_transfer_stock`, debug must also expose:

```txt
seller_country
buyer_country
source_market
target_market
seller_stock_before
seller_stock_after
buyer_stock_before
buyer_stock_after
source_market_stock_before
source_market_stock_after
target_market_stock_before
target_market_stock_after
transferred_quantity
rejected_or_unsatisfied_quantity
same_market_transfer
inter_market_transfer
```

## Mandatory debug for US-00

For each `country × market × good`, expose:

```txt
country
market
good
produced_quantity
actual_added_quantity
rejected_quantity
available_capacity_when_added_if_available
ledger_update_source
overproduction_ratio
target_overproduction_buffer
effective_overproduction_ratio
production_efficiency_penalty_coefficient
max_production_efficiency_penalty
production_efficiency_penalty
modifier_application_mode
affected_locations_count
fallback_used
theoretical_only_if_applicable
good_price
good_price_source
void_income_penalty_coefficient
void_wealth_tracked
void_taxable_income_proxy
```

Aggregates:

```txt
modeu5_void_wealth_by_market[market]
modeu5_total_void_wealth
```

Allowed `modifier_application_mode` values:

```txt
good_specific_local_output_modifier
local_production_efficiency_modifier
theoretical_only
```

## Mandatory debug for US-04

For each `location × good`, expose:

```txt
location
good
base_location_pop_good_demand
location_good_demand_multiplier
mod_location_pop_good_demand
requested_quantity
satisfied_quantity
unsatisfied_quantity
satisfaction_ratio
satisfaction_threshold
months_satisfied_current_year
months_unsatisfied_current_year
previous_demand_multiplier
new_demand_multiplier
annual_adjustment_applied
```

## Mandatory debug for US-05 / US-05.1

For each affected slider:

```txt
country
slider_name
vanilla_slider_cost
modeu5_slider_cost_base
modeu5_total_void_wealth_if_correction_enabled
modeu5_corrected_slider_cost_base_if_applicable
modeu5_target_slider_cost
modeu5_slider_reconciliation
net_effective_slider_cost
correction_mode
ui_display_mode
```

Allowed `correction_mode` values:

```txt
direct_slider_base_replacement
monthly_reconciliation
debug_only
not_enabled
```

## Mandatory debug for US-10

For every call to `modeu5_resolve_stock_demand`, expose:

```txt
demand_type
demanding_country
buyer_country_if_applicable
consumer_type_if_consumption
consumer_scope_if_consumption
location_if_applicable
market
source_market_if_trade
target_market_if_trade
good
requested_quantity
ordered_stock_candidates
stock_priority_score_by_candidate
excluded_candidates
exclusion_reason_by_candidate
total_available_candidate_stock
```

For consumption resolution, expose:

```txt
quantity_taken_by_candidate
satisfied_quantity
unsatisfied_quantity
is_intra_market_trade = no
trade_income_generated = no
transport_cost_generated = no
trade_capacity_used = no
```

For inter-market transfer, expose:

```txt
quantity_transferred_by_candidate
transferred_quantity
unsatisfied_trade_quantity
buyer_available_capacity
exposed_to_us_06 = yes/no
```

Standard exclusion reasons:

```txt
at_war_not_allowed
embargoed_stock_not_allowed
no_valid_market_access
foreign_stocks_not_allowed
subject_stocks_not_allowed
market_owner_stock_not_allowed
stock_below_minimum_threshold
wrong_market
wrong_good
```

## Mandatory debug for US-06

For each inspected trade/import/export scope:

```txt
month
scope_type
trade_owner
buyer_country
seller_country
from_market
to_market
traded_goods
used_trade_capacity
trade_distance
trade_range
cost_basis_quantity
gross_trade_income_if_available
modeu5_transport_cost
transport_cost_payer
imputation_mode
missing_trade_data
```

Monthly aggregate debug:

```txt
country
monthly_trade_count_inspected
monthly_import_count_inspected
monthly_export_count_inspected
monthly_transport_cost_total
monthly_trade_income_reconciliation
effective_trade_income_estimate
ui_display_mode
```

Allowed `imputation_mode` values:

```txt
direct_trade_income_reduction
monthly_reconciliation
skipped_missing_data
```

Allowed `ui_display_mode` values:

```txt
vanilla_trade_tooltip
country_modifier
debug_window
custom_modeu5_window
monthly_report
```

## Fallback debug

If a fallback is used, debug must show:

```txt
fallback_used = yes
fallback_reason
missing_scope_or_value
fallback_method
fallback_scope
TECH_01_entry_id
```

Fallbacks must not be silent.

## Do not hide reconciliation

Any economic correction must be visible in at least one of:

```txt
debug event
country modifier tooltip
monthly report
custom ModeU5 window
vanilla tooltip if safely overridable
```

This applies to:

```txt
US-05 slider reconciliation
US-05.1 void-wealth exclusion if enabled
US-06 trade-income reconciliation
US-00 theoretical-only production penalties
```

## Error policy

If a negative stock is detected:

```txt
1. clamp to zero
2. log anomaly
3. validate market stock
4. do not allow negative value to persist
```

If market stock differs from country stock sum:

```txt
1. calculate expected market stock
2. overwrite market stock with expected value
3. log market, good, previous value, corrected value, difference
4. do not modify country stocks
```

If a trade/import/export scope lacks required data:

```txt
1. record missing_trade_data
2. skip or use the one accepted fallback
3. update TECH-01
4. do not apply silent costs
```

If a modifier or effect is unconfirmed:

```txt
1. keep the calculation debug-only or theoretical-only
2. do not apply gameplay effect
3. update TECH-01
```

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
whether an economic adjustment was applied
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
modeu5_debug_last_economic_base
```

## Debug output levels

| Level | Use |
|---|---|
| OFF | No debug output. |
| BASIC | Key stock, void-economy, and Economic Base values only. |
| VERBOSE | Candidate lists, excluded scopes, formulas, fallbacks, and affected calculations. |
| TEST | Deterministic values for manual tests. |

Recommended variable:

```txt
modeu5_debug_level
```

## Mandatory package diagnostics

At startup and in the general diagnostic event, expose:

```txt
modeu5_core_package_loaded = yes
modeu5_core_package_version
modeu5_economy_rebalance_loaded
modeu5_economy_package_version_if_loaded
modeu5_trade_rebalance_loaded
modeu5_trade_package_version_if_loaded
modeu5_war_rebalance_loaded
modeu5_war_package_version_if_loaded
package_version_mismatch
missing_required_core
package_selection_changed_since_save_if_detectable
```

Optional feature debug must include its package state. It must never report an optional effect as active when the companion package is absent.

For local development, each installed package also contains
`MODEU5_SOURCE.txt`. Inspect it before reading runtime diagnostics to confirm
that EU5 is loading the intended branch and commit.

## Pre-campaign debug configuration

`modeu5_debug_level` is selected through EU5's built-in Game Rules screen before the campaign starts:

```txt
Off = 0
Basic = 1
Verbose = 2
```

The startup configuration effect copies the selected rule to the global debug-level variable. Package state remains owned by the launcher/mod playset and startup package markers.

There is no custom in-game configuration panel. Diagnostics, rebuilds, and validation are invoked only through their dedicated debug/test flows and must never reseed stocks implicitly.

## Mandatory debug for CORE-02 startup

Global startup debug:

```txt
startup_hook
startup_delay_days
initialization_state_before
initialization_mode
schema_version_before
schema_version_target
existing_country_stock_detected
existing_market_cache_detected
opening_source_available
monthly_gameplay_enabled
initialization_state_after
blocking_failure
```

For each market x good:

```txt
market
good
opening_quantity_source
opening_source_quantity
total_modeu5_capacity
opening_target_quantity
eligible_country_count
allocated_quantity
opening_allocation_difference
over_capacity_country_count
total_over_capacity_quantity
rounding_residue_before
rounding_residue_after
market_stock_after
stock_difference_after
rebuild_called
validation_passed
```

For each positive country allocation:

```txt
country
market
good
country_capacity
capacity_share
requested_initial_quantity
actual_initial_quantity
capacity_policy = allow_over_capacity
over_capacity_before
over_capacity_after
over_capacity_created
stock_before
stock_after
mutation_effect_called = modeu5_add_stock
```

Startup must allocate the full opening source. Over-cap quantities must be labeled separately from `rejected_quantity` and `void_wealth`. A positive source with zero total capacity is a blocking `zero_total_capacity` allocation error, not truncation.

## Mandatory debug for CORE-03 succession

For each permanent location ownership change and good:

```txt
lifecycle_event
location
market
good
loser_country
winner_country
loser_stock_before
loser_capacity_before
transferred_location_capacity
transfer_ratio
requested_stock_transfer
actual_stock_transfer
target_capacity_policy = allow_over_capacity
loser_capacity_after
winner_capacity_after
winner_over_capacity_before
winner_over_capacity_after
over_capacity_created
loser_stock_after
winner_stock_after
market_stock_before
market_stock_after
stock_difference_after
mutation_effect_called = modeu5_transfer_stock
duplicate_transfer_prevented
```

For country creation or annexation finalization:

```txt
lifecycle_finalizer
country
predecessor_or_target
affected_market_good_count
residual_stock_before
residual_stock_transferred
target_capacity_policy = allow_over_capacity
winner_over_capacity_after
rebuild_called
validation_passed
```

Succession transfers must explicitly show:

```txt
trade_income_generated = no
transport_cost_generated = no
trade_capacity_used = no
rejected_production_recorded = no
unsatisfied_demand_recorded = no
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
capacity_policy
over_capacity_before
over_capacity_after
over_capacity_created
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
target_capacity_policy
same_market_transfer
inter_market_transfer
```

For `modeu5_rebuild_market_stock_from_country_stocks`, debug must expose:

```txt
operation = rebuild_market_stock
market
good
market_stock_before
expected_market_stock
market_stock_after
correction_applied
country_source_count
negative_country_source_detected
country_stocks_modified = no
```

For `modeu5_validate_stock_consistency`, debug must expose:

```txt
operation = validate_stock_consistency
market
good
expected_market_stock
actual_market_stock_before
stock_difference_before
inconsistency_detected
inconsistency_severity
rebuild_called
actual_market_stock_after
stock_difference_after
negative_country_source_detected
over_cap_country_source_detected
over_cap_is_accounting_inconsistency = no
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

## Mandatory debug for US-05

For each affected slider:

```txt
country
slider_name
wealth_input
wealth_source
monthly_trade_income
modeu5_slider_cost_base
formula_replacement_active
affected_formula_call_site
ui_display_mode
```

Allowed `formula_replacement_active` values:

```txt
yes
no_unconfirmed_wealth_value
no_unconfirmed_formula_hook
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

## Do not hide economic adjustments

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
US-00 theoretical-only production penalties
US-04 simulated-demand fallback
US-05 direct formula replacement status
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

If a modifier or effect is unconfirmed:

```txt
1. keep the calculation debug-only or theoretical-only
2. do not apply gameplay effect
3. update TECH-01
```

# TECH-01 — Engine Exposure Matrix

## Purpose

This document tracks whether ModeU5 can rely on a vanilla EU5 scope, scope link, value, trigger, effect, modifier, on_action, or static file field.

No implementation depending on vanilla exposure should proceed until the relevant entry is marked:

```txt
CONFIRMED
FALLBACK_ACCEPTED
OUT_OF_SCOPE
```

## Status values

| Status | Meaning |
|---|---|
| TO_TEST | Need identified, not verified yet. |
| CONFIRMED | Verified in wiki, script docs, vanilla files, or local test. |
| NOT_CONFIRMED | Searched but not found. |
| FALLBACK_ACCEPTED | Not exposed or unreliable, but one fallback has been accepted. |
| OUT_OF_SCOPE | Not required for MVP. |

## Required sources to check

```txt
https://eu5.paradoxwikis.com/Scope_link
https://eu5.paradoxwikis.com/Variable
https://eu5.paradoxwikis.com/Trigger
https://eu5.paradoxwikis.com/Effect
https://eu5.paradoxwikis.com/Modifier_types
https://eu5.paradoxwikis.com/Building_modding
https://eu5.paradoxwikis.com/Goods_modding
local vanilla files
local script_docs output
error.log after test
```

## Wiki audit — 2026-06-13

The seven wiki pages listed above were reviewed for every matrix entry that was still marked `TO_CHECK` or `TO_TEST`.

- `CONFIRMED` means the required exposure and the exact method named in the row are documented by at least one of those pages.
- `NOT_CONFIRMED` means the exact required exposure was not documented by those pages. Adjacent or partial APIs are recorded in the notes but do not satisfy the row.
- Wiki confirmation does not replace a local script-docs check and controlled `error.log` test before gameplay implementation.
- A wiki `NOT_CONFIRMED` result is not proof that the engine lacks the exposure; it remains blocked until local vanilla files, local script docs, or a controlled test confirm it, or one fallback is accepted.

## Matrix

| ID | US | Need | Expected scope | Candidate exposure | Type | Source checked | Status | Fallback decision | Test / notes |
|---:|---|---|---|---|---|---|---|---|---|
| 001 | Core | Iterate all countries | none → country | `every_country` | effect iterator | Wiki: Effect | CONFIRMED | N/A | Exact syntax: `every_country = { limit = { ... } ... }`. |
| 002 | Core | Iterate all markets | none → market | `every_market_in_world` | effect iterator | Wiki: Effect | CONFIRMED | N/A | The documented name is `every_market_in_world`, not `every_market`. Needed for annual validation/rebuild. |
| 003 | Core | Iterate owned locations of a country | country → location | `every_owned_location` | effect iterator | Wiki: Effect | CONFIRMED | N/A | Exact iterator is documented on country scope. |
| 004 | Core | Identify a location's market | location → market | `market` | scope link | Wiki: Scope link | CONFIRMED | N/A | `market` links a location to its market. |
| 005 | Core | Identify location owner | location → country | `owner` | scope link | Wiki: Scope link | CONFIRMED | N/A | `owner` accepts location scope and returns country. |
| 006 | Core | Iterate or identify goods | none → goods | `every_goods` | effect iterator | Wiki: Effect; Goods modding | CONFIRMED | N/A | `every_goods` iterates all goods types; static goods are in `in_game/common/goods`. |
| 007 | Core | Store variables by country × market × good | scoped object with market key and per-good map name | `add_to_variable_map`, <code>variable_map(name&#124;key)</code>, `remove_from_variable_map`, `clear_variable_map` | variable map | Wiki: Variable; Effect | CONFIRMED | N/A | A country-scoped, per-good map keyed by market can represent country × market × good. Existing keys are not overwritten: remove then re-add when updating. |
| 008 | Core | Save and reuse country/market/good scopes in effects | current effect scope | `save_scope_as`, `save_temporary_scope_as`, `clear_saved_scope` | scope handling | Wiki: Effect; Variable | CONFIRMED | N/A | `save_scope_as` survives an unbroken event chain; temporary scopes last for the current effect. |
| 009 | Core | Apply temporary country modifier | country | `add_country_modifier` | effect | Wiki: Effect | CONFIRMED | N/A | Supports duration, mode, dynamic `size`, description localization, and immediate recalculation. |
| 010 | Core | Apply temporary location modifier | location | `add_location_modifier` / generic location modifier effect | effect | All 7 wiki pages | NOT_CONFIRMED | Theoretical-only production penalty | Location modifier types are documented, but the reviewed Effect page documents no effect that dynamically adds one to a location. |
| 011 | Core | Monthly on_action | global | recurring monthly on_action | on_action | All 7 wiki pages | NOT_CONFIRMED | event pulse if available | `trigger_event_silently` can invoke a named on_action or delayed event, but no recurring monthly hook/name is documented on the reviewed pages. |
| 012 | Core | Yearly on_action | global | recurring yearly on_action | on_action | All 7 wiki pages | NOT_CONFIRMED | event pulse if available | No recurring yearly hook/name is documented on the reviewed pages. |
| 013 | Core | Fire debug/test events | effect scope | `trigger_event_silently`, `trigger_event_non_silently` | event effect | Wiki: Effect | CONFIRMED | N/A | Supports event IDs, named on_actions, and optional day/month/year delay. `debug_log`, `error_log`, and `test_log` are also documented. |
| 014 | Core | Localization for modifiers/tooltips | effect/modifier/static object | `custom_tooltip`, modifier `desc`, object `<key>` / `<key>_desc` | localization hook | Wiki: Effect; Building modding; Goods modding | CONFIRMED | N/A | The pages document localization-key hooks. Exact project localization file paths still need local validation. |
| 015 | US-01 | Current country stock in market for good | ModeU5 | country_market_good_stock | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 016 | US-01 | Market stock for good | ModeU5 | market_good_stock | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 017 | US-01 | Country stock capacity | ModeU5 | country_market_good_stock_cap | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 018 | US-01 | Available stock capacity | ModeU5 | stock_cap - stock | internal scripted value | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 019 | US-11 | Rebuild market stock from country stocks | ModeU5 | modeu5_rebuild_market_stock_from_country_stocks | internal effect | ModeU5 | CONFIRMED | N/A | Must not modify country stocks. |
| 020 | US-11 | Validate stock consistency | ModeU5 | modeu5_validate_stock_consistency | internal effect | ModeU5 | CONFIRMED | N/A | Corrects market aggregate only. |
| 021 | US-00.1 | Read production quantity at its source and attribute it to the ledger key | production source × location × good, then credited country × location market × good | `goods_output`, `raw_material_output`, `produced_in_country`, `produced_in_market` | value / production integration output | Wiki: Scope link; Trigger; Building modding | NOT_CONFIRMED | One explicit source-level production estimate if no reliable value is exposed | Location totals and country/market aggregates are documented, but no exact building/RGO source quantity plus credited-country attribution is documented. Compute from country × market × location only after 081 is resolved. |
| 022 | US-00.1 | Actual quantity added to stock | ModeU5 | modeu5_add_stock output | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 023 | US-00.1 | Rejected quantity | ModeU5 | quantity_to_add - actual_added_quantity | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 024 | US-00.1 | Ledger helper | ModeU5 | modeu5_update_production_rejection_ledger | internal effect | ModeU5 | CONFIRMED | N/A | Must be used for all ledger writes. |
| 025 | US-00.1 | Store and read a monthly ledger keyed by country × market × good | country-scoped per-good map keyed by market | `add_to_variable_map`, <code>variable_map(name&#124;key)</code>, `remove_from_variable_map`, `clear_variable_map` | variable storage and keying | Wiki: Variable; Effect | CONFIRMED | N/A | Build and update the ledger monthly. Existing map keys require remove then re-add; clear only after all monthly consumers run. Do not reconstruct it from final stock snapshots. |
| 026 | US-00.2 | Calculate ratios with division/min/max | scripted effect/value | `change_variable` operations `divide`, `min`, `max` | scripted math | Wiki: Variable; Effect | CONFIRMED | N/A | `change_variable` documents add/subtract/multiply/divide/modulo/min/max. Script must guard `produced <= 0` before division. |
| 027 | US-00.3 | Good-specific local output modifier | location, one generated modifier per good | `local_<good>_output_modifier` | modifier | Wiki: Goods modding; Modifier types | CONFIRMED | N/A | Goods modding defines the generated pattern; concrete entries such as `local_iron_output_modifier` are listed. Applying it dynamically remains blocked by 010. |
| 028 | US-00.3 | Local production efficiency modifier | location | `local_production_efficiency` | modifier | Wiki: Modifier types | CONFIRMED | N/A | Exact location modifier, percent-good format. Applying it dynamically remains blocked by 010 and it affects all local goods. |
| 029 | US-00.3 | Identify affected production sources/locations producing the good | building/location/production method/goods | `every_buildings_in_location`, `building_produced_goods`, `every_production_method_of_building`, `produced_goods`, location `raw_material` | iterator/trigger/scope link | Wiki: Effect; Trigger; Scope link | CONFIRMED | N/A | These APIs identify producing buildings, production methods, and RGO goods. Credited-country consistency still depends on 081. |
| 030 | US-00.4 | Good price for void wealth | market × good | `market_price`; fallback `default_price` / `default_market_price` | value/static field | Wiki: Scope link; Trigger; Goods modding | CONFIRMED | N/A | `market_price` is exposed on market for scoped goods; `default_market_price` is the static goods field. Log `good_price_source`. |
| 031 | US-00.4 | Estate tax base for proxy sizing | country or estate | `estate_tax_base` | value/trigger | Wiki: Scope link; Trigger | CONFIRMED | N/A | Correct documented name is `estate_tax_base`, not `estate_taxable_income`. Optional proxy only; not the primary punishment. |
| 032 | US-00.4 | Estate tax percentage for proxy sizing | country | `estate_tax_percentage` | value/trigger | Wiki: Scope link; Trigger | CONFIRMED | N/A | Correct documented name is `estate_tax_percentage`, not `estate_tax`. |
| 033 | US-02 | Count owned locations in market | country → location → market | `every_owned_location` plus location `market` | iterator/scope link | Wiki: Effect; Scope link | CONFIRMED | N/A | Iterate country-owned locations and retain those whose `market` equals the target market. |
| 034 | US-02 | Buildings in location | location → building | `every_buildings_in_location` | effect iterator | Wiki: Effect | CONFIRMED | N/A | Exact iterator is documented. |
| 035 | US-02 | Foreign buildings in location | location → building | `every_foreign_buildings_in_location` | effect iterator | Wiki: Effect; Building modding | CONFIRMED | N/A | Building modding also documents `is_foreign = yes` and distinguishes building owner from location owner. |
| 036 | US-03 | Monthly decay pulse | global | recurring monthly on_action | on_action | All 7 wiki pages | NOT_CONFIRMED | debug event pulse | Same unresolved recurring hook as 011. |
| 037 | US-04 | Local Pop demand for good | location × good | runtime vanilla Pop demand value | value | Wiki: Goods modding; Trigger; Scope link | NOT_CONFIRMED | Simulated demand | `pop_demand`, `demand_add`, and `demand_multiply` are documented as static definitions, but no runtime location × good Pop-demand value is documented. |
| 038 | US-04 | Population by type in location | location | `num_pop_type`, `percentage_pop_type_in_location` | value/trigger | Wiki: Scope link; Trigger | CONFIRMED | N/A | Both exact location values are documented. |
| 039 | US-04 | Apply a local demand modifier to vanilla demand | location × good × Pop context | local dynamic Pop-demand modifier/effect | modifier/effect | Wiki: Goods modding; Modifier types; Effect | NOT_CONFIRMED | Simulated demand only | Static `pop_demand` script values and country-wide `global_<good>_pop_demand` modifiers exist, but no local location × good runtime modifier/application effect is documented. |
| 040 | US-04 | Track yearly satisfied/unsatisfied months | location/good | variables | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 041 | US-05 | Read the vanilla Stability/Court slider cost | country/slider | readable slider cost value | value | Wiki: Modifier types; Trigger; Scope link | NOT_CONFIRMED | reconciliation modifier / debug only | `stability_cost` and `court_spending_cost_modifier` modifier types are documented, but no readable current slider-cost value is documented. |
| 042 | US-05 | Monthly trade income | country | `monthly_trade_income` | value/trigger | Wiki: Trigger | CONFIRMED | N/A | Exact country value/trigger is documented. `monthly_income_trade_and_tax` is a separate broader value. |
| 043 | US-05 | Country wealth | country | country `wealth` / location wealth aggregate | value | All 7 wiki pages | NOT_CONFIRMED | ModeU5 reconstructed/estimated wealth | `wealth_impact_threshold` is a static goods-demand field, not a readable country-wealth value. |
| 044 | US-05 | Directly replace slider cost base | country/slider | slider cost-base script or replacement effect | static/scripted value | All 7 wiki pages | NOT_CONFIRMED | monthly reconciliation | Cost modifiers are listed, but no replacement hook for the Wealth + Trade Income base is documented. |
| 045 | US-05 | Apply visible reconciliation | country/UI | `add_country_modifier` with `monthly_gold_expense` or `add_gold` plus a visible presentation | effect/modifier/UI | Wiki: Effect; Modifier types | NOT_CONFIRMED | debug-only if no safe visible effect | The economic effects are documented, but the reviewed pages do not confirm that the reconciliation amount can be exposed visibly to the player. |
| 046 | US-05.1 | Subtract void wealth from slider base | country | modeu5_total_void_wealth | internal variable | ModeU5 | CONFIRMED | N/A | Optional/MVP+ unless needed to avoid double penalty. |
| 047 | US-06 | Iterate trades | country → trade | `every_trade`, `ordered_trade` | iterator | Wiki: Effect | CONFIRMED | N/A | Both iterators are documented on country scope. |
| 048 | US-06 | Iterate imports | market → trade | `every_import`, `ordered_import` | iterator | Wiki: Effect | CONFIRMED | N/A | Both iterators are documented on market scope. |
| 049 | US-06 | Iterate exports | market → trade | `every_export`, `ordered_export` | iterator | Wiki: Effect | CONFIRMED | N/A | Both iterators are documented on market scope. |
| 050 | US-06 | Trade income recipient | trade | `trade_income_recipient` | scope link/value | All 7 wiki pages | NOT_CONFIRMED | trade owner, buyer country, current scope | No exact recipient link/value is documented. Payer priority #1 remains unresolved. |
| 051 | US-06 | Trade owner | trade → country | `owner` | scope link | Wiki: Scope link | CONFIRMED | N/A | `owner` accepts trade scope and returns country. The alias `trade_owner` is not documented. |
| 052 | US-06 | Buyer country | trade | `buyer_country` | scope link | All 7 wiki pages | NOT_CONFIRMED | current country scope | No exact buyer-country link is documented. |
| 053 | US-06 | Seller country | trade | `seller_country` | scope link | All 7 wiki pages | NOT_CONFIRMED | Debug only | No exact seller-country link is documented. |
| 054 | US-06 | Trade from/to markets | trade → market | `from_market`, `to_market` | scope links | Wiki: Scope link | CONFIRMED | N/A | Both exact trade scope links are documented. |
| 055 | US-06 | Traded good | trade → goods | `traded_goods` | scope link | Wiki: Scope link | CONFIRMED | N/A | Exact trade-to-goods link is documented. |
| 056 | US-06 | Used trade capacity or exposed quantity | trade | per-trade quantity / `used_trade_capacity` | value | Wiki: Trigger; Scope link | NOT_CONFIRMED | Use US-10 `transferred_quantity` | Market-level `used_merchant_capacity`, `merchant_capacity`, and trade `capacity_market` exist, but no per-trade quantity/capacity value is documented. |
| 057 | US-06 | Trade distance | trade | per-trade `trade_distance` | value | Wiki: Trigger | NOT_CONFIRMED | configured market distance proxy | `distance_to` and `distance_to_squared` are location values, not a trade distance exposure. |
| 058 | US-06 | Trade range | trade | per-trade numeric `trade_range` | value | Wiki: Trigger; Modifier types | NOT_CONFIRMED | configured range proxy; invalid if <= 0 | `in_trade_range_of` is a market boolean and `trade_range` is a country modifier type; no per-trade numeric range is documented. |
| 059 | US-06 | Gross trade income per trade | trade | `gross_trade_income` / per-trade vanilla income | value | All 7 wiki pages | NOT_CONFIRMED | monthly trade income estimate | Only country-level `monthly_trade_income` is documented. |
| 060 | US-06 | Directly reduce trade income | trade | direct trade-income effect | effect | Wiki: Effect; Modifier types | NOT_CONFIRMED | monthly reconciliation | `trade_income` is a country modifier type, but no effect that imputes a specific trade's income is documented. Direct mode remains non-MVP. |
| 061 | US-06 | Apply country-level trade reconciliation | country | `add_country_modifier` with `monthly_gold_expense` or `trade_income`; `add_gold` | effect/modifier | Wiki: Effect; Modifier types | CONFIRMED | N/A | Country-level sized modifiers and gold mutation are documented. Choose one reconciliation mechanism and validate sign/timing locally. |
| 062 | US-06 | Display transport cost in UI | modifier/tooltip/window | native transport-cost UI binding | UI/localization | Wiki: Effect; Modifier types | NOT_CONFIRMED | debug event/report | `custom_tooltip`, modifier descriptions, and debug logs exist, but no native transport-cost panel/tooltip binding is documented. Cost must not be hidden. |
| 063 | US-07 | Trade building modifier names | building/location modifier block | `local_burghers_estate_power`, `local_merchant_power` | static modifier | Wiki: Modifier types; Building modding | CONFIRMED | N/A | Both exact modifier names are documented; building `modifier` applies regular location modifiers. Local vanilla entries still determine which buildings to override. |
| 064 | US-08 | Goods price field | `in_game/common/goods` | `default_market_price` | static field | Wiki: Goods modding | CONFIRMED | N/A | The documented field is `default_market_price`, not `base_price`. |
| 065 | US-08 | Building dynamic price rules | building type static definition | `price`, `p_building_<key>`, `p_expensive_building_<key>`, `expensive`, `increase_per_level_cost` | static field/rule | Wiki: Building modding; Scope link | CONFIRMED | N/A | The `<key>` is the building's unlock age, or the first age when no advance unlocks it. `building_base_cost_in_gold` is also exposed. RGO pricing is tracked separately in 082. |
| 066 | US-09 | Production efficiency bonus | country | `global_production_efficiency` | modifier | Wiki: Modifier types | CONFIRMED | N/A | Exact country modifier, percent-good format. Apply with `add_country_modifier` from 009. |
| 067 | US-10.0 | Opinion buyer toward seller | country → country | `opinion = { target = <country> value ... }` | value/trigger | Wiki: Trigger; Variable | CONFIRMED | N/A | Exact target-country comparison/value is documented. |
| 068 | US-10.0 | Trade advantage in market | market with country argument/context | `merchant_power_in_market` | value/trigger | Wiki: Trigger; Variable | CONFIRMED | N/A | Returns market merchant power for a country in the scoped market. |
| 069 | US-10.0 | Market access | location | `market_access` | value/trigger | Wiki: Trigger; Variable | CONFIRMED | N/A | Exact exposure is location-scoped; country/market aggregation must be scripted. |
| 070 | US-10.0 | Embargo relation | country → country | `is_embargoed_by`, `is_embargoing` | trigger | Wiki: Trigger | CONFIRMED | N/A | Both relation directions are documented. |
| 071 | US-10.0 | War relation | country → country | `is_at_war_with` | trigger | Wiki: Trigger | CONFIRMED | N/A | Exact target-country trigger is documented. |
| 072 | US-10.0 | Subject relation | country → country | `is_subject_of`, `overlord` | trigger/scope link | Wiki: Trigger; Scope link | CONFIRMED | N/A | Both the relation trigger and country-to-overlord link are documented. |
| 073 | US-10.0 | Market owner | market → country | `owner` | scope link | Wiki: Scope link | CONFIRMED | N/A | `owner` accepts market scope and returns country. The alias `market_owner` is not documented. |
| 074 | US-10.0 | Ordered candidate sorting | list/map/typed iterator | `ordered_in_list`, `ordered_key_in_variable_map`, typed `ordered_*` with `order_by` | iterator | Wiki: Variable; Effect | CONFIRMED | N/A | Supports `limit`, `order_by`, position/min/max, and deterministic bounded iteration. |
| 075 | US-10.1 | Resolve consumption without trade | ModeU5 | modeu5_remove_stock | internal effect | ModeU5 | CONFIRMED | N/A | Must never create trade income/cost. |
| 076 | US-10.2 | Resolve inter-market transfer | ModeU5 | modeu5_transfer_stock | internal effect | ModeU5 | CONFIRMED | N/A | Applies only when source_market != target_market. |
| 077 | US-10.3 | Track unsatisfied demand | ModeU5 | internal variables | internal variable | ModeU5 | CONFIRMED | N/A | Feeds US-04 when consumer is local Pops. |
| 078 | US-13 | Non-horde check | country | exact government/horde classification trigger | trigger | Wiki: Scope link; Trigger | NOT_CONFIRMED | exclude US-13 until confirmed | `government_type`, `has_reform`, `horde_unity`, and `horde_unity_percentage` exist, but none is documented as a reliable generic horde/non-horde classification. |
| 079 | US-13 | Current age | current script context | `current_age` | trigger | Wiki: Trigger | CONFIRMED | N/A | Exact trigger is documented; accepted values still require local vanilla/static-file inspection. |
| 080 | US-13 | Conquest CB/wargoal cost override | static CB/wargoal files | `conquer_cost` | static field | All 7 wiki pages | NOT_CONFIRMED | no implementation until confirmed | No `conquer_cost` field or equivalent conquest-cost override is documented on the reviewed pages. |
| 081 | US-00.1 | Identify the country credited with a production source | building/RGO/location → country | production owner / output recipient | scope link/value | Wiki: Scope link; Building modding | NOT_CONFIRMED | No fallback selected; propose one after the exposure spike | `owner` exists for building and location, and foreign buildings explicitly have a building owner distinct from location owner. The pages do not document which country is credited with each building/RGO output, so neither owner may be assumed universally. |
| 082 | US-08 | RGO dynamic price rules | RGO/static economy files | RGO construction/upgrade price fields | static field/rule | All 7 wiki pages | NOT_CONFIRMED | do not override until confirmed | Goods modding documents `block_rgo_upgrade`, AI RGO fields, and upgrade-demand names, but not RGO price calculation or an RGO base-price field. |

## Rule

If an entry remains `TO_TEST` or `NOT_CONFIRMED`, gameplay implementation may not depend on it unless the fallback decision is explicitly approved.

When a fallback is accepted, record only one fallback for the PR. Do not implement several competing fallbacks without approval.

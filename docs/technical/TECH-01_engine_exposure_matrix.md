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
https://eu5.paradoxwikis.com/On_actions
local vanilla files
local script_docs output
error.log after test
```

## Wiki audit — 2026-06-13

The wiki pages listed above were reviewed for every matrix entry that was still marked `TO_CHECK` or `TO_TEST`.

- `CONFIRMED` means the required exposure and the exact method named in the row are documented by at least one of those pages.
- `NOT_CONFIRMED` means the exact required exposure was not documented by those pages. Adjacent or partial APIs are recorded in the notes but do not satisfy the row.
- Wiki confirmation does not replace a local script-docs check and controlled `error.log` test before gameplay implementation.
- A wiki `NOT_CONFIRMED` result is not proof that the engine lacks the exposure; it remains blocked until local vanilla files, local script docs, or a controlled test confirm it, or one fallback is accepted.
- Rows 083-085 were added as explicit local-file audits after the wiki pass and remain `TO_TEST` until those files are inspected.
- Row 044 combines the ModeU5 direct-formula contract with an engine hook that remains `TO_TEST`.
- Row 081 is a ModeU5 scope contract; its `CONFIRMED` status does not claim an undocumented vanilla income-recipient endpoint.

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
| 010 | Core | Apply or replace a temporary location modifier | location | `add_location_modifier`, `remove_location_modifier` | effect | Wiki: Effect | CONFIRMED | N/A | `add_location_modifier` supports days/months/years, mode, dynamic `size`, description, and `recalculate_immediately`. Use a one-month duration or explicit remove/replace in the shared monthly cycle; verify replacement locally. |
| 011 | Core | Monthly country cycle | none → country | `monthly_country_pulse` | on_action | Wiki: On actions | CONFIRMED | N/A | The pulse changes scope to each country and fires its `pulse_effect`. ModeU5 should register one shared monthly dispatcher and preserve the normative runtime order. |
| 012 | Core | Yearly country cycle | none → country | `yearly_country_pulse` | on_action | Wiki: On actions | CONFIRMED | N/A | The documented yearly pulse changes scope to each country. ModeU5 should register one shared yearly dispatcher. |
| 013 | Core | Fire debug/test events | effect scope | `trigger_event_silently`, `trigger_event_non_silently` | event effect | Wiki: Effect | CONFIRMED | N/A | Supports event IDs, named on_actions, and optional day/month/year delay. `debug_log`, `error_log`, and `test_log` are also documented. |
| 014 | Core | Localization for modifiers/tooltips | effect/modifier/static object | `custom_tooltip`, modifier `desc`, object `<key>` / `<key>_desc` | localization hook | Wiki: Effect; Building modding; Goods modding | CONFIRMED | N/A | The pages document localization-key hooks. Exact project localization file paths still need local validation. |
| 015 | US-01 | Current country stock in market for good | ModeU5 | country_market_good_stock | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 016 | US-01 | Market stock for good | ModeU5 | market_good_stock | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 017 | US-01 | Country stock capacity | ModeU5 | country_market_good_stock_cap | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 018 | US-01 | Available stock capacity | ModeU5 | stock_cap - stock | internal scripted value | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 019 | US-11 | Rebuild market stock from country stocks | ModeU5 | modeu5_rebuild_market_stock_from_country_stocks | internal effect | ModeU5 | CONFIRMED | N/A | Must not modify country stocks. |
| 020 | US-11 | Validate stock consistency | ModeU5 | modeu5_validate_stock_consistency | internal effect | ModeU5 | CONFIRMED | N/A | Corrects market aggregate only. |
| 021 | US-00.1 | Read location production by good and aggregate it into the country ledger | current country → owned location × good → location market | location `goods_output` for a target good; location `raw_material_output` when `raw_material = good`; validation against `produced_in_country:<good>` / `produced_in_market:<good>` | value / aggregation design | Wiki: Trigger; local vanilla trigger localization and scripts | TO_TEST | N/A | The required data exists. Sum each owned location's output into `country × location.market × good`; source-level building/RGO output is not required. Controlled script test must confirm the exact target-good syntax for `goods_output` and treatment of foreign-owned buildings before gameplay implementation. |
| 022 | US-00.1 | Actual quantity added to stock | ModeU5 | modeu5_add_stock output | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 023 | US-00.1 | Rejected quantity | ModeU5 | quantity_to_add - actual_added_quantity | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 024 | US-00.1 | Ledger helper | ModeU5 | modeu5_update_production_rejection_ledger | internal effect | ModeU5 | CONFIRMED | N/A | Must be used for all ledger writes. |
| 025 | US-00.1 | Store and read a monthly ledger keyed by country × market × good | country-scoped per-good map keyed by market | `add_to_variable_map`, <code>variable_map(name&#124;key)</code>, `remove_from_variable_map`, `clear_variable_map` | variable storage and keying | Wiki: Variable; Effect | CONFIRMED | N/A | Build and update the ledger monthly. Existing map keys require remove then re-add; clear only after all monthly consumers run. Do not reconstruct it from final stock snapshots. |
| 026 | US-00.2 | Calculate ratios with division/min/max | scripted effect/value | `change_variable` operations `divide`, `min`, `max` | scripted math | Wiki: Variable; Effect | CONFIRMED | N/A | `change_variable` documents add/subtract/multiply/divide/modulo/min/max. Script must guard `produced <= 0` before division. |
| 027 | US-00.3 | Good-specific local output modifier | location, one generated modifier per good | `local_<good>_output_modifier` | modifier | Wiki: Goods modding; Modifier types | CONFIRMED | N/A | Goods modding defines the generated pattern; concrete entries such as `local_iron_output_modifier` are listed. Apply through 010. |
| 028 | US-00.3 | Local production efficiency modifier | location | `local_production_efficiency` | modifier | Wiki: Modifier types | CONFIRMED | N/A | Exact location modifier, percent-good format. Apply through 010; it affects all local goods. |
| 029 | US-00.3 | Identify affected production sources/locations producing the good | building/location/production method/goods | `every_buildings_in_location`, `building_produced_goods`, `every_production_method_of_building`, `produced_goods`, location `raw_material` | iterator/trigger/scope link | Wiki: Effect; Trigger; Scope link | CONFIRMED | N/A | These APIs identify producing buildings, production methods, and RGO goods. Use the country-rooted attribution rule in 081. |
| 030 | US-00.4 | Good price for void wealth | market × good | `market_price`; fallback `default_price` / `default_market_price` | value/static field | Wiki: Scope link; Trigger; Goods modding | CONFIRMED | N/A | `market_price` is exposed on market for scoped goods; `default_market_price` is the static goods field. Log `good_price_source`. |
| 031 | US-00.4 | Estate tax base for proxy sizing | country or estate | `estate_tax_base` | value/trigger | Wiki: Scope link; Trigger | CONFIRMED | N/A | Correct documented name is `estate_tax_base`, not `estate_taxable_income`. Optional proxy only; not the primary punishment. |
| 032 | US-00.4 | Estate tax percentage for proxy sizing | country | `estate_tax_percentage` | value/trigger | Wiki: Scope link; Trigger | CONFIRMED | N/A | Correct documented name is `estate_tax_percentage`, not `estate_tax`. |
| 033 | US-02 | Count owned locations in market | country → location → market | `every_owned_location` plus location `market` | iterator/scope link | Wiki: Effect; Scope link | CONFIRMED | N/A | Iterate country-owned locations and retain those whose `market` equals the target market. |
| 034 | US-02 | Buildings in location | location → building | `every_buildings_in_location` | effect iterator | Wiki: Effect | CONFIRMED | N/A | Exact iterator is documented. |
| 035 | US-02 | Foreign buildings in location | location → building | `every_foreign_buildings_in_location` | effect iterator | Wiki: Effect; Building modding | CONFIRMED | N/A | Building modding also documents `is_foreign = yes` and distinguishes building owner from location owner. |
| 036 | US-03 | Invoke monthly decay in the shared cycle | country | `monthly_country_pulse` → ModeU5 monthly dispatcher → `modeu5_decay_stock` | on_action integration | Wiki: On actions; ModeU5 runtime order; TECH-01 011 | CONFIRMED | N/A | This is an orchestration rule, not a separate engine pulse. Invoke decay at runtime step 12 and do not register a second monthly mechanism. |
| 037 | US-04 | Local Pop demand for good | location × good | runtime vanilla Pop demand value | value | Wiki: Goods modding; Trigger; Scope link | NOT_CONFIRMED | Simulated demand | `pop_demand`, `demand_add`, and `demand_multiply` are documented as static definitions, but no runtime location × good Pop-demand value is documented. |
| 038 | US-04 | Population by type in location | location | `num_pop_type`, `percentage_pop_type_in_location` | value/trigger | Wiki: Scope link; Trigger | CONFIRMED | N/A | Both exact location values are documented. |
| 039 | US-04 | Apply a local demand modifier to vanilla demand | location × good × Pop context | local dynamic Pop-demand modifier/effect | modifier/effect | Wiki: Goods modding; Modifier types; Effect | NOT_CONFIRMED | Simulated demand only | Static `pop_demand` script values and country-wide `global_<good>_pop_demand` modifiers exist, but no local location × good runtime modifier/application effect is documented. |
| 040 | US-04 | Track yearly satisfied/unsatisfied months | location/good | variables | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 041 | US-05 | Read the vanilla Stability/Court slider cost | country/slider | readable slider cost value | value | ModeU5 direct-formula design | OUT_OF_SCOPE | N/A | Not required when ModeU5 replaces the Economic Base formula directly. Do not implement monthly slider reconciliation in this design. |
| 042 | US-05 | Monthly trade income | country | `monthly_trade_income` | value/trigger | Wiki: Trigger | CONFIRMED | N/A | Exact country value/trigger is documented. `monthly_income_trade_and_tax` is a separate broader value. |
| 043 | US-05 | Read total country wealth for the Economic Base formula | country | script value equivalent to GUI `Country.GetTotalWealth`, or a confirmed aggregate | value | Local vanilla GUI; Wiki: Trigger; Scope link | TO_TEST | One accepted ModeU5 wealth aggregate if no script value exists | Vanilla GUI exposes `Country.GetTotalWealth`, proving the engine has the value, but the exact gameplay-script value is not documented. Test a script equivalent before accepting reconstruction. |
| 044 | US-05 | Replace the Economic Base formula used by Stability and legitimacy-producing Court costs | economy/slider formula context | modifiable formula or controlled call site using `modeu5_slider_cost_base = Wealth + monthly_trade_income` | formula/static/script hook | Local vanilla economy GUI and common files; ModeU5 specification | TO_TEST | No reconciliation fallback in the selected design | The formula contract is clear, but local files have not yet exposed a moddable Stability/Court base-formula hook. Confirm the actual call site before implementation. |
| 045 | US-05 | Apply visible slider reconciliation | country/UI | sized modifier or gold effect with visible presentation | effect/modifier/UI | ModeU5 direct-formula design | OUT_OF_SCOPE | N/A | Reconciliation is not part of the selected direct-formula design. US-05-UI must explain the replacement formula and inputs instead. |
| 047 | US-10.2 | Iterate vanilla trades | country/market → trade | `every_trade`, `ordered_trade` | effect iterator | Wiki: Effect | CONFIRMED | N/A | Both trade iterators are documented; ordered iteration supports deterministic filtering and ordering. |
| 048 | US-10.2 | Iterate vanilla imports | country/market → import | `every_import`, `ordered_import` | effect iterator | Wiki: Effect | CONFIRMED | N/A | Both import iterators are documented. |
| 049 | US-10.2 | Iterate vanilla exports | country/market → export | `every_export`, `ordered_export` | effect iterator | Wiki: Effect | CONFIRMED | N/A | Both export iterators are documented. |
| 054 | US-10.2 | Identify source and target markets of a trade | trade → market | `from_market`, `to_market` | scope link | Wiki: Scope link | CONFIRMED | N/A | Both links are documented on trade scope. |
| 055 | US-10.2 | Identify the traded good | trade → goods | `traded_goods` | scope link | Wiki: Scope link | CONFIRMED | N/A | The trade-to-goods link is documented. |
| 056 | US-10.2 | Read actual and desired quantity while iterating a vanilla trade | trade | script value equivalent to GUI `Trade.GetQuantityOfGoodsActuallyMoved`; optional desired quantity equivalent to `Trade.GetDesiredGoodsToShip` / `GetDesiredGoodsShipped` | value | Local vanilla GUI; Wiki: Trigger; Scope link | TO_TEST | Use an explicit requested quantity for ModeU5-created transfers; do not infer a vanilla request | Trade iteration enters trade scope and the engine exposes exact quantities to GUI, but no gameplay-script trigger/value name is documented. A controlled script test must prove the equivalent value is callable inside `every_trade`/`ordered_trade`. |
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
| 078 | US-13 | Non-horde check | country | `government_type = government_type:steppe_horde`; invert for non-horde | trigger / scope comparison | Wiki: Scope link; Government; local vanilla events and auto modifiers | CONFIRMED | N/A | Vanilla repeatedly uses this exact country trigger, including `events/government/steppe_horde.txt` and `events/disaster/horde_civil_war.txt`. |
| 079 | US-13 | Current age | current script context | `current_age` | trigger | Wiki: Trigger | CONFIRMED | N/A | Exact trigger is documented; accepted values still require local vanilla/static-file inspection. |
| 080 | US-13 | Conquest CB/wargoal cost override | static CB/wargoal files | `conquer_cost` | static field | Wiki pages | NOT_CONFIRMED | no implementation until confirmed | No `conquer_cost` field or equivalent conquest-cost override is documented on the reviewed pages. |
| 081 | US-00.1 | Establish the ModeU5 ledger country for location aggregation | country-rooted cycle → owned location | current country from `monthly_country_pulse`; `every_owned_location`; location `owner` validation | scope contract / iterator / scope link | Wiki: On actions; Effect; Scope link; local vanilla scripts; ModeU5 | CONFIRMED | N/A | The ledger country is the current country running the monthly cycle. Aggregate its owned locations by `location.market`; do not require an undocumented vanilla income-recipient concept. Foreign-building treatment is tested under 021. |
| 082 | US-08 | RGO dynamic price rules | RGO/static economy files | RGO construction/upgrade price fields | static field/rule | Wiki pages | NOT_CONFIRMED | do not override until confirmed | Goods modding documents `block_rgo_upgrade`, AI RGO fields, and upgrade-demand names, but not RGO price calculation or an RGO base-price field. |
| 083 | US-07 | Identify exact vanilla trade-building definitions and current values | local vanilla building files | in-scope building keys, modifiers, costs, and capacities | static data audit | Local vanilla files pending | CONFIRMED | N/A | Confirm the exact entries and source values before creating overrides or claiming tooltip differences. |
| 084 | US-08 | Identify the exact in-scope building and RGO definitions | local vanilla building/RGO files | definition keys and current price-related values | static data audit | Local vanilla files pending | TO_TEST | N/A | This inventory is separate from whether the RGO price hook itself exists under 082. |
| 085 | US-08-UI | Bind native building/RGO price breakdowns into UI | vanilla GUI and localization files | existing price tooltip/datacontext binding | UI exposure | Local vanilla GUI files pending | TO_TEST | Documentation/debug only | Do not claim the native tooltip can show the ModeU5 breakdown until the binding is confirmed. |
| 086 | US-10.1 | Read Estate and other non-Pop consumer demand context | estate/country/consumer caller | reliable vanilla requested-quantity inputs | value/caller context | Wiki pages; local script check pending | NOT_CONFIRMED | One explicitly accepted simulated-demand caller | No reliable generic Estate/other consumer requested-quantity input has been identified. |

## Unresolved exposure impact matrix

This matrix maps each `TO_TEST` or `NOT_CONFIRMED` engine exposure to the user stories that reference it directly or inherit its blocked behavior.

| TECH-01 | Unresolved exposure | Impacted US | Blocked behavior | Current fallback / boundary |
|---:|---|---|---|---|
| 021 | Exact target-good syntax and ownership semantics for location output | US-00.1, EPIC US-00, US-00-UI | Aggregate location production into `country × market × good` before stock insertion | Test `goods_output` and `raw_material_output`; no source-level reconstruction is required. |
| 037 | Runtime local Pop demand by good | US-04, US-04-UI, US-10.1, EPIC US-10 | Read the actual quantity requested by local Pops for stock resolution and adaptation | Use one explicitly accepted simulated-demand source. |
| 039 | Dynamically modify local vanilla Pop demand | US-04 | Apply annual demand adaptation at location × good × Pop context | Simulated ModeU5 demand only; do not claim vanilla demand was changed. |
| 043 | Gameplay-script access to total country wealth | US-05, US-05-UI | Calculate the required `Wealth + Trade Income` ModeU5 Economic Base | Test a script equivalent to `Country.GetTotalWealth`; accept one aggregate only if needed. |
| 044 | Modifiable Stability/Court Economic Base formula hook | US-05, US-05-UI | Replace Tax Base with the ModeU5 Economic Base in the affected vanilla calculations | Direct formula replacement only; reconciliation is out of scope. |
| 056 | Gameplay-script access to actual/desired per-trade quantity | US-10.2, EPIC US-10 | Derive a vanilla transfer request from the actual/desired trade quantity | Test script equivalents to the confirmed GUI accessors; use explicit requested quantity for ModeU5-created transfers. |
| 080 | Override conquest CB/wargoal cost | US-13 | Apply fixed age-based conquest-cost additions | Keep US-13 excluded until confirmed. |
| 082 | Read or override RGO dynamic price rules | US-08, US-08-UI | Set RGO construction/upgrade base price to 50 and explain it in UI | Do not override RGO pricing until confirmed. |
| 084 | Exact in-scope building/RGO definition inventory | US-08 | Limit fixed-price overrides to an explicit approved list | Audit local vanilla building and RGO files. |
| 085 | Native price-tooltip binding | US-08-UI | Show the ModeU5 base-price breakdown in vanilla UI | Use documentation/debug until the binding is confirmed. |
| 086 | Estate/other consumer requested quantity | US-10.1, EPIC US-10 | Resolve non-Pop consumption from stock | Require one explicitly accepted simulated-demand caller. |

## Rule

If an entry remains `TO_TEST` or `NOT_CONFIRMED`, gameplay implementation may not depend on it unless the fallback decision is explicitly approved.

When a fallback is accepted, record only one fallback for the PR. Do not implement several competing fallbacks without approval.

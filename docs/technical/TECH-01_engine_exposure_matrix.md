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

## Matrix

| ID | US | Need | Expected scope | Candidate exposure | Type | Source checked | Status | Fallback decision | Test / notes |
|---:|---|---|---|---|---|---|---|---|---|
| 001 | Core | Iterate all countries | global | every_country | effect iterator | TO_CHECK | TO_TEST | Required |  |
| 002 | Core | Iterate all markets | global | every_market / market list | effect iterator | TO_CHECK | TO_TEST | Required | Needed for annual validation/rebuild. |
| 003 | Core | Iterate owned locations of a country | country | every_owned_location | effect iterator | TO_CHECK | TO_TEST | Required |  |
| 004 | Core | Identify a location's market | location | market | scope link | TO_CHECK | TO_TEST | Required |  |
| 005 | Core | Identify location owner | location | owner | scope link | TO_CHECK | TO_TEST | Required |  |
| 006 | Core | Iterate or identify goods | global / good | every_goods / goods list / static goods | iterator/list | TO_CHECK | TO_TEST | Required |  |
| 007 | Core | Store variables by country × market × good | country / market / good | variable maps / scoped variables / generated variable names | variable | TO_CHECK | TO_TEST | Use flattened variable names by good/market if maps fail | Critical for US-00/US-01. |
| 008 | Core | Save and reuse country/market/good scopes in effects | effect | saved scopes / event targets | scope handling | TO_CHECK | TO_TEST | Pass explicit parameters through effects |  |
| 009 | Core | Apply temporary country modifier | country | add_modifier or equivalent | effect | TO_CHECK | TO_TEST | Debug-only if unconfirmed |  |
| 010 | Core | Apply temporary location modifier | location | add_modifier or equivalent | effect | TO_CHECK | TO_TEST | Theoretical-only production penalty |  |
| 011 | Core | Monthly on_action | global | monthly on_action | on_action | TO_CHECK | TO_TEST | event pulse if available |  |
| 012 | Core | Yearly on_action | global | yearly on_action | on_action | TO_CHECK | TO_TEST | event pulse if available |  |
| 013 | Core | Fire debug/test events | country/global | events / hidden events | event | TO_CHECK | TO_TEST | manual console event |  |
| 014 | Core | Localization for modifiers/tooltips | localization | localization files | static file | TO_CHECK | TO_TEST | Debug only if UI unavailable |  |
| 015 | US-01 | Current country stock in market for good | ModeU5 | country_market_good_stock | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 016 | US-01 | Market stock for good | ModeU5 | market_good_stock | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 017 | US-01 | Country stock capacity | ModeU5 | country_market_good_stock_cap | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 018 | US-01 | Available stock capacity | ModeU5 | stock_cap - stock | internal scripted value | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 019 | US-11 | Rebuild market stock from country stocks | ModeU5 | modeu5_rebuild_market_stock_from_country_stocks | internal effect | ModeU5 | CONFIRMED | N/A | Must not modify country stocks. |
| 020 | US-11 | Validate stock consistency | ModeU5 | modeu5_validate_stock_consistency | internal effect | ModeU5 | CONFIRMED | N/A | Corrects market aggregate only. |
| 021 | US-00.1 | Production quantity by country × market × good | country × market × good | produced_in_market / produced_in_country / local production values | value | TO_CHECK | TO_TEST | Estimate from best available production proxy | Do not invent exact value. |
| 022 | US-00.1 | Actual quantity added to stock | ModeU5 | modeu5_add_stock output | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 023 | US-00.1 | Rejected quantity | ModeU5 | quantity_to_add - actual_added_quantity | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 024 | US-00.1 | Ledger helper | ModeU5 | modeu5_update_production_rejection_ledger | internal effect | ModeU5 | CONFIRMED | N/A | Must be used for all ledger writes. |
| 025 | US-00.1 | Variable map indexed by market | country | modeu5_<good>_produced_by_market[market] | variable map | TO_CHECK | TO_TEST | Flattened per-good/per-market variables |  |
| 026 | US-00.2 | Calculate ratios with division/min/max | scripted value/effect | arithmetic operators | scripted math | TO_CHECK | TO_TEST | Store precomputed values in effects | Need safe division when produced <= 0. |
| 027 | US-00.3 | Good-specific local output modifier | location × good | local output modifier for specific good | modifier | TO_CHECK | TO_TEST | local_production_efficiency | Preferred. |
| 028 | US-00.3 | Local production efficiency modifier | location | local_production_efficiency | modifier | TO_CHECK | TO_TEST | theoretical_only if unavailable | Fallback may affect other goods. |
| 029 | US-00.3 | Count affected locations producing good | country/location/good | production building / RGO / output checks | value/iterator | TO_CHECK | TO_TEST | Apply at country/market level or theoretical-only |  |
| 030 | US-00.4 | Good price for void wealth | market × good | market price / average price / base price | value | TO_CHECK | TO_TEST | configured scripted good price | Must log good_price_source. |
| 031 | US-00.4 | Estate taxable income for proxy sizing | estate | estate_taxable_income | value/trigger | TO_CHECK | TO_TEST | Optional proxy only | Not primary punishment. |
| 032 | US-00.4 | Estate tax for proxy sizing | estate | estate_tax | value/trigger | TO_CHECK | TO_TEST | Optional proxy only |  |
| 033 | US-02 | Count owned locations in market | country/market/location | every_owned_location + market check | iterator/scope link | TO_CHECK | TO_TEST | Static configured base capacity |  |
| 034 | US-02 | Buildings in location | location | every_buildings_in_location | effect iterator | TO_CHECK | TO_TEST | Static configured capacity by location only |  |
| 035 | US-02 | Foreign buildings in location | location | every_foreign_buildings_in_location | effect iterator | TO_CHECK | TO_TEST | Exclude foreign compatible buildings for MVP |  |
| 036 | US-03 | Monthly decay pulse | global | monthly on_action | on_action | TO_CHECK | TO_TEST | debug event pulse |  |
| 037 | US-04 | Local Pop demand for good | location × good | vanilla pop demand by good | value | TO_CHECK | NOT_CONFIRMED | Simulated demand | Existing fallback accepted conceptually but must be implemented explicitly. |
| 038 | US-04 | Population by type in location | location | num_pop_type / percentage_pop_type_in_location | value | TO_CHECK | TO_TEST | rough location population proxy |  |
| 039 | US-04 | Apply demand modifier to vanilla demand | location/good/pop | pop demand modifier | modifier/effect | TO_CHECK | TO_TEST | Simulated demand only |  |
| 040 | US-04 | Track yearly satisfied/unsatisfied months | location/good | variables | internal variable | ModeU5 | CONFIRMED | N/A | Defined by mod. |
| 041 | US-05 | Slider vanilla cost | country | stability / court slider cost | value/effect | TO_CHECK | TO_TEST | reconciliation modifier / debug only |  |
| 042 | US-05 | Monthly trade income | country | monthly_trade_income | value/trigger | TO_CHECK | TO_TEST | monthly income estimate |  |
| 043 | US-05 | Country wealth | country | wealth / location wealth aggregate | value | TO_CHECK | TO_TEST | ModeU5 reconstructed/estimated wealth |  |
| 044 | US-05 | Directly replace slider cost base | country/slider | slider cost script | static/scripted value | TO_CHECK | TO_TEST | monthly reconciliation |  |
| 045 | US-05 | Apply visible reconciliation | country | country modifier / money effect / expense effect | effect/modifier | TO_CHECK | TO_TEST | debug-only if no safe effect |  |
| 046 | US-05.1 | Subtract void wealth from slider base | country | modeu5_total_void_wealth | internal variable | ModeU5 | CONFIRMED | N/A | Optional/MVP+ unless needed to avoid double penalty. |
| 047 | US-06 | Iterate trades | country/global | every_trade / ordered_trade | iterator | TO_CHECK | TO_TEST | Use US-10 transferred_quantity |  |
| 048 | US-06 | Iterate imports | country/market | every_import / ordered_import | iterator | TO_CHECK | TO_TEST | Use US-10 transferred_quantity |  |
| 049 | US-06 | Iterate exports | country/market | every_export / ordered_export | iterator | TO_CHECK | TO_TEST | Use US-10 transferred_quantity |  |
| 050 | US-06 | Trade income recipient | trade/import/export | trade_income_recipient | scope link/value | TO_CHECK | TO_TEST | trade_owner, buyer_country, current scope | Payer priority #1. |
| 051 | US-06 | Trade owner | trade/import/export | owner / trade_owner | scope link | TO_CHECK | TO_TEST | buyer_country or current country scope | Payer priority #2. |
| 052 | US-06 | Buyer country | trade/import/export | buyer_country | scope link | TO_CHECK | TO_TEST | current country scope | Payer priority #3. |
| 053 | US-06 | Seller country | trade/import/export | seller_country | scope link | TO_CHECK | TO_TEST | Debug only |  |
| 054 | US-06 | Trade from/to markets | trade/import/export | from_market / to_market | scope links | TO_CHECK | TO_TEST | Use US-10 source/target market |  |
| 055 | US-06 | Traded good(s) | trade/import/export | traded_goods / good | scope link/list | TO_CHECK | TO_TEST | Use US-10 good |  |
| 056 | US-06 | Used trade capacity or exposed quantity | trade/import/export | used_trade_capacity / exposed trade quantity | value | TO_CHECK | TO_TEST | Use US-10 transferred_quantity |  |
| 057 | US-06 | Trade distance | trade/import/export | trade_distance | value | TO_CHECK | TO_TEST | configured market distance proxy |  |
| 058 | US-06 | Trade range | trade/import/export | trade_range | value | TO_CHECK | TO_TEST | configured range proxy; invalid if <= 0 |  |
| 059 | US-06 | Gross trade income per trade | trade/import/export | gross_trade_income / vanilla_trade_income | value | TO_CHECK | TO_TEST | monthly trade income estimate |  |
| 060 | US-06 | Directly reduce trade income | trade/import/export | trade income effect | effect | TO_CHECK | TO_TEST | monthly reconciliation | Direct mode is ideal but not MVP-required. |
| 061 | US-06 | Apply country-level trade reconciliation | country | money effect / trade income modifier / trade efficiency modifier | effect/modifier | TO_CHECK | TO_TEST | visible debug-only if no safe effect |  |
| 062 | US-06 | Display transport cost in UI | modifier/tooltip/window | country modifier / custom UI / debug event | UI/localization | TO_CHECK | TO_TEST | debug window | Cost must not be hidden. |
| 063 | US-07 | Trade building modifier names | static building files | local_burghers_estate_power / local_merchant_power | static modifier | TO_CHECK | TO_TEST | use confirmed local files only |  |
| 064 | US-08 | Goods price field | static goods files | default_market_price / base_price | static field | TO_CHECK | TO_TEST | use confirmed local files only |  |
| 065 | US-08 | Building/RGO dynamic price rules | static files | 1.2 dynamic pricing fields | static field | TO_CHECK | TO_TEST | do not override until confirmed |  |
| 066 | US-09 | Production efficiency bonus | country/global | global_production_efficiency / production_efficiency | modifier | TO_CHECK | TO_TEST | no implementation until confirmed |  |
| 067 | US-10.0 | Opinion buyer toward seller | country → country | opinion | value/trigger | TO_CHECK | TO_TEST | omit opinion from MVP scoring |  |
| 068 | US-10.0 | Trade advantage in market | market/country | merchant_power_in_market / trade advantage | value/trigger | TO_CHECK | TO_TEST | omit trade advantage from MVP scoring |  |
| 069 | US-10.0 | Market access | location/country/market | market_access | value/trigger | TO_CHECK | TO_TEST | allow only own stock first |  |
| 070 | US-10.0 | Embargo relation | country → country | embargo trigger/scope | trigger | TO_CHECK | TO_TEST | omit embargo filter from MVP if unconfirmed |  |
| 071 | US-10.0 | War relation | country → country | is_at_war_with / war trigger | trigger | TO_CHECK | TO_TEST | exclude only if confirmed; otherwise own-stock MVP |  |
| 072 | US-10.0 | Subject relation | country → country | is_subject_of / overlord | trigger/scope | TO_CHECK | TO_TEST | omit subject bonus if unconfirmed |  |
| 073 | US-10.0 | Market owner | market | owner / market_owner | scope link | TO_CHECK | TO_TEST | omit market owner bonus if unconfirmed |  |
| 074 | US-10.0 | Ordered candidate sorting | script/effect | ordered_* iterator / scripted sort | iterator | TO_CHECK | TO_TEST | simple deterministic priority buckets |  |
| 075 | US-10.1 | Resolve consumption without trade | ModeU5 | modeu5_remove_stock | internal effect | ModeU5 | CONFIRMED | N/A | Must never create trade income/cost. |
| 076 | US-10.2 | Resolve inter-market transfer | ModeU5 | modeu5_transfer_stock | internal effect | ModeU5 | CONFIRMED | N/A | Applies only when source_market != target_market. |
| 077 | US-10.3 | Track unsatisfied demand | ModeU5 | internal variables | internal variable | ModeU5 | CONFIRMED | N/A | Feeds US-04 when consumer is local Pops. |
| 078 | US-13 | Non-horde check | country | government type / horde trigger | trigger | TO_CHECK | TO_TEST | exclude US-13 until confirmed |  |
| 079 | US-13 | Current age | global/country | current age value/trigger | trigger/value | TO_CHECK | TO_TEST | static CB variants with age trigger |  |
| 080 | US-13 | Conquest CB/wargoal cost override | static CB/wargoal files | conquer_cost | static field | TO_CHECK | TO_TEST | no implementation until confirmed |  |

## Rule

If an entry remains `TO_TEST` or `NOT_CONFIRMED`, gameplay implementation may not depend on it unless the fallback decision is explicitly approved.

When a fallback is accepted, record only one fallback for the PR. Do not implement several competing fallbacks without approval.

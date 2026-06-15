# AGENTS.md — ModeU5 Country Stocks Within Markets

## Project mission

ModeU5 adds a double-accounting layer for goods inside EU5 markets.

The mod does **not** replace the vanilla economy or vanilla markets. It adds a stock, control, debug, and consistency layer so that goods only generate effective ModeU5 economic value when they enter a stock that can actually be consumed, transferred, or lost.

The two stock levels are:

```txt
country_market_good_stock
market_good_stock
```

The central invariant is:

```txt
market_good_stock = sum(country_market_good_stock)
```

The country-level stock is the source of truth. The market-level stock is an aggregate/cache.

If the two diverge, rebuild `market_good_stock` from country stocks. Never rebuild country stocks from market stock.

## Module/package contract

ModeU5 is a suite:

```txt
No Void Economy
  required; cannot be disabled while ModeU5 is active

Rebalance Economy
  optional; US-04, US-05, US-08, US-09 and their UI stories

Rebalance Estate Power
  optional; US-07 and US-07-UI

Rebalance Early Blobbing
  optional; US-13
```

All other CORE and US stories belong to the required Core package.

Companion-package presence is the source of truth for optional static overrides. Do not claim that a runtime game rule disables US-07 or US-08 while their static files remain loaded.

Package selection occurs before campaign load. Adding or removing a package mid-campaign is unsupported without an explicit migration. Follow `docs/technical/MODULE_OPTION_MODEL.md`.

The default supported playset enables Core, Rebalance Economy, Rebalance Estate Power, and Rebalance Early Blobbing together. Optional means removable before campaign start, not disabled by default. Core must never synthesize a companion package marker when that package is absent.

ModeU5 configuration is pre-campaign. Optional packages are selected in the launcher/mod playset. Script-safe settings such as `modeu5_debug_level` use EU5's built-in Game Rules screen and are fixed when the campaign starts. Do not create an in-game configuration panel.

## Variable-map storage rule

Follow:

```txt
docs/technical/VARIABLE_MAP_STORAGE_MODEL.md
```

Use persistent variable maps for durable multidimensional state and counters. Use local variables and saved scopes for one operation's temporary values.

Canonical logical storage:

```txt
country × market × good:
  one country_market_good_record with named fields
  owner = country
  tuple = market × good

market × good aggregate:
  one market_good_record/cache
  owner = market
  tuple = good

location × good:
  one location_good_record with named fields
  owner = location
  tuple = good
```

EU5 variable maps are documented as one `key -> value` association, not as inline structs or nested maps. Until TECH-01 `088` confirms a unique persistent record scope or nested-map value, represent each logical record with a synchronized map family:

```txt
same owner
same tuple key
one static physical map per persistent field
centralized helpers enforcing record-level consistency
```

Map names are static identifiers. Do not assume runtime map-name construction. Existing keys must be removed before their replacement is re-added. Missing numeric entries require an explicit safe default.

## Non-negotiable stock rule

No user story may directly mutate stock variables.

All stock mutations must go through centralized scripted effects:

```txt
modeu5_add_stock
modeu5_remove_stock
modeu5_transfer_stock
modeu5_decay_stock
modeu5_rebuild_market_stock_from_country_stocks
modeu5_validate_stock_consistency
```

If an implementation writes directly to `country_market_good_stock` or `market_good_stock` outside these effects, stop and refactor.

## Runtime order is normative

The implementation roadmap is only a safe delivery order. The runtime order is the economic contract.

A monthly economic cycle must follow this logical sequence:

```txt
1. Apply previous-month production penalties.
2. If the Rebalance Economy package is loaded, apply its global ModeU5 modifiers, including the +5% Production Efficiency compensation.
3. Recalculate stock capacities when needed.
4. Read or estimate vanilla production.
5. Calculate ModeU5-recognized production.
6. Add stockable production through modeu5_add_stock.
7. Update market stock through the centralized operation.
8. Update US-00.1 production / added / rejected ledger.
9. Resolve Pop and Estate consumption through US-10.1.
10. Track satisfied and unsatisfied quantities through US-10.3.
11. Resolve inter-market transfers through US-10.2 when applicable.
12. Apply monthly decay through modeu5_decay_stock.
13. Calculate US-00.2 overproduction ratios.
14. Calculate US-00.4 void wealth.
15. Calculate US-00.3 next-month production penalties.
16. If the Rebalance Economy package is loaded, calculate the US-05 Economic Base.
17. If the Rebalance Economy package is loaded, display the US-05 formula inputs and result when exposure permits.
18. Validate stock consistency through modeu5_validate_stock_consistency.
19. Reset monthly counters only after every consumer has read them.
```

A yearly economic cycle must validate/rebuild stock aggregates, read annual satisfaction counters, apply US-04 demand adaptation only when the Rebalance Economy package is loaded, reset annual counters, and run diagnostics if enabled.

The monthly and yearly stock cycles must not mutate ModeU5 stock until CORE-02 has set the current schema version and marked initialization complete. A missing, failed, older unsupported, or newer incompatible initialization state fails closed and remains diagnostic-only.

## Stock succession rule

After initialization, permanent location ownership changes conserve stock and reassign the capacity-proportional share:

```txt
transferred_stock
= loser_stock_before
   * transferred_location_storage_capacity
   / loser_storage_capacity_before
```

Use the same US-02 location-capacity helper for the numerator and capacity totals. Apply the quantity through `modeu5_transfer_stock` in the same market. The loser retains the formula's complementary share and `market_good_stock` remains unchanged.

Sequential location transfers must produce the same result as one aggregate split. New-country/release hooks validate and finalize; they must not duplicate location-level transfers. Annexation finalizers transfer any residual stock of the disappearing country to its successor.

CORE-02 initialization and CORE-03 succession use capacity as a proportional allocation key, not as an admission cap. They must use the centralized operators' explicit `allow_over_capacity` policy and allocate or transfer the full formula-derived quantity. Any resulting over-cap stock is valid state to report; neither lifecycle operation truncates, rejects, or erases it.

Ordinary production and inter-market trade continue to use the default `enforce` policy. No other caller may bypass capacity without an explicit approved business rule.

## Documentation-first rule

Before implementing any script that depends on vanilla data, verify exposure through:

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
error.log after a local test
```

Do not assume a scope link, iterator, trigger, value, modifier, effect, or static field exists.

When exposure is checked, update:

```txt
docs/technical/TECH-01_engine_exposure_matrix.md
```

Allowed statuses:

```txt
TO_TEST
CONFIRMED
NOT_CONFIRMED
FALLBACK_ACCEPTED
OUT_OF_SCOPE
```

No gameplay implementation may depend on `TO_TEST` or `NOT_CONFIRMED` exposure unless one fallback is explicitly accepted.

## Implementation order

Follow this delivery order, even though it is not the runtime order:

```txt
0. CORE-00 module packaging contract and engine-exposure spike.
1. Bootstrap Core and optional-package structures and documentation.
2. CORE-01.1 through CORE-01.4 stock mutation effects.
3. CORE-01.5 / CORE-01.6 rebuild and validation, then US-11 orchestration.
4. Debug conventions and deterministic test events.
5. US-01 country × market × good stock.
6. US-02 stock capacity.
7. CORE-02 delayed, versioned start-game initialization.
8. CORE-03 country and territory stock succession.
9. Monthly and yearly on_actions.
10. US-03 monthly decay.
11. US-00.1 / US-00.2 / US-00.4 void economy measurement.
12. US-00.3 production penalty.
13. US-10.0 / US-10.1 / US-10.2 / US-10.3 demand resolution.
14. Rebalance Economy: US-04 local Pop demand adaptation.
15. Rebalance Economy: US-05 direct Economic Base formula.
16. Rebalance Economy and Rebalance Estate Power: US-07 / US-08 / US-09 static balance changes.
17. Rebalance Early Blobbing: US-13 only after exposure is confirmed.
18. UI/debug polish.
```

## Current canonical US-00

US-00 is not a direct monthly Estate income penalty.

US-00 is a pipeline:

```txt
production vanilla
→ modeu5_add_stock
→ actual_added_quantity / rejected_quantity
→ US-00.1 monthly production rejection ledger
→ US-00.2 overproduction ratio and stability buffer
→ US-00.4 void wealth valuation
→ US-00.3 production penalty for N+1
→ debug / UI
```

US-00 tracks values at:

```txt
country × market × good
```

Required counters or maps:

```txt
modeu5_<good>_produced_by_market[market]
modeu5_<good>_added_by_market[market]
modeu5_<good>_rejected_by_market[market]
modeu5_<good>_overproduction_ratio_by_market[market]
modeu5_<good>_effective_overproduction_ratio_by_market[market]
modeu5_<good>_void_wealth_by_market[market]
modeu5_<good>_void_taxable_income_proxy_by_market[market]
modeu5_<good>_production_penalty_by_market[market]
```

These are fields of one logical `country × market × good` record. With currently confirmed exposure, they are physically stored as a synchronized family of country-scoped, per-good maps keyed by market. Market-level stock uses a global `modeu5_<good>_market_stock` map keyed by market because controlled runtime testing confirmed that Market scope does not support variables. Country-wide totals with no remaining keyed dimension stay ordinary country variables.

All ledger writes must go through:

```txt
modeu5_update_production_rejection_ledger
```

The overproduction buffer affects the production penalty, not the fact that rejected value is tracked.

Estate taxable income may be used only as a proxy for sizing/debug. It is not the main monthly punishment.

## Current canonical US-10

US-10 resolves demand from stock. It does not own the stock and never mutates stock directly.

US-10 uses:

```txt
modeu5_resolve_stock_demand
```

US-10.1 handles consumption within one market. This is a stock-availability resolution, not intra-market trade.

Within one market, ModeU5 must not create:

```txt
trade income
transport cost
trade capacity usage
trade profit
trade-income reconciliation
```

US-10.2 handles inter-market stock transfers only when:

```txt
source_market != target_market
```

US-10.2 records `requested_quantity`, `transferred_quantity`, and `unsatisfied_quantity` separately for US-10.3 and diagnostics.

## Current canonical US-05

US-05 concerns only:

```txt
Stability Investment
Cost of the Court / Government Power when it produces Legitimacy
```

Target base:

```txt
modeu5_slider_cost_base = Wealth + Trade Income
```

US-05 uses direct formula replacement only. Monthly gold adjustments, modifiers that emulate a cost difference, and slider reconciliation are outside the selected design. If the Wealth value or the Stability/Court formula hook is unavailable, keep US-05 blocked rather than introducing a second implementation path.

## Debug requirement

Every feature must expose enough debug values to validate:

```txt
scope used
inputs read
quantity requested
quantity actual
quantity rejected or unsatisfied
mutation effect called
stock before
stock after
market stock difference
fallback used
economic adjustment applied
```

US-00 debug must show produced, added, rejected, ratios, buffer, penalty, good price source, void wealth, and aggregation.

US-10 debug must show ordered candidates, scores, exclusions, quantities used, satisfied quantity, and unsatisfied quantity.

When the Rebalance Economy package is loaded, US-05 debug must show the Wealth input, Trade Income input, resulting Economic Base, affected calculation, and whether direct replacement is active.

## Testing rule

Every PR must include:

```txt
manual test scenario
expected result
actual result
debug output inspected
error.log result
known limitation
TECH-01 entries updated
```

A PR is not complete if it only adds scripts without a test scenario.

## Git rule

Use small PRs. One PR should implement one testable layer, not necessarily one full user story.

Preferred branch names:

```txt
spike/engine-exposure
feature/core-stock-effects
feature/stock-validation
feature/monthly-stock-cycle
feature/void-economy-ledger
feature/void-production-penalty
feature/storage-capacity
feature/stock-demand-resolver
feature/consumption-resolution
feature/inter-market-transfer
feature/local-pop-demand-adaptation
feature/economic-base
balance/static-overrides
config/game-rules
```

## Do not widen MVP

Do not implement the following unless explicitly requested:

```txt
full building-level profit reconstruction
RGO-level profit reconstruction
complete custom GUI stock ledger
advanced AI economic planner
detailed logistics routes
transport queues
full replacement of vanilla markets
intra-market trade profit simulation
trade capacity consumption for same-market stock resolution
multiple competing fallback systems for one missing exposure
```

## When blocked

If a vanilla value is not exposed:

```txt
1. Do not invent it.
2. Search the wiki.
3. Search local script_docs.
4. Search vanilla files.
5. Record the result in TECH-01.
6. Propose one fallback.
7. Do not implement multiple fallback paths without approval.
```

If no reliable fallback exists, implement debug-only tracking or mark the item `OUT_OF_SCOPE`.

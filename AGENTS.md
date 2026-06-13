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
2. Apply global ModeU5 modifiers, including the +5% Production Efficiency compensation if enabled.
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
16. Calculate the US-05 Economic Base.
17. Display the US-05 formula inputs and result when exposure permits.
18. Validate stock consistency through modeu5_validate_stock_consistency.
19. Reset monthly counters only after every consumer has read them.
```

A yearly economic cycle must validate/rebuild stock aggregates, read annual satisfaction counters, apply US-04 demand adaptation, reset annual counters, and run diagnostics if enabled.

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
0. Spike engine exposure.
1. Bootstrap mod structure and documentation.
2. Core stock variables and centralized mutation effects.
3. US-11 validation / rebuild / consistency layer.
4. Debug conventions and deterministic test events.
5. Monthly and yearly on_actions.
6. US-01 country × market × good stock.
7. US-02 stock capacity.
8. US-03 monthly decay.
9. US-00.1 / US-00.2 / US-00.4 void economy measurement.
10. US-00.3 production penalty.
11. US-10.0 / US-10.1 / US-10.2 / US-10.3 demand resolution.
12. US-04 local Pop demand adaptation.
13. US-05 direct Economic Base formula.
14. US-07 / US-08 / US-09 static balance changes.
15. US-13 only after exposure is confirmed.
16. UI/debug polish.
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

US-05 debug must show the Wealth input, Trade Income input, resulting Economic Base, affected calculation, and whether direct replacement is active.

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
ui/debug-panel
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

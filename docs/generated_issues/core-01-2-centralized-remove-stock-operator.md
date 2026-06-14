# CORE-01.2 - Centralized remove-stock operator

Labels: none

## User Story

```txt
CORE-01.2 - Centralized remove-stock operator
```

As a ModeU5 feature author, I want one bounded remove operation so consumption and other justified losses can never remove more goods than a country actually holds.

## Functional objective

Implement `modeu5_remove_stock` to remove at most the available country stock, decrease the matching market aggregate by the same quantity, and expose the actual removed and unsatisfied quantities without introducing trade economics.

## Runtime position

```txt
Monthly step: called by stock consumers, principally step 9
Yearly step: none
Depends on counters from: explicit caller inputs and country stock
Feeds counters to: US-10.1, US-10.3, debug, CORE-01.6
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Country stock field | country x market x good | country-scoped `modeu5_<good>_stock_by_market` keyed by market | CONFIRMED | 007, 015 |
| Market aggregate | market x good | global per-good `modeu5_<good>_market_stock` keyed by market | FALLBACK_ACCEPTED | 007, 016 |
| Bounded arithmetic | transaction | `min`, `max`, subtract | CONFIRMED | 026 |
| Scope passing | scripted effect | explicit parameters plus saved country, market, and good scopes | CONFIRMED | 008 |
| Consumption removal | ModeU5 | `modeu5_remove_stock` | CONFIRMED | 075 |

## Persistent storage / variable-map contract

```txt
logical dimensions: country x market x good
logical record and fields read/written: stock
owner scope: country
tuple/key: market x good logical tuple; market scope physical key
confirmed physical map family: modeu5_<good>_stock_by_market
physical value type: numeric
default value: 0
write owner: modeu5_remove_stock for removals
readers: US-01/UI, US-03, US-10, US-11
reset/rebuild lifecycle: durable; market cache rebuilt by CORE-01.5
```

The market aggregate is the global `modeu5_<good>_market_stock[market]` cache. Requested, actual removed, unsatisfied, reason, and before/after values remain transaction-local except for debug snapshots.

## Files expected to change

```txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
in_game/common/scripted_effects/modeu5_debug_effects.txt
in_game/events/
main_menu/localization/english/
docs/tests/TEST_PLAN.md
docs/technical/DEBUG_CONVENTIONS.md
```

## Dependencies

```txt
Depends on: CORE-01.1 shared map helpers; TECH-01 007, 008, 015-016, 026, 075
Blocks: US-10.1, stock-loss callers
Related US: US-01, US-03, US-10.1, US-10.3, US-11
```

## Implementation rules

- Follow all mandatory project and storage-model rules.
- Require explicit `country`, `market`, `good`, `quantity_to_remove`, and `reason` inputs.
- Normalize the requested quantity to at least zero and log a negative request.
- Calculate `actual_removed_quantity = min(requested_quantity, max(0, stock_before))`.
- Calculate `unsatisfied_quantity = requested_quantity - actual_removed_quantity`.
- Calculate outputs before mutating either stock level.
- Decrease country stock and market aggregate by exactly the same actual quantity.
- Replace map entries through the shared remove/re-add helper.
- Do not create trade income, transport cost, trade capacity use, or profit.
- Keep caller-specific satisfaction counters outside this effect.
- If a pre-existing aggregate inconsistency would cause market underflow, log it and invoke the consistency path rather than independently clamping the market cache.
- Use generated per-good helpers or dispatch; never build a map name dynamically.

## CORE-specific boundary checks

- [ ] `reason` is diagnostic context, not permission to bypass bounds.
- [ ] Removing from an empty or missing stock is a no-op with the full request unsatisfied.
- [ ] Consumption in one market remains stock resolution, not intra-market trade.
- [ ] Decay uses CORE-01.4 and is not reported as consumer demand.

## Acceptance criteria

- [ ] A request below available stock is fully removed.
- [ ] A request above available stock removes only the available amount.
- [ ] No country or market stock becomes negative from this operation.
- [ ] Actual removed plus unsatisfied equals requested.
- [ ] Country and market stocks change by the same actual quantity.
- [ ] Debug includes reason, requested, actual, unsatisfied, before/after, and invariant difference.
- [ ] No trade or economic side effect is created.
- [ ] `error.log` has no new blocking error.

## Manual test scenario

### Setup

```txt
Country A, Market X, Good grain
Country stock = 30
Market stock = 30
quantity_to_remove = 50
reason = consumption
```

### Expected result

```txt
requested_quantity = 50
actual_removed_quantity = 30
unsatisfied_quantity = 20
country stock after = 0
market stock after = 0
stock difference after = 0
no trade economics created
```

## Known limitations

This operator removes stock from one explicit country record. Candidate selection and multi-stock demand resolution remain owned by US-10.0 and US-10.1.

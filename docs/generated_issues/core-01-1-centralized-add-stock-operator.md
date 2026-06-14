# CORE-01.1 - Centralized add-stock operator

Labels: none

## User Story

```txt
CORE-01.1 - Centralized add-stock operator
```

As a ModeU5 feature author, I want one capacity-aware add operation so production can enter country and market stocks without bypassing the double-accounting invariant.

## Functional objective

Implement `modeu5_add_stock` as the only operation that adds newly produced, gathered, or transformed goods to stock. It must calculate the stockable and rejected quantities before mutation, update the country source stock and market aggregate by the same actual quantity, and expose transaction outputs to US-00.1.

## Runtime position

```txt
Monthly step: 6-7
Yearly step: none
Depends on counters from: explicit caller inputs and the US-02 capacity field
Feeds counters to: US-00.1, debug, CORE-01.6
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Country stock field | country x market x good | country-scoped `modeu5_<good>_stock_by_market` keyed by market | CONFIRMED | 007, 015 |
| Country capacity field | country x market x good | country-scoped `modeu5_<good>_stock_cap_by_market` keyed by market | CONFIRMED | 007, 017 |
| Available capacity | transaction | `max(0, stock_cap - stock)` | CONFIRMED | 018, 026 |
| Market aggregate | market x good | market-scoped `modeu5_market_good_stock` keyed by goods scope | CONFIRMED | 007, 016 |
| Scope passing | scripted effect | explicit parameters plus saved country, market, and good scopes | CONFIRMED | 008 |
| Add/reject outputs | transaction | `modeu5_actual_added_quantity`, `modeu5_rejected_quantity` | CONFIRMED | 022-023 |

## Persistent storage / variable-map contract

```txt
logical dimensions: country x market x good
logical record and fields read: stock, capacity
logical record field written: stock
owner scope: country
tuple/key: market x good logical tuple; market scope physical key
confirmed physical map family:
  modeu5_<good>_stock_by_market
  modeu5_<good>_stock_cap_by_market
physical value type: numeric
default value: 0
write owner: modeu5_add_stock for additions; other CORE operators for their mutations
readers: US-00.1, US-01/UI, US-03, US-10, US-11
reset/rebuild lifecycle: stock is durable and never reset; market cache is rebuilt by CORE-01.5
```

The market aggregate is stored separately on market scope in `modeu5_market_good_stock[good]`. Requested, actual, rejected, before/after, and saved scopes remain transaction-local except for configured debug snapshots.

## Files expected to change

```txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
in_game/common/scripted_values/modeu5_stock_values.txt
in_game/common/scripted_effects/modeu5_debug_effects.txt
in_game/events/
in_game/localization/
docs/tests/TEST_PLAN.md
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
```

## Dependencies

```txt
Depends on: TECH-01 007, 008, 015-018, 022-023, 026; VARIABLE_MAP_STORAGE_MODEL
Blocks: CORE-01.2, CORE-01.3, CORE-01.4, CORE-01.5, US-01, US-00.1
Related US: US-01, US-02, US-00.1, US-11
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Treat missing stock and capacity entries as zero.
- Normalize the requested quantity to at least zero and log a negative request as invalid input.
- Calculate `available_capacity = max(0, capacity - stock_before)`.
- Calculate `actual_added_quantity = min(requested_quantity, available_capacity)`.
- Calculate `rejected_quantity = requested_quantity - actual_added_quantity`.
- Calculate all outputs before changing either stock level.
- Replace existing variable-map entries by read, remove, and re-add.
- Increase country stock and market aggregate by exactly `actual_added_quantity`.
- Do not write the US-00.1 ledger from this effect; expose outputs to its centralized ledger helper.
- Do not create wealth, income, trade, or transport effects.
- Use generated per-good helpers or generated dispatch; do not construct map names at runtime.
- Establish reusable internal read/replace helpers for the remaining CORE operators without exposing a second public stock-mutation path.
- Log a pre-existing negative or over-cap country stock. Do not silently discard pre-existing stock as part of an add transaction.

## CORE-specific boundary checks

- [ ] Rejected quantity remains outside all stock maps.
- [ ] Rejected quantity is exposed to US-00.1 but does not directly create a ledger write.
- [ ] A zero-capacity or full stock rejects the complete request.
- [ ] A no-op request does not remove and re-add unchanged entries unnecessarily.

## Acceptance criteria

- [ ] Full-capacity addition updates country and market stocks by the requested quantity.
- [ ] Partial-capacity addition updates both stocks by the same actual quantity and exposes the remainder as rejected.
- [ ] Stock never exceeds the capacity because of this operation.
- [ ] Missing entries use the documented zero default.
- [ ] Transaction outputs remain distinct: requested, actual added, and rejected.
- [ ] Debug exposes every mandatory stock-mutation field.
- [ ] A valid pre-operation invariant remains valid after the operation.
- [ ] No gameplay behavior depends on TECH-01 `088`.
- [ ] `error.log` has no new blocking error.

## Manual test scenario

### Setup

```txt
Country A, Market X, Good grain
Country stock = 80
Country capacity = 100
Market stock = 80
quantity_to_add = 50
```

### Expected result

```txt
requested_quantity = 50
available_capacity = 20
actual_added_quantity = 20
rejected_quantity = 30
country stock after = 100
market stock after = 100
stock difference after = 0
mutation_effect_called = modeu5_add_stock
```

## Known limitations

The public logical API is generic, but the confirmed physical country maps encode the good in a static map name. The implementation therefore requires generated per-good helpers or dispatch until a persistent record scope or nested map is confirmed under TECH-01 `088`.

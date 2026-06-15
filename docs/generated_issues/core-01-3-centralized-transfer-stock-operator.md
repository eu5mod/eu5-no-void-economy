# CORE-01.3 - Centralized transfer-stock operator

Labels: none

## User Story

```txt
CORE-01.3 - Centralized transfer-stock operator
```

As a ModeU5 feature author, I want one atomic transfer operation so ownership or market movement preserves stock quantity and both market aggregates.

## Functional objective

Implement `modeu5_transfer_stock` as one pre-calculated transaction always bounded by seller stock and normally bounded by buyer capacity. It must support an explicit `allow_over_capacity` target policy for CORE-03 succession, same-market ownership transfers, and capacity-enforced inter-market transfers for US-10.2 without implicit loss or trade-economic side effects.

## Runtime position

```txt
Monthly step: 11 when called by US-10.2
Yearly step: none
Depends on counters from: explicit seller, buyer, market, good, and requested quantity inputs
Feeds counters to: US-10.2, US-10.3, US-06 if restored, debug, CORE-01.6
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Seller and buyer stock fields | country x market x good | country-scoped per-good stock maps keyed by market | CONFIRMED | 007, 015 |
| Buyer capacity field | buyer x target market x good | country-scoped per-good capacity map keyed by target market | CONFIRMED | 007, 017-018 |
| Source and target aggregates | market x good | global per-good `modeu5_<good>_market_stock` keyed by market | FALLBACK_ACCEPTED | 007, 016 |
| Scope passing | scripted effect | saved seller, buyer, source market, target market, and good scopes | CONFIRMED | 008 |
| Bounded transfer arithmetic | transaction | `min`, `max`, subtract | CONFIRMED | 026 |
| Inter-market transfer operation | ModeU5 | `modeu5_transfer_stock` | CONFIRMED | 076 |
| Target capacity policy | transaction | `enforce` or explicitly authorized `allow_over_capacity` | CONFIRMED | 099 |

## Persistent storage / variable-map contract

```txt
logical dimensions: seller x source market x good; buyer x target market x good
logical record and fields read/written: seller stock, buyer stock; buyer capacity read-only
owner scope: seller country and buyer country
tuple/key: market x good logical tuple; market scope physical key
confirmed physical map family:
  modeu5_<good>_stock_by_market
  modeu5_<good>_stock_cap_by_market
physical value type: numeric
default value: 0
write owner: modeu5_transfer_stock for transfer mutations
readers: US-01/UI, US-10.2, US-11
reset/rebuild lifecycle: durable; affected market caches rebuilt by CORE-01.5
```

The source and target market aggregates use `modeu5_<good>_market_stock[market]`. All requested, transferred, unsatisfied, capacity, before/after, and transfer-mode values are transaction-local except for debug or explicitly owned downstream counters.

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
Depends on: CORE-01.1 shared map helpers; TECH-01 007, 008, 015-018, 026, 076, 099
Blocks: US-10.2
Related US: US-01, US-02, US-10.2, US-10.3, US-11
```

## Implementation rules

- Follow all mandatory project and storage-model rules.
- Require explicit seller, buyer, source market, target market, good, and requested quantity.
- Calculate target available capacity before any mutation.
- Default `target_capacity_policy` to `enforce`.
- Under `enforce`, calculate `actual_transferred_quantity = min(requested, seller_stock, target_available_capacity)`.
- Under `allow_over_capacity`, calculate `actual_transferred_quantity = min(requested, seller_stock)`.
- Calculate `unsatisfied_quantity = requested - actual_transferred_quantity`.
- Under `enforce`, do not remove stock that the target cannot accept; unsatisfied goods remain in seller stock.
- Under `allow_over_capacity`, target capacity creates no unsatisfied quantity; only seller shortage may do so.
- Replace all affected entries only after the complete transaction has been calculated.
- For different markets, decrease the source aggregate and increase the target aggregate by the same actual quantity.
- For the same market and different country records, update both country records and leave the market aggregate unchanged.
- Reject an exact source-record-to-same-source-record call as an invalid no-op: actual zero, full request unsatisfied, diagnostic reason recorded.
- Do not create transport loss, trade income, transport cost, trade capacity use, or profit.
- US-10.2 may call this effect only when `source_market != target_market`; same-market support exists for core ownership accounting and deterministic tests.
- CORE-03 must call same-market transfers with `target_capacity_policy = allow_over_capacity`.
- Never use `allow_over_capacity` for ordinary inter-market trade.
- Use a generated per-good EU5 persistence adapter containing complete literal map reads/writes; keep validation and arithmetic in the shared effect and do not assume runtime map-name construction.

## CORE-specific boundary checks

- [ ] Seller stock is always a hard bound.
- [ ] Buyer capacity is a hard bound under `enforce`.
- [ ] Buyer capacity does not truncate an authorized `allow_over_capacity` transfer.
- [ ] Same-market ownership transfer preserves the market aggregate.
- [ ] Inter-market transfer preserves global quantity across source and target.
- [ ] Unsatisfied quantity is not removed, lost, priced, or passed to transport-cost calculation as transferred quantity.

## Acceptance criteria

- [ ] Same-market transfer changes only seller and buyer country records.
- [ ] Inter-market transfer changes both country records and both market aggregates by the same quantity.
- [ ] Under `enforce`, partial transfer is bounded by the lesser of seller stock and buyer capacity.
- [ ] Requested, transferred, and unsatisfied quantities remain distinct.
- [ ] No stock becomes negative.
- [ ] `enforce` does not exceed buyer capacity; `allow_over_capacity` may do so and reports the resulting amount.
- [ ] No partial mutation remains if the calculated transfer is zero.
- [ ] Debug exposes all transfer-specific fields from `DEBUG_CONVENTIONS.md`.
- [ ] `error.log` has no new blocking error.

## Manual test scenario

### Setup

```txt
Seller A stock in Market X = 100
Buyer B stock in Market Y = 70
Buyer B capacity in Market Y = 100
Market X aggregate = 100
Market Y aggregate = 70
quantity_to_transfer = 50
```

### Expected result

```txt
target available capacity = 30
actual_transferred_quantity = 30
unsatisfied_quantity = 20
Seller A Market X stock = 70
Buyer B Market Y stock = 100
Market X aggregate = 70
Market Y aggregate = 100
both market differences = 0
```

### Authorized succession policy

```txt
Seller stock in Market X = 50
Buyer stock in Market X = 90
Buyer capacity in Market X = 100
quantity_to_transfer = 50
target_capacity_policy = allow_over_capacity
```

Expected:

```txt
actual_transferred_quantity = 50
unsatisfied_quantity = 0
seller stock after = 0
buyer stock after = 140
buyer over_capacity_after = 40
market aggregate unchanged
```

## Known limitations

This operator does not select sellers, infer vanilla trade quantity, or calculate economic trade effects. Those responsibilities remain outside the core transaction.

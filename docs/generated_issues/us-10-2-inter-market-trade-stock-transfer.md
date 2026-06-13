# US-10.2 — Inter-Market Trade Stock Transfer

Labels: `blocked:engine-exposure`

## User Story

```txt
US-10.2 — Inter-Market Trade Stock Transfer
```

As a player, I want inter-market trade to move actual goods from source stocks into buyer stock subject to availability and capacity.

## Functional objective

When `source_market != target_market`, select source-market sellers through US-10.0 and transfer only the minimum of seller stock, buyer target capacity, and remaining demand through `modeu5_transfer_stock`.

## Runtime position

```txt
Monthly step: 11, then handoff at step 12
Depends on counters from: US-10.0, US-02 capacity, trade request source
Feeds counters to: US-10.3 and US-06
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Source/target markets, good, request | trade/import/export or ModeU5 | exposed trade data | TO_TEST | 047-056 |
| Ordered source sellers | source market | US-10.0 output | TO_TEST | 067-074 |
| Buyer target capacity | ModeU5 | US-02/US-01 values | CONFIRMED | 017-018 |
| Central transfer | ModeU5 | `modeu5_transfer_stock` | CONFIRMED | 076 |

## Files expected to change

```txt
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-10.0, US-01, US-02, modeu5_transfer_stock, TECH-01
Blocks: actual-quantity transport costing in US-06
Related US: US-10.3, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Execute only when source and target markets differ.
- Search sellers only in the source market.
- Transfer through `modeu5_transfer_stock` only.
- Respect seller stock and buyer target capacity.
- Expose requested, actual transferred, and unsatisfied quantities.
- Do not calculate logistics, trade income, or trade-capacity use here.

## US-specific boundary checks

- [ ] No implicit transport loss is created in MVP.
- [ ] US-06 receives `transferred_quantity`, never requested or unsatisfied quantity.

## Acceptance criteria

- [ ] Same-market requests do not enter US-10.2.
- [ ] Multiple source sellers can fulfill one request in order.
- [ ] Seller/source stocks decrease and buyer/target stocks increase consistently.
- [ ] Buyer capacity is never exceeded.
- [ ] Unsatisfied quantity equals request minus actual transfer.
- [ ] All mutations use `modeu5_transfer_stock`.
- [ ] Debug shows markets, sellers, scores, capacity, quantities, and exclusions.

## Manual test scenario

### Setup

```txt
Source M1; target M2; request 100
Seller A stock 60; Seller B stock 30
Buyer target available capacity 70
```

### Expected result

```txt
Transferred 70; unsatisfied 30
Source aggregate falls 70; target aggregate rises 70
Buyer receives 70 without exceeding cap
US-06 cost basis output is 70
```

## Known limitations

Vanilla trade request/source/target/good exposure is `TO_TEST`. ModeU5-simulated requests may be used only as one approved fallback.

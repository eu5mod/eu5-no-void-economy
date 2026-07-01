# US-10.2 — Inter-Market Trade Stock Transfer

Labels: `blocked:engine-exposure`

## User Story

```txt
US-10.2 — Inter-Market Trade Stock Transfer
```

As a player, I want inter-market trade to move actual goods from source stocks into buyer stock subject to availability and capacity.

## Functional objective

When `source_market != target_market`, select source-market sellers through US-10.0 and transfer only the minimum of seller stock, buyer target capacity, and remaining demand through `modeu5_transfer_stock`.

## Current implementation slice

This PR implements the explicit-request MVP for US-10.2 on top of the US-10.0
resolver core:

- callers use `modeu5_resolve_inter_market_stock_transfer` with
  `buyer_country`, `source_market`, `target_market`, `good`, and
  `requested_quantity`;
- the generated per-good adapter rebuilds the source-market country cache,
  scans candidates once for aggregate diagnostics, then transfers stock by
  deterministic priority bucket;
- own/source stock is tried before subject/overlord, market-owner, and other
  foreign seller stock;
- zero/below-threshold stock, at-war candidates, embargoed candidates, and
  disallowed subject/market-owner/foreign buckets are excluded before mutation;
- the implementation fails closed for same-market requests;
- successful inter-market movement calls `modeu5_transfer_stock` only;
- buyer target capacity is enforced through the central transfer operator;
- requested, transferred, and unsatisfied quantities are exposed to US-10.3.

Full vanilla trade iteration remains gated by TECH-01 056. Until the exact
gameplay-script quantity is confirmed, deterministic tests use an explicit
ModeU5 request. Full score-based seller tie-breaking and exhaustive candidate UI
remain follow-up work; audit runtime emits bounded seller scan and mutation
traces in `debug.log`.

## Runtime position

```txt
Monthly step: 11
Depends on counters from: US-10.0, US-02 capacity, trade request source
Feeds counters to: US-10.3 and debug/UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Trade/import/export iteration | country/market → trade | every/ordered trade, import, and export iterators | CONFIRMED | 047-049 |
| Source/target markets and good | trade → market/goods | `from_market`, `to_market`, `traded_goods` | CONFIRMED | 054-055 |
| Actual/desired vanilla trade quantity | trade | script equivalent to GUI `Trade.GetQuantityOfGoodsActuallyMoved` and `Trade.GetDesiredGoodsToShip` | TO_TEST | 056 |
| Explicit ModeU5 request context | ModeU5 | source market, target market, good, requested quantity | CONFIRMED | internal |
| Ordered source sellers | source market | confirmed US-10.0 output | CONFIRMED | 067-074 |
| Buyer target capacity | ModeU5 | US-02/US-01 values | CONFIRMED | 017-018 |
| Central transfer | ModeU5 | `modeu5_transfer_stock` | CONFIRMED | 076 |
| Transaction state | current effect/event chain | local requested/remaining/transferred/unsatisfied values and saved trade scopes | CONFIRMED | 008, internal |


Note : Testing can be done via buy_goods_from_market if version EU 5  > 1.3

## Files expected to change

```txt
in_game/common/scripted_effects/
in_game/common/on_action/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-10.0, US-01, US-02, modeu5_transfer_stock, TECH-01
Blocks: complete inter-market stock resolution
Related US: US-10.3, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Execute only when source and target markets differ.
- Search sellers only in the source market.
- Transfer through `modeu5_transfer_stock` only.
- Respect seller stock and buyer target capacity.
- Expose requested, actual transferred, and unsatisfied quantities.
- Keep one transfer's arithmetic and candidate state local; persist outcomes only through US-10.3.
- Do not calculate logistics, trade income, or trade-capacity use here.

## US-specific boundary checks

- [ ] No implicit transport loss is created in MVP.
- [ ] `transferred_quantity` is recorded separately from requested and unsatisfied quantities.

## Acceptance criteria

- [ ] Same-market requests do not enter US-10.2.
- [x] Multiple source sellers can fulfill one request in bucket order.
- [ ] Seller/source stocks decrease and buyer/target stocks increase consistently.
- [ ] Buyer capacity is never exceeded.
- [ ] Unsatisfied quantity equals request minus actual transfer.
- [ ] All mutations use `modeu5_transfer_stock`.
- [x] Audit debug shows bounded per-candidate sellers, buckets, scores, quantities, and exclusions.

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
Recorded transferred quantity is 70
```

## Known limitations

Bucket ordering is implemented for explicit ModeU5 transfer requests. Vanilla
trade iteration, source/target markets, traded goods, and exact GUI quantity
accessors are documented in local vanilla files. Their gameplay-script
equivalents inside a trade iterator remain `TO_TEST`; explicit ModeU5 requests
may be used only as one approved fallback. Full score-based seller tie-breaking
remains follow-up work.

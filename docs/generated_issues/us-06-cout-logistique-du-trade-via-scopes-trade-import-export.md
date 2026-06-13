# US-06 — Coût logistique du trade via scopes Trade / Import / Export

Labels: `blocked:engine-exposure`

## User Story

```txt
US-06 — Coût logistique du trade via scopes Trade / Import / Export
```

As a player, I want distance and capacity to reduce effective trade profitability using the most granular exposed trade data.

## Functional objective

Attempt trade/import/export iteration, calculate transport cost from available data, prioritize actual US-10.2 transferred quantity, aggregate cost by payer country, and apply a visible monthly reconciliation by default.

## Runtime position

```txt
Monthly step: 13, then reconciliation at step 18
Depends on counters from: US-10.2 where associated
Feeds counters to: US-05 trade-income base, US-06-UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Trade/import/export iteration | country/market → trade | `every_trade`, `ordered_trade`, `every_import/export`, ordered variants | CONFIRMED | 047-049 |
| Trade income recipient | trade → country | `trade_income_recipient` | NOT_CONFIRMED | 050 |
| Trade owner | trade → country | `owner` | CONFIRMED | 051 |
| Buyer/seller country | trade → country | `buyer_country`, `seller_country` | NOT_CONFIRMED | 052-053 |
| Markets and goods | trade → market/goods | `from_market`, `to_market`, `traded_goods` | CONFIRMED | 054-055 |
| Per-trade quantity/capacity | trade | exposed quantity / `used_trade_capacity` | NOT_CONFIRMED | 056 |
| Per-trade distance/range | trade | `trade_distance`, numeric `trade_range` | NOT_CONFIRMED | 057-058 |
| Gross income per trade | trade | `gross_trade_income` / vanilla trade income | NOT_CONFIRMED | 059 |
| Direct trade-income reduction | trade | direct imputation effect | NOT_CONFIRMED | 060 |
| Monthly country reconciliation | country | sized `monthly_gold_expense` / `trade_income` modifier or `add_gold` | CONFIRMED | 061 |
| Actual transfer quantity | ModeU5 | US-10.2 output | CONFIRMED | 076 |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/common/modifiers/
in_game/events/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: TECH-01 trade spike; US-10.2 for ModeU5 transfers
Blocks: US-06-UI and transport-cost contribution to effective trade income
Related US: US-05, US-10.2
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- First attempt granular trade/import/export iteration.
- Use `transferred_quantity` when US-10.2 provides it; never charge unsatisfied demand.
- Default to monthly payer-country reconciliation.
- Use payer priority: recipient, owner, buyer, current country scope.
- Skip and log trades with no reliable payer or required data.
- Use only one accepted fallback for each blocked path and keep reconciliation visible.

## US-specific boundary checks

- [ ] Same-market stock consumption creates no transport cost.
- [ ] Direct trade-income imputation is optional, not required for MVP.
- [ ] Invalid/non-positive range yields zero cost and a debug flag.

## Acceptance criteria

- [ ] Exposed scopes are inspected at the most granular confirmed level.
- [ ] Cost uses the configured formula and actual transfer quantity when available.
- [ ] Missing data, payer, and imputation mode are logged per item.
- [ ] Monthly totals reconcile by payer country.
- [ ] No cost is calculated on unsatisfied demand.
- [ ] Reconciliation is visible and can reduce effective profitability below zero.
- [ ] TECH-01 and complete manual test evidence are updated.

## Manual test scenario

### Setup

```txt
Inter-market transfer requests 100 but transfers 60
Set confirmed capacity/distance/range inputs and known payer
Include one trade with missing payer/data
```

### Expected result

```txt
Cost basis is 60, never 100
Valid cost accumulates against the chosen payer
Missing-data trade is skipped/logged
Monthly reconciliation equals negative accumulated cost and is visible
```

## Known limitations

Trade iteration, trade owner, source/target markets, traded goods, and country-level reconciliation effects are documented. Recipient, buyer/seller, per-trade quantity, distance, range, gross income, and direct imputation remain `NOT_CONFIRMED`; use only the approved US-10 transfer or one documented proxy path.

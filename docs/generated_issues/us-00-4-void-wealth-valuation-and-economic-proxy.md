# US-00.4 — Void Wealth Valuation and Economic Proxy

Labels: none

## User Story

```txt
US-00.4 — Void Wealth Valuation and Economic Proxy
```

As a player, I want rejected production valued economically so the void economy can be displayed, balanced, and passed to relevant systems.

## Functional objective

Value rejected production per `country × market × good`, record the price source, and aggregate the result by market and country for diagnostics and balancing.

## Runtime position

```txt
Monthly step: 14
Depends on counters from: US-00.1
Feeds counters to: US-00-UI and balancing diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Rejected quantity output | country × market × good | US-00.1 accumulated stock-add results | CONFIRMED | 023-024, internal |
| Read keyed rejected entry | country-scoped per-good map keyed by market | <code>variable_map(name&#124;key)</code> | CONFIRMED | 007, 025 |
| Good price | market × good | `market_price`; fallback `default_price` / `default_market_price` | CONFIRMED | 030 |
| Estate tax-base proxy | country or estate | `estate_tax_base` | CONFIRMED | 031 |
| Estate tax-percentage proxy | country | `estate_tax_percentage` | CONFIRMED | 032 |
| Country/market aggregation | detailed ledger → market → country | variable maps and `change_variable` arithmetic | CONFIRMED | 007, 025-026 |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/events/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-00.1, good-price exposure, TECH-01
Blocks: complete void-economy visibility
Related US: US-00.3, US-00-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Default to `rejected_quantity × good_price × coefficient`.
- Record `good_price_source` for every valuation.
- Preserve the detailed level while also aggregating by market and country.
- Use Estate values only as optional sizing/debug proxies.
- Do not directly change stocks or Estate income.

## US-specific boundary checks

- [ ] Void wealth is tracked even when the overproduction buffer suppresses a penalty.
- [ ] `modeu5_total_void_wealth` is an aggregate, not a replacement for detailed records.
- [ ] Proxy data is not treated as the primary punishment.

## Acceptance criteria

- [ ] Detailed, market, and country void-wealth values reconcile.
- [ ] The selected price and source are visible.
- [ ] A fallback price is used only after explicit acceptance.
- [ ] Estate proxy values are optional and do not mutate income.
- [ ] Country and market aggregates are available to debug and balancing tools.
- [ ] Debug exposes rejected quantity, price, coefficient, proxy, and totals.
- [ ] TECH-01 and test evidence are updated.

## Manual test scenario

### Setup

```txt
Country A; Market M; Good iron
Rejected quantity 30; configured price 4; coefficient 1.00
Second good contributes void wealth 20 in the same market
```

### Expected result

```txt
Iron void wealth: 120
Market M aggregate: 140
Country total includes 140 plus any other markets
Price source is logged; no Estate income or stock is changed
```

## Known limitations

Market price, default goods price, Estate tax base, and Estate tax percentage are documented. Their runtime semantics and the chosen price fallback still require controlled testing and explicit debug identification.

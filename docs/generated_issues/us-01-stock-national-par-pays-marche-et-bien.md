# US-01 — Country stocks

Labels: none

## User Story

```txt
US-01 — Stock national par pays, marché et bien
```

As a player, I want each country to hold a separate stock for each good in each market it accesses.

## Functional objective

Define the country-level source-of-truth stock and capacity model at `country × market × good`, with market stock retained only as a derived aggregate/cache.

## Runtime position

```txt
Monthly step: read/write through centralized operations at steps 6-12
Yearly step: validated/rebuilt before annual consumers
Feeds counters to: US-00, US-02, US-03, US-10, US-11
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Country stock record field | country × market × good | logical record field `stock`; physical country-scoped `modeu5_<good>_stock_by_market` map keyed by market | CONFIRMED | 007, 015 |
| Market aggregate | market × good | logical `market_good_stock`; physical market-scoped `modeu5_market_good_stock` map keyed by goods scope | CONFIRMED | 007, 016 |
| Capacity and available capacity | country × market × good record | logical `capacity` field; physical `modeu5_<good>_stock_cap_by_market`; scripted capacity minus stock | CONFIRMED | 007, 017-018 |
| Market/good iteration and scope passing | none/effect → market/goods | `every_market_in_world`, `every_goods`, saved scopes | CONFIRMED | 002, 006, 008 |

## Variable-map storage pattern

Logical country × market × good record:

```txt
country_market_good_record = {
    stock
    capacity
    produced
    added
    rejected
    overproduction_ratio
    effective_overproduction_ratio
    void_wealth
    production_penalty
}
```

US-01 owns the `stock` field. US-02 owns capacity fields. US-00 owns its ledger, ratio, valuation, and penalty fields.

Confirmed physical stock field:

```txt
owner scope: country
map name:    modeu5_<good>_stock_by_market
key:         market scope
value:       numeric stock
default:     0
writers:     centralized stock effects only
```

Market aggregate/cache:

```txt
owner scope: market
map name:    modeu5_market_good_stock
key:         goods scope
value:       numeric aggregate stock
default:     0
rebuild:     sum country source records' stock fields
```

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: core centralized stock effects, TECH-01
Blocks: US-02, US-03, US-00, US-10, US-11
Related US: US-01-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Treat country stock as source of truth and market stock as aggregate/cache.
- Credit production to the same producing country and market key used by US-00.1.
- Keep production reading and country/market attribution in US-00.1; US-01 only accepts explicit stock-operation inputs.
- Mutate stock only through centralized stock effects.
- Enforce non-negative stock and capacity limits.
- Rebuild market stock from country stocks only, never the reverse.
- Treat missing stock and capacity entries as zero.
- Replace existing entries by remove/re-add inside their owning centralized effect.
- Do not construct per-good map names dynamically; use generated per-good helpers.
- Treat the physical map family as an implementation of one logical record, not as unrelated variables.
- Log requested, actual, rejected/unsatisfied, before/after, and invariant difference.

## US-specific boundary checks

- [ ] Production enters country stock through `modeu5_add_stock`.
- [ ] Production attribution is consistent between the stock destination and US-00.1 ledger.
- [ ] Rejected production does not create effective ModeU5 wealth.
- [ ] The data model distinguishes the same good in different markets.

## Acceptance criteria

- [ ] Separate country/market/good stocks can coexist without collision.
- [ ] Market aggregates use a market owner and goods key rather than duplicating country-map orientation.
- [ ] Stock cannot exceed capacity or remain negative.
- [ ] Every mutation updates the country source and market aggregate consistently.
- [ ] Rejected quantities are exposed to US-00.1.
- [ ] Validation restores `market_good_stock = sum(country_market_good_stock)`.
- [ ] Debug and test evidence satisfy project conventions.

## Manual test scenario

### Setup

```txt
Country A; Markets M1/M2; Good iron
M1 stock 80/cap 100; M2 stock 10/cap 50
Add 50 to M1 and 20 to M2 through modeu5_add_stock
```

### Expected result

```txt
M1 stock 100, added 20, rejected 30
M2 stock 30, added 20, rejected 0
Each market aggregate changes by the matching actual addition
```

## Known limitations

Variable maps, market/goods iteration, scope passing, stock capacity, and centralized stock-operation outputs are documented. Production reading remains isolated in US-00.1 and does not block the US-01 stock model.

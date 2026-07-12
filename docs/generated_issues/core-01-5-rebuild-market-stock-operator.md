# CORE-01.5 - Rebuild market-stock aggregate operator

Labels: none

## User Story

```txt
CORE-01.5 - Rebuild market-stock aggregate operator
```

As a ModeU5 maintainer, I want one rebuild operation so a market-good cache can always be reconstructed from authoritative country stocks.

## Functional objective

Implement `modeu5_rebuild_market_stock_from_country_stocks` for one market and good. It must sum the matching country stock entries, replace only the market aggregate, and expose the previous value, expected value, and correction.

## Runtime position

```txt
Monthly step: only when requested by CORE-01.6 or exceptional recovery
Yearly step: 1-2 safety rebuild when needed
Depends on counters from: all country stock records for the selected market and good
Feeds counters to: CORE-01.6, US-11 diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Iterate countries | none/effect | `every_country` | CONFIRMED | 001 |
| Country stock field | country x market x good | country-scoped per-good stock map keyed by saved market | CONFIRMED | 007, 015 |
| Market aggregate | market x good | global per-good `modeu5_<good>_market_stock` keyed by saved market | FALLBACK_ACCEPTED | 007, 016 |
| Scope passing | scripted effect | saved market and good scopes across country iteration | CONFIRMED | 008 |
| Transaction-local accumulator | country controller | `set_local_variable`, `change_local_variable`, `local_var:<name>` | CONFIRMED | 109 |
| Rebuild operation | ModeU5 | `modeu5_rebuild_market_stock_from_country_stocks` | CONFIRMED | 019 |

## Persistent storage / variable-map contract

```txt
logical dimensions: market x good
logical record and fields read: every country record's stock field
logical record field written: market aggregate stock
owner scope: global variable system
tuple/key: market scope in one static map per good
confirmed physical map family: modeu5_<good>_market_stock
physical value type: numeric
default value: 0
write owner: modeu5_rebuild_market_stock_from_country_stocks for rebuild correction
readers: stock operations, US-01/UI, US-10, US-11
reset/rebuild lifecycle: replace on initialization, exceptional recovery, validation failure, or four-year safety pass
```

The country source maps remain country-scoped `modeu5_<good>_stock_by_market[market]`. Sum, previous aggregate, correction, and anomaly details remain transaction-local except for debug snapshots.

## Files expected to change

```txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
in_game/common/scripted_effects/modeu5_debug_effects.txt
in_game/common/scripted_effects/modeu5_stock_test_effects.txt
in_game/events/
in_game/localization/
tools/templates/modeu5_stock_good_adapter.template.txt
docs/tests/TEST_PLAN.md
docs/technical/DEBUG_CONVENTIONS.md
```

## Dependencies

```txt
Depends on: CORE-01.1 shared map helpers; TECH-01 001, 007-008, 015-016, 019, 104, 109
Blocks: CORE-01.6, US-11 recovery
Related US: US-01, US-11
```

## Implementation rules

- Follow all mandatory project and storage-model rules.
- Accept one explicit market and good per call.
- Save the market and good scopes before country iteration.
- Iterate countries and treat a missing matching country stock entry as zero.
- Iterate every country, not only countries currently owning a location in the
  market; durable country stock can survive territorial loss.
- Sum the country stock source fields; do not derive the value from production, capacity, ledger, or the previous market aggregate.
- Replace only `modeu5_<good>_market_stock[market]` for the selected market.
- Never modify, proportionally rescale, or infer any country stock from the aggregate.
- Use read, remove, and re-add to replace the market aggregate key.
- Do not create consumption, loss, transfer, wealth, or income.
- Detect and prominently log a negative country source entry. Source correction remains owned by centralized country-stock operations, not by rebuild.
- Use generated per-good source readers because country stock map names are static per good.

## CORE-specific boundary checks

- [ ] Countries without the map key contribute zero.
- [ ] Over-cap but non-negative country stock remains part of the authoritative sum.
- [ ] Rebuild changes exactly one selected market-good aggregate per call.
- [ ] Rebuild does not claim to validate or repair country-source anomalies.

## Acceptance criteria

- [ ] The rebuilt aggregate equals the exact sum of matching country stocks.
- [ ] Country stock entries are byte-for-byte/logically unchanged.
- [ ] A missing aggregate key is created with the calculated sum.
- [ ] An existing aggregate key is replaced rather than duplicated.
- [ ] Debug exposes market, good, old aggregate, expected aggregate, correction, and source anomalies.
- [ ] No economic side effect is created.
- [ ] `error.log` has no new blocking error.

## Manual test scenario

### Setup

```txt
Market X, Good wheat
Country A stock = 100
Country B stock = 50
all other country entries missing or zero
Market X aggregate deliberately set to 200
```

### Expected result

```txt
expected market stock = 150
old market stock = 200
correction = -50
new market stock = 150
Country A remains 100
Country B remains 50
```

## Known limitations

The rebuild repairs only the aggregate/cache. It reports invalid country source
values but cannot invent an economically justified country-stock correction.
Each market-good rebuild scans all countries, including countries with missing
keys, so US-11 must schedule tuple iteration once and avoid duplicating a
world-wide rebuild from every country pulse.

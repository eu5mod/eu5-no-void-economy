# CORE-01.4 - Centralized decay-stock operator

Labels: none

## User Story

```txt
CORE-01.4 - Centralized decay-stock operator
```

As a ModeU5 feature author, I want stock decay to use one dedicated operation so storage loss is calculated on country stock and mirrored exactly in the market aggregate.

## Functional objective

Implement `modeu5_decay_stock` for one explicit country, market, and good record. It must calculate decay from the country source stock, update the country and market values by the same quantity, and expose the loss without treating it as unsatisfied demand.

## Runtime position

```txt
Monthly step: 14, called by US-03
Yearly step: none
Depends on counters from: country stock and configured/caller decay rate
Feeds counters to: US-03-UI/debug, CORE-01.6
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Country stock field | country x market x good | country-scoped per-good stock map keyed by market | CONFIRMED | 007, 015 |
| Market aggregate | market x good | global per-good `modeu5_<good>_market_stock` keyed by market | FALLBACK_ACCEPTED | 007, 016 |
| Decay arithmetic | transaction | multiply plus bounded min/max | CONFIRMED | 026 |
| Fractional precision and persistence | transaction / variable map | controlled fractional arithmetic and map write/read probe | TO_TEST | 113 |
| Monthly invocation | country | caller orchestration through `monthly_country_pulse` | CONFIRMED | 011 |
| Scope passing | scripted effect | saved country, market, and good scopes | CONFIRMED | 008 |

## Persistent storage / variable-map contract

```txt
logical dimensions: country x market x good
logical record and fields read/written: stock
owner scope: country
tuple/key: market x good logical tuple; market scope physical key
confirmed physical map family: modeu5_<good>_stock_by_market
physical value type: numeric
default value: 0
write owner: modeu5_decay_stock for decay mutations
readers: US-01/UI, US-03/UI, US-11
reset/rebuild lifecycle: durable; market cache rebuilt by CORE-01.5
```

`decay_rate`, `stock_before`, `decayed_quantity`, and `stock_after` are transaction-local. No separate durable decay-state map is created.

## Files expected to change

```txt
in_game/common/script_values/modeu5_stock_values.txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
in_game/common/scripted_effects/modeu5_debug_effects.txt
in_game/events/
main_menu/localization/english/
docs/tests/TEST_PLAN.md
docs/technical/DEBUG_CONVENTIONS.md
```

## Dependencies

```txt
Depends on: CORE-01.1 shared map helpers; TECH-01 007, 008, 011, 015-016, 026, 104, 105, 108, 113
Blocks: US-03
Related US: US-01, US-03, US-03-UI, US-11
```

## Implementation rules

- Follow all mandatory project and storage-model rules.
- Operate on one country, market, and good record per call; US-03 owns iteration and scheduling.
- Use the caller rate when provided; callers that want the configured default
  must pass `decay_rate = modeu5_default_monthly_decay_rate` explicitly to
  `modeu5_decay_stock`.
- Do not reintroduce a per-good `modeu5_decay_stock_default` dispatch layer:
  EU5's static analyzer reports its saved default scopes as unset even when the
  runtime wrapper would set them, creating avoidable non-blocking log noise.
- Bound the effective decay rate to `[0, 1]` and log an out-of-range input.
- Apply TECH-01 108 literally: use EU5 `min = 0` for the lower bound and
  `max = 1` for the upper bound.
- Calculate `decayed_quantity = min(stock_before, stock_before * effective_decay_rate)`.
- Calculate the loss from country stock only; never calculate a second independent decay from market stock.
- Decrease country stock and market aggregate by exactly the same decayed quantity.
- Keep decay diagnostics separate from consumer `unsatisfied_quantity`.
- Do not create wealth, demand, trade, or transport effects.
- Use a generated per-good EU5 persistence adapter containing complete literal map reads/writes; keep validation and arithmetic in the shared effect.

## CORE-specific boundary checks

- [ ] Zero stock and zero decay are no-ops.
- [ ] A 100 percent decay reaches zero but never becomes negative.
- [ ] Market decay is the sum of country-level losses, not a market-level percentage calculation.
- [ ] US-03 controls when and how often the operator is called.

## Acceptance criteria

- [ ] A 1 percent decay changes stock 100 to 99 for each affected country record.
- [ ] The market aggregate decreases by the exact sum of country decayed quantities.
- [ ] No stock becomes negative.
- [ ] No durable duplicate decay state is introduced.
- [ ] Debug exposes rate, before, decayed, after, market change, and invariant difference.
- [ ] The operation does not increment unsatisfied-demand counters.
- [ ] `error.log` has no new blocking error.

## Manual test scenario

### Setup

```txt
Country A stock in Market X = 100
Country B stock in Market X = 100
Market X aggregate = 200
decay rate = 0.01
Call the operator once for each country record
```

### Expected result

```txt
Country A decayed = 1; stock after = 99
Country B decayed = 1; stock after = 99
Market X aggregate after = 198
stock difference after = 0
```

## Known limitations

The core operator does not discover records or schedule itself. Complete monthly coverage across countries, markets, and goods remains the responsibility of US-03 and its confirmed pulse/iteration implementation.

EU5's fractional precision and map-persistence rounding are not documented.
The current `100 * 0.1 = 10` deterministic fixture has low rounding risk but
does not prove arbitrary fractional decay. If it fails, inspect the raw decay
operands and results according to
`docs/technical/NUMERIC_PRECISION_AND_TEST_DIAGNOSTICS.md` before changing the
formula or adding a tolerance.

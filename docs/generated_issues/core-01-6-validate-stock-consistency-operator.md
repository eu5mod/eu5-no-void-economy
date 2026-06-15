# CORE-01.6 - Validate stock consistency operator

Labels: none

## User Story

```txt
CORE-01.6 - Validate stock consistency operator
```

As a ModeU5 maintainer, I want one validation operation so every market-good divergence is detected, classified, logged, and repaired from country source stocks.

## Functional objective

Implement `modeu5_validate_stock_consistency` for one market and good. It must compare the market aggregate with the sum of country stocks, do nothing when equal, call CORE-01.5 when different, and verify that the post-rebuild difference is zero.

## Runtime position

```txt
Monthly step: 18 after all economic stock mutations
Yearly step: 1 before annual stock consumers
Depends on counters from: all centralized stock operations
Feeds counters to: US-11 diagnostics and safe downstream reads
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Iterate countries | none/effect | `every_country` | CONFIRMED | 001 |
| Country source stock | country x market x good | country-scoped per-good stock map keyed by market | CONFIRMED | 007, 015 |
| Market aggregate | market x good | global per-good `modeu5_<good>_market_stock` keyed by market | FALLBACK_ACCEPTED | 007, 016 |
| Scope passing | scripted effect | saved market and good scopes | CONFIRMED | 008 |
| Transaction-local accumulator | country controller | `set_local_variable`, `change_local_variable`, `local_var:<name>` | CONFIRMED | 109 |
| Rebuild effect | ModeU5 | `modeu5_rebuild_market_stock_from_country_stocks` | CONFIRMED | 019 |
| Validation effect | ModeU5 | `modeu5_validate_stock_consistency` | CONFIRMED | 020 |
| Monthly/yearly orchestration | country | `monthly_country_pulse`, `yearly_country_pulse` owned by US-11/on-actions | CONFIRMED | 011-012 |

## Persistent storage / variable-map contract

```txt
logical dimensions: market x good
logical record and fields read: country stock source fields and market aggregate
logical record fields written: none directly; correction delegates to CORE-01.5
owner scope: global variable system
tuple/key: market scope in one static map per good
confirmed physical map family: modeu5_<good>_market_stock
physical value type: numeric
default value: 0
write owner: CORE-01.5 when validation requests rebuild
readers: US-11 diagnostics
reset/rebuild lifecycle: validate after major operations; rebuild only on a detected difference
```

Expected stock, actual stock, difference, severity, rebuild-called flag, and post-rebuild difference are transaction-local except for the documented debug snapshot.

## Files expected to change

```txt
in_game/common/script_values/modeu5_stock_values.txt
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
Depends on: CORE-01.5; TECH-01 001, 007-008, 011-012, 015-016, 019-020, 104, 109-110
Blocks: US-11 completion and safe monthly/yearly stock cycles
Related US: US-01, US-03, US-10, US-11
```

## Implementation rules

- Follow all mandatory project and storage-model rules.
- Accept one explicit market and good per call; US-11 owns global iteration and scheduling.
- Calculate `expected_market_stock = sum(country_market_good_stock)`.
- Calculate `stock_difference = actual_market_stock - expected_market_stock`.
- If the difference is exactly zero, do not rewrite the aggregate.
- If the difference is nonzero, record the inconsistency and call `modeu5_rebuild_market_stock_from_country_stocks`.
- Use a configurable diagnostic threshold only to classify/promote the log severity, never to decide whether a nonzero difference is repaired.
- Re-read the aggregate after rebuild and assert that the post-rebuild difference is zero.
- Never repair country stock from market stock.
- Never directly write the aggregate from the validation effect; delegate correction to CORE-01.5.
- Report negative country source values as invalid.
- Report over-cap country source values separately as valid diagnostic state when produced by CORE-02/CORE-03; validation must not delete or clamp them.
- Route any future approved over-cap correction through the owning centralized operation.
- Do not create or destroy wealth, consumption, transfer, or demand.

## CORE-specific boundary checks

- [ ] A consistent record is a read-only no-op.
- [ ] Small and large nonzero differences are both rebuilt.
- [ ] Large differences receive prominent debug output.
- [ ] Validation failure after rebuild is reported as a blocking diagnostic.

## Acceptance criteria

- [ ] Deliberate market-cache corruption is detected.
- [ ] Validation identifies the market, good, expected value, actual value, and signed difference.
- [ ] Any nonzero difference calls CORE-01.5 and is corrected.
- [ ] Country stocks remain unchanged.
- [ ] Over-cap country stock remains included in the expected market aggregate and is not treated as an accounting divergence.
- [ ] A second validation is a no-op with difference zero.
- [ ] Debug records whether rebuild was called and the post-rebuild result.
- [ ] Monthly and yearly orchestration cannot run duplicate global validation unintentionally from every country pulse.
- [ ] `error.log` has no new blocking error.

## Manual test scenario

### Setup

```txt
Country A stock in Market X for wheat = 100
Country B stock in Market X for wheat = 50
Market X wheat aggregate deliberately set to 200
Run modeu5_validate_stock_consistency for Market X and wheat
```

### Expected result

```txt
expected market stock = 150
actual market stock before = 200
stock difference before = 50
inconsistency detected = yes
rebuild called = yes
actual market stock after = 150
stock difference after = 0
country stocks unchanged
```

## Known limitations

Validation reconciles the market cache only. Negative country records are
invalid and require an explicit correction through the operation that owns that
change. Over-cap records are diagnostic state, not an accounting inconsistency.
Validation scans all country source records for one market-good tuple; US-11
must own and de-duplicate global scheduling.

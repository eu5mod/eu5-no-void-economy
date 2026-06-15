# Numeric Precision and Test Diagnostics

## Status

EU5 documentation confirms that variables and script values can contain
numeric values, and several documented triggers describe their inputs as
`float` or `real`. It does not document:

```txt
internal numeric representation
number of decimal places retained
rounding mode
variable-map serialization precision
accumulator precision
an approximate-equality comparator
```

Therefore numeric precision is an engine exposure that requires a controlled
runtime test. Do not assume IEEE floating-point behavior, fixed-point behavior,
or exact decimal preservation.

## Current CORE-01 risk

The existing deterministic CORE-01 fixtures are intentionally dominated by
integers. Their rounding risk is low:

```txt
add/remove/transfer quantities: integers
rebuild fixture: 100 + 50 = 150
validation corruption: 200 - 150 = 50
```

The decay test is the first fractional path:

```txt
stock = 100
decay rate = 0.1
expected decay = 10
```

This product often remains exact after engine rounding, so it is not a strong
precision probe. A PASS does not prove that arbitrary fractional decay is
exact.

## Sensitive locations

### Deterministic assertions

`modeu5_stock_test_effects.txt` uses exact equality for expected values.
Fractional results can produce a false negative even when the economic result
is acceptable.

Start with these values when only the decay test fails:

```txt
modeu5_decay_rate_raw
modeu5_decay_rate
modeu5_country_stock_before
modeu5_decayed_quantity
modeu5_country_stock_after
modeu5_market_stock_before
modeu5_market_stock_after
modeu5_stock_difference_after
```

### Validation and rebuild

CORE-01.6 currently treats every nonzero difference as an inconsistency. That
is the correct accounting contract, but a tiny residual can appear if:

```txt
country stocks were accumulated in a different order from market mutations
variable-map storage rounds values on write
an iterator accumulator retains different precision from a persisted map
```

Start with:

```txt
modeu5_validation_expected_market_stock
modeu5_validation_actual_market_stock_before
modeu5_validation_difference_before
modeu5_validation_actual_market_stock_after
modeu5_validation_difference_after
modeu5_rebuild_correction_applied
```

If a rebuild succeeds but `difference_after` remains a very small nonzero
value, test map-write/read precision before changing the invariant.

### Underflow guards

Remove, inter-market transfer, and decay fail closed when the market aggregate
is smaller than the requested country-side mutation. A tiny precision residue
can therefore block an otherwise valid transaction.

Start with:

```txt
market_stock_before
country_stock_before
quantity_requested
quantity_actual
consistency_validation_required
validation_difference_before
```

Run CORE-01.6 immediately. If rebuild removes the failure, investigate numeric
drift or operation ordering before weakening the guard.

## Controlled precision probe

Before introducing any epsilon, add a deterministic probe that records raw
values for:

```txt
3 * 0.1
1 / 3
three additions of 0.1
one subtraction of 0.3
map write followed by map read
iterator sum of repeated fractional values
```

Repeat the probe after save/reload. Record the smallest stable nonzero
difference observed in `error.log`, `game.log`, and debug variables.

## Epsilon policy

Do not introduce one global epsilon for every numeric decision.

Three policies must be considered independently:

```txt
test assertion tolerance
  prevents false-negative tests

diagnostic classification tolerance
  distinguishes visible drift from a prominent inconsistency

gameplay mutation tolerance
  changes whether stock is added, removed, transferred, or blocked
```

A test-only tolerance may be acceptable after the precision probe. A gameplay
tolerance is a business-rule change and requires explicit approval.

Do not silently clamp or ignore a residual in CORE-01.6. Country stock remains
the source of truth. Until engine precision is measured, rebuild every nonzero
difference and preserve the raw signed difference in debug.

## Debugging order

When a deterministic test unexpectedly fails:

1. Confirm the installed branch and commit through `MODEU5_SOURCE.txt`.
2. Confirm no stale duplicate mod is loaded.
3. Inspect the raw operands and calculated result listed above.
4. Determine whether the failure is an exact-value assertion, an underflow
   guard, or a post-rebuild consistency failure.
5. Reproduce with integer-only values.
6. Reproduce with the controlled fractional precision probe.
7. Review map values before and after one write/read cycle.
8. Only then propose a test tolerance or gameplay change.

Do not diagnose a precision problem from one failed PASS marker alone.

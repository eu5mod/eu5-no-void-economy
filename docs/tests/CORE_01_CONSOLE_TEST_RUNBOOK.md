# CORE-01 Console Test Runbook

Use this procedure to test all six CORE-01 stock operators.

## Before starting EU5

Close EU5, then run these commands from the repository:

```bash
./tools/generate_stock_good_helpers.sh
./tools/generate_us09_economy_overrides.sh 5
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Confirm that every installed `MODEU5_SOURCE.txt` points to this repository,
branch, and commit. Remove or disable any older real directory or launcher entry
that can shadow `modeu5_core`; a stale duplicate can load different scripts
even when the development checkout is correct.

In the launcher:

```txt
Enable: No Void Economy / modeu5_core
Enable for this validation run only: No Void Economy Tests / modeu5_core_tests
Do not simultaneously enable the older eu5voideco alias.
The three optional gameplay ModeU5 packages may remain enabled.
```

Start a clean 1337 campaign. FRA and ENG must exist for the transfer tests.

## Console command

This is the only test command to enter in the EU5 console:

```txt
event modeu5_debug.1
```

Do not enter any of the following:

```txt
modeu5_test_*_passed
trigger "var:modeu5_test_*_passed = 1"
trigger "global_var:modeu5_test_*_passed = 1"
```

The `modeu5_test_*` names are internal result markers, not console commands.

## Test A: add, remove, and decay

1. Enter:

```txt
event modeu5_debug.1
```

2. Select:

```txt
Test add, remove, and decay
```

3. The console/test log must show the suite starting and finishing, and the result event must display:

```txt
PASS - Add with allow_over_capacity
PASS - Add with enforced capacity
PASS - Remove stock
PASS - Decay stock
```

Transfer rows will display `FAIL / NOT RUN`. This is expected because this
action clears previous markers and does not execute transfer tests.

## Test B: same-market transfers

1. Close the result event.
2. Enter again:

```txt
event modeu5_debug.1
```

3. Select:

```txt
Test same-market transfers
```

4. The console/test log must show the suite starting and finishing, and the result event must display:

```txt
PASS - Same-market transfer
PASS - Invalid same-record transfer rejected
```

Add, remove, decay, and inter-market rows will display `FAIL / NOT RUN`. This
is expected.

The invalid transfer is reported through the debug snapshot. It must not add an
`error.log` entry.

## Test C: inter-market transfer

1. Close the result event.
2. Enter again:

```txt
event modeu5_debug.1
```

3. Select:

```txt
Test inter-market transfer
```

4. The console/test log must show the suite starting and finishing, and the result event must display:

```txt
PASS - Inter-market transfer
```

All other rows will display `FAIL / NOT RUN`. This is expected.

If FRA and ENG capitals are in the same market in the selected setup, this test
cannot run meaningfully; use a clean 1337 campaign where their capital markets
differ.

## Test D: rebuild and validation

1. Close the result event.
2. Enter again:

```txt
event modeu5_debug.1
```

3. Select:

```txt
Test rebuild and consistency validation
```

4. The result event must display:

```txt
PASS - Rebuild market aggregate
PASS - Validation detects and repairs divergence
PASS - Consistent validation is a no-op
```

The test creates FRA = 100 and ENG = 50 wheat in FRA's market, injects a
test-only aggregate value of 200, rebuilds it to 150, corrupts it again, and
verifies that validation delegates repair to rebuild. Country stocks must
remain unchanged.

## Test E: US-11 dirty reconciliation

1. Close the result event.
2. Enter again:

```txt
event modeu5_debug.1
```

3. Select:

```txt
Test US-11 dirty-record reconciliation
```

4. The result event must display:

```txt
PASS - Dirty market-good reconciliation
PASS - Empty reconciliation is a no-op
```

The first pass creates FRA = 100 and ENG = 50 wheat in FRA's market, corrupts
the market aggregate to 200, and must report:

```txt
records checked = 1
inconsistencies = 1
rebuilds = 1
failures = 0
market aggregate = 150
```

The second pass runs without another mutation and must report zero for every
counter.

## Numeric precision warning

The current fixtures mostly use integer quantities. The decay fixture uses
`100 * 0.1 = 10`, which is not sufficient to characterize arbitrary
fractional arithmetic.

If only decay or consistency assertions fail, do not immediately weaken the
stock invariant. Inspect the raw values listed in:

```txt
docs/technical/NUMERIC_PRECISION_AND_TEST_DIAGNOSTICS.md
```

In particular, compare the calculated decay and the signed validation
difference before and after rebuild. A very small nonzero result may indicate
engine precision, map persistence, or accumulation order; it may also expose a
real accounting error. The controlled precision probe must distinguish these
cases before an epsilon is introduced.

## Log review

After all five tests, close EU5 before reviewing:

```txt
Documents/Paradox Interactive/Europa Universalis V/logs/error.log
Documents/Paradox Interactive/Europa Universalis V/logs/game.log
Documents/Paradox Interactive/Europa Universalis V/logs/system.log
```

Search for logged ModeU5 diagnostics and test-log lines:

```bash
rg -n 'ModeU5|modeu5|malformed|Script system error|modeu5_core_01' \
  "$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/error.log" \
  "$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/game.log"
```

The test is successful when:

```txt
All expected PASS rows appear.
The console/test log shows each selected suite starting, finishing, and each executed test PASS/FAIL result.
No "deterministic CORE-01 ... test failed" message appears.
No modeu5 map identifier contains a remaining "$".
No result marker reports "Failed to fetch variable".
No expected business-rule rejection adds a CORE-01 error diagnostic.
```

Static `used but is never set` warnings with a correctly formed literal map name
do not alone prove that a runtime operation failed. Any map identifier retaining
`$`, such as `modeu5wheat$_stock_by_market`, is invalid and must be reported.

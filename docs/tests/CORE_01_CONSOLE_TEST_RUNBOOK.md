# CORE-01 Console Test Runbook

Use this procedure to test `modeu5_add_stock`, `modeu5_remove_stock`,
`modeu5_transfer_stock`, and `modeu5_decay_stock`.

## Before starting EU5

Close EU5, then run these commands from the repository:

```bash
./tools/generate_stock_good_helpers.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

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

The following diagnostic in `error.log` is expected for this test:

```txt
ModeU5 modeu5_transfer_stock rejected an exact source-record-to-source-record transfer.
```

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

## Log review

After all three tests, close EU5 before reviewing:

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
The expected invalid same-record rejection is the only CORE-01 error diagnostic.
```

Static `used but is never set` warnings with a correctly formed literal map name
do not alone prove that a runtime operation failed. Any map identifier retaining
`$`, such as `modeu5wheat$_stock_by_market`, is invalid and must be reported.

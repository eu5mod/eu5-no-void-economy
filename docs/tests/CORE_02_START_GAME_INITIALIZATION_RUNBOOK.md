# CORE-02 Start-game Initialization Runbook

This runbook validates the CORE-02 implementation layer. It is distinct from
`CORE_02_OPENING_STOCK_EXPOSURE_RUNBOOK.md`, which only proves that the
opening vanilla market stock value is exposed.

## Install

Close EU5, then run:

```bash
./tools/generate_stock_good_helpers.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Confirm that `MODEU5_SOURCE.txt` for No Void Economy and No Void Economy Tests
points to the CORE-02 implementation branch and commit being tested.

## Timing rule

CORE-02 startup/integration tests are delayed by at least one in-game day.
The implementation is wired as:

```txt
on_game_start -> delay = { days = 1 } -> modeu5_start_game_stock_initialization_dispatcher
```

Do not inspect startup state, run the startup probe, or judge the startup logs
on campaign day 0. Unpause and let at least one full daily tick complete first.
For quieter logs, wait until the next day is visible in the UI before running
console tests or reviewing `error.log` and `game.log`.

## Deterministic allocation test

1. Enable No Void Economy and No Void Economy Tests in a dedicated playset.
2. Start a clean 1337 campaign.
3. Let at least one full in-game day pass so delayed startup work has settled.
4. Open the console and run:

```txt
event modeu5_debug.1
```

5. Select:

```txt
Run CORE-02 initialization allocation tests
```

## Expected result

The result event must show:

```txt
PASS - CORE-02 proportional opening allocation
PASS - CORE-02 over-capacity opening allocation
```

The test fixture injects wheat capacity for FRA and ENG in FRA's capital
market, seeds a controlled opening quantity through `modeu5_seed_opening_market_good`,
and verifies:

```txt
Scenario 1:
FRA capacity = 100
ENG capacity = 300
Opening wheat = 200
FRA stock = 50
ENG stock = 150
Market stock = 200

Scenario 2:
FRA capacity = 40
ENG capacity = 60
Opening wheat = 150
FRA stock = 60
ENG stock = 90
Market stock = 150
```

Both scenarios must leave `modeu5_initialization_failure_detected` absent and
must use `modeu5_add_stock` with `capacity_policy = allow_over_capacity`.

## Full startup check

The full `on_game_start -> delay 1 day -> modeu5_start_game_stock_initialization_dispatcher`
path depends on US-02 capacity maps being populated with positive capacity. A
clean campaign with positive vanilla opening stock and zero ModeU5 capacity is
expected to fail closed rather than invent a fallback allocation.

Expected fail-closed markers in that case:

```txt
modeu5_initialization_state = -1
modeu5_initialization_failure_detected = yes
modeu5_initialization_zero_capacity_failures > 0
```

This is not a CORE-02 allocation failure. It means the lifecycle guard is doing
the conservative thing while capacity exposure or capacity calculation produced
no eligible recipient.

## Log review

Review:

```txt
error.log
system.log
```

Passing deterministic tests should show the CORE-02 PASS lines in the result
event and set `modeu5_test_core02_initialization_started`,
`modeu5_test_core02_initialization_finished`,
`modeu5_test_core02_proportional_passed`, and
`modeu5_test_core02_over_capacity_passed`. Console-driven tests intentionally
avoid `test_log` and `debug_log`, so `game.log` is not the source of truth for
PASS/FAIL. `error.log` should not gain ModeU5 script errors.

Failure evidence includes:

```txt
Unknown effect modeu5_seed_opening_market_good_<good>
Unknown ordered iterator for the residue recipient
Failed to fetch modeu5_initialization_controller
ModeU5 deterministic CORE-02 proportional initialization allocation test failed
ModeU5 deterministic CORE-02 over-capacity initialization allocation test failed
```

If residue-related failures appear, start by inspecting TECH-01 `093`, the
generated per-good adapter, and the current fixed-point behavior described in
`NUMERIC_PRECISION_AND_TEST_DIAGNOSTICS.md`.

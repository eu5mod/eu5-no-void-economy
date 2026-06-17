# CORE-03 Stock Succession Runbook

This focused test validates the first gameplay use of the lifecycle hook
confirmed by TECH-01 `098`.

It is intentionally destructive. Use a disposable Castile baseline save.

## Purpose

Validate the full implemented chain:

```txt
US-02 creates storage capacity
CORE-01 enables stock movement
CORE-02 initializes stock state
CORE-03 moves stock after a real location owner change
```

The deterministic fixture seeds one controlled stock record, changes one
visible location owner, and verifies that:

```txt
country stock moves from loser to winner
market aggregate remains unchanged
the transfer quantity follows the capacity-share formula
the location-owner hook was observed
the result is visible in debug.log dumps
```

## Prerequisites

Use the following playset:

```txt
No Void Economy
No Void Economy Tests
```

Start a clean campaign as Castile and wait until CORE-02 initialization has
completed. CORE-02 starts after a delayed startup tick, so do not run this test
on campaign day 0.

The deterministic fixture requires:

```txt
CAS exists
POR exists
Huelva is owned by CAS
ModeU5 stock schema is current
ModeU5 initialization_state = 2
```

If any prerequisite is missing, the test must report `BLOCKED`, not `PASS`.

## Install

Close EU5, then run:

```bash
./tools/generate_stock_good_helpers.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Console Command

Run:

```txt
event modeu5_core03_debug.1
```

Choose:

```txt
Run CORE-03 Huelva stock-survival test
```

The test:

```txt
1. clears prior deterministic test markers
2. recalculates CAS/POR wheat capacity in Huelva's market
3. clears CAS/POR wheat stock in that market through CORE-01 operators
4. adds 100 wheat to CAS through modeu5_add_stock
5. records the expected capacity-share transfer
6. transfers Huelva to POR with change_location_owner
7. waits one day
8. reads CAS/POR/market wheat stock and emits the result dump
```

## Expected UI Result

Huelva visibly changes owner from Castile to Portugal.

The result event should show one of:

```txt
PASS - CORE-03 location stock succession
FAIL - CORE-03 location stock succession
BLOCKED - CORE-03 location stock succession prerequisites missing
```

## Required Log Evidence

Review `debug.log`, `error.log`, `game.log`, and `system.log`.

The validation comment for the PR must include the relevant dump lines:

```txt
ModeU5 CORE-03 DUMP before scenario=Huelva_to_Portugal ...
ModeU5 CORE-03 RESULT location_succession STAGED wait_one_day
ModeU5 CORE-03 DUMP after scenario=Huelva_to_Portugal ...
ModeU5 CORE-03 RESULT location_succession PASS
```

A passing dump must show:

```txt
expected_transfer = actual_transfer
cas_after = cas_before - expected_transfer
por_after = por_before + expected_transfer
market_delta = 0
```

The test also requires the lifecycle hook evidence from the same run:

```txt
ModeU5 CORE-03 OBSERVED on_location_changed_owner
ModeU5 CORE-03 PASS location hook resolved distinct loser and winner scopes
```

## Blocking / Failure Interpretation

`BLOCKED prerequisites` means the fixture was not valid. Common causes:

```txt
CORE-02 initialization was not complete yet
Huelva was already transferred in the current save
the campaign was not started from Castile's 1337 state
No Void Economy Tests was not loaded
```

`FAIL` means the fixture ran but stock succession did not reconcile. Start by
checking the before/after dumps, then inspect:

```txt
modeu5_core03_handle_location_changed_owner
modeu5_core03_prepare_location_good_transfer
modeu5_transfer_stock
modeu5_validate_dirty_stock_consistency
```

Known localization-disabled assertions are tolerated only when the expected
`ModeU5 CORE-03 DUMP` and `ModeU5 CORE-03 RESULT` lines are present.

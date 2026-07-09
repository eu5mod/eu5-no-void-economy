# PERF-01 Low-Risk Quick Wins Runbook

## Scope

This runbook validates the low-risk performance guards from GitHub issue #60:

```txt
skip zero-resource markets before opening-stock country scans
do not persist zero-valued stock/capacity/aggregate map entries
disable debug captures in normal runtime
reserve automatic full validation for audit mode
use explicit normal/debug/audit runtime flags
```

## Build And Install

Run from the repository root:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Scenario A - Normal Runtime Smoke

Setup:

```txt
Start a new campaign with ModeU5 debug set to Off.
Let the campaign pass the CORE-02 delayed initialization tick.
Let one monthly tick pass.
```

Expected:

```txt
modeu5_runtime_mode_normal is the active diagnostic mode.
Opening-stock initialization skips zero-source market x good pairs before the
country-capacity scan and still increments the zero-source counter.
Startup, normal monthly runtime, and verbose debug runtime do not call
automatic reconciliation. Monthly reconciliation runs only when audit mode is
active, and the four-year safety pass uses the active/dirty indexed path.
No new ModeU5 script-system error appears in error.log.
```

Logs to inspect:

```txt
error.log
game.log
system.log
```

## Scenario B - Audit/Test Regression

Setup:

```txt
Run a focused deterministic test event, for example:

event modeu5_debug.1
```

Expected:

```txt
The test fixture enters test-audit mode through modeu5_debug_clear_stock_test_results.
CORE stock debug captures and deterministic dump values remain visible.
Full validation remains available to explicit audit/test flows, but verbose
debug alone does not enable automatic audit reconciliation.
No generated stock adapter contains a dynamic map identifier.
```

Logs to inspect:

```txt
error.log
game.log
system.log
debug.log when the feature emits deterministic dumps
```

## Known Limitations

This PR does not add relationship caches, active-market lists, or a redesigned
monthly economy loop. It only removes avoidable zero-work and debug persistence
from existing paths.

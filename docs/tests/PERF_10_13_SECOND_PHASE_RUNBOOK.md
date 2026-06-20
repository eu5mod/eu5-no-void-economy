# PERF-10/13 Second-Phase Performance Runbook

## Purpose

Validate the remaining issue #89 second-phase guardrails:

```txt
PERF-10 - per-good loop audit
PERF-11 - active-list repair semantics
PERF-12 - market-scope value probe
PERF-13 - focused debug metrics
```

## Static Checks

Close EU5, then run:

```sh
./tools/generate_all.sh
./tools/audit_modeu5_per_good_loops.sh
./tools/validate_module_packages.sh
git diff --check
```

Expected:

```txt
ModeU5 per-good loop audit
Shared capacity per-good helpers: 0
Runtime traded_in_market dependencies: 0
```

## Install

```sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Enable:

```txt
No Void Economy
No Void Economy Tests
```

Use a disposable validation save.

## Scenario A - Broad Revalidation

Run:

```txt
event modeu5_revalidate_debug.1
```

Select:

```txt
Revalidate main operations
```

Wait for the final result event. Then close EU5 and run:

```sh
./tools/summarize_modeu5_test_logs.sh
```

Expected compact result:

```txt
Failed: 0
Blocked: 0
Missing expected scenarios: 0
ModeU5 TEST PASS scenario=perf10_13_active_repair_metrics
```

Relevant `debug.log` lines:

```txt
ModeU5 PERF-11 DUMP active_repair good=wheat ...
ModeU5 PERF-13 DUMP metrics_probe path=active_repair metrics_disabled_in_normal_runtime=yes
ModeU5 PERF-11 RESULT active_repair PASS
```

## Scenario B - PERF-12 Explicit Probe

Run:

```txt
event modeu5_perf12_debug.1
```

Select:

```txt
Run market-scope value probe
```

Expected if the candidate value link is valid:

```txt
ModeU5 PERF-12 DUMP market_values good=wheat produced_in_market=... stockpile_in_market=... traded_in_market=...
ModeU5 PERF-12 RESULT market_values PASS
```

If the test fails or `error.log` reports `traded_in_market:wheat` syntax/scope
errors, keep `traded_in_market:<good>` out of runtime code and update TECH-01
with the observed failure.

## Source Of Truth

Logs are the source of truth. Use the compact summary first, then inspect:

```txt
debug.log
error.log
game.log
system.log
```

Actual validation results belong in a PR comment, not in the PR body.

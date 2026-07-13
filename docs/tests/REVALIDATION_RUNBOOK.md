# Revalidation runbook

## Purpose

`event cbp_revalidate_debug.1` is the broad deterministic regression harness for the test-only package. It is intended for explicit manual/debug validation, not normal runtime.

## Execution contract

| Rule | Requirement |
|---|---|
| Entry point | Run manually from the console with `event cbp_revalidate_debug.1`. |
| Runtime cadence | Never call revalidation from monthly/yearly on-actions or runtime ticks. |
| Step cap | A single revalidation chain must never contain more than 10 scenario steps. |
| Summary event | The summary/finalize event is allowed after the 10 steps, but it must not run additional scenario work. |
| More coverage | If an 11th scenario is needed, create a second manual revalidation entry event/suite instead of extending the existing chain. |
| Tick isolation | Continuation events must use `days = 0` so the chain remains on the same in-game day and does not cross a monthly tick between scenario steps. |

## Why revalidation is isolated from monthly ticks

The suite intentionally mutates and validates controlled stock/capacity/debug state. Running it across a normal monthly tick can make the test results harder to interpret because monthly runtime systems may mutate stock, rebuild caches, or refresh audit state while the harness is mid-run.

For that reason, revalidation is treated as a manual diagnostic action. It should not be wired into automatic monthly validation, CMM monthly audit, or gameplay on-actions.

## Current scenario steps

| Step | Scenario |
|---:|---|
| 1 | US-02 storage capacity |
| 2 | CORE-01 single-record stock operators |
| 3 | CORE-01 same-market transfer |
| 4 | CORE-01 inter-market transfer |
| 5 | CORE-02 initialization |
| 6 | US-00 controlled pipeline |
| 7 | US-00 monthly runtime harness |
| 8 | US-10 demand resolution |
| 9 | US-10 issue #109 fast path / pruning |
| 10 | PERF-10/13 active repair metrics |

The result event only finalizes and displays pass/blocked/fail state.

## Extension guidance

When adding new coverage:

1. Keep the existing suite at 10 scenario steps or fewer.
2. Put any additional scenario into a new manual suite, for example `cbp_revalidate_debug.200`.
3. Do not schedule revalidation from monthly pulses.
4. Keep continuation delays at `days = 0` unless there is a documented test reason to observe a date transition; such tests should live outside the broad revalidation suite.
5. Update this runbook whenever the scenario list changes.

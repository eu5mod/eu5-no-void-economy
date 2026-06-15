# CORE-03 Lifecycle Hook Runbook

This controlled test verifies TECH-01 `098`. The probe records lifecycle hooks,
scope validity, duplicate location calls, and delayed finalizers. It never
calculates capacity or mutates stock.

## Install

Close EU5, then run:

```bash
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Confirm that `MODEU5_SOURCE.txt` identifies:

```txt
branch: spike/core-03-lifecycle-hooks
```

## Reset and report

Before each scenario, run:

```txt
event modeu5_core03_probe.1
```

Select `Reset lifecycle probe markers`, perform exactly one controlled
lifecycle action, let two days pass when a country finalizer is expected, then
run the event again and select `Open lifecycle probe report`.

## Scenario A - one permanent location transfer

Transfer one owned location to another existing country through a peace treaty.

Expected:

```txt
PASS - Location owner-change hook observed
PASS - Distinct loser and winner scopes resolved
PASS - No duplicate location hook observed
NOT OBSERVED - Country lifecycle hook
NOT OBSERVED - Delayed country finalizer
```

Temporary occupation without owner change must leave every location marker
absent.

## Scenario B - release or create a country

Release a country or create a subject through a path that permanently moves
locations.

Expected:

```txt
One location hook per transferred location
No duplicate-location marker
At least one country lifecycle hook
At least one delayed finalizer after the location hooks
```

Record whether `on_new_country_formed`, `on_released_country`, or both fired.
Multiple finalizers are evidence of overlapping hooks and must be resolved in
the CORE-03 design before gameplay implementation.

## Scenario C - annexation

Fully annex a controlled country, wait two days, and open the report.

Expected:

```txt
One location hook per transferred location
Distinct loser and winner scopes on every location hook
At least one annexation hook with a valid target
At least one delayed finalizer after location hooks
```

Record which of these markers exist:

```txt
modeu5_core03_probe_annexed_observed
modeu5_core03_probe_diplomatic_annexed_observed
modeu5_core03_probe_military_annexed_observed
modeu5_core03_probe_civil_war_annexed_observed
modeu5_core03_probe_multiple_finalizers_observed
```

## Log review

Review `error.log`, `game.log`, and `system.log` for unknown on-actions, unset
scopes, invalid delayed targets, or ModeU5 script errors.

Only after the required scenarios establish one non-duplicating location path
and an ordered finalizer contract may TECH-01 `098` become `CONFIRMED` and
CORE-03 stock succession begin.

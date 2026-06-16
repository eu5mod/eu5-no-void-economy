# CORE-03 Lifecycle Hook Runbook

This controlled test verifies TECH-01 `098`. The probe records lifecycle hooks,
scope validity, duplicate location calls, and delayed finalizers. It never
calculates capacity or mutates stock.

## Reproducible baseline

Use one clean baseline save as Spain and reload it before each scenario. The
probe can now auto-reset and arm each scenario, but it does not reset campaign
state for you.

Suggested baseline:

```txt
Start a clean campaign as Spain
Pause immediately
Create one baseline save
Reload that same baseline before Scenario A, B, and C
```

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

## Scenario hub

The probe hub is:

```txt
event modeu5_core03_probe.1
```

Use the scenario-preparation options instead of the bare reset when you want a
reproducible run. Each preparation option:

```txt
1. clears prior markers
2. arms the selected scenario
3. opens a short in-game briefing
```

The plain `Reset lifecycle probe markers` option remains available for ad hoc
testing.

## Report flow

For each controlled scenario:

```txt
Reload the baseline Spain save
event modeu5_core03_probe.1
```

Then:

```txt
1. choose the matching Prepare Spain scenario option
2. perform exactly one controlled lifecycle action
3. wait two days only when a country finalizer is expected
4. reopen `event modeu5_core03_probe.1`
5. select `Open lifecycle probe report`
```

The report now starts with the currently prepared scenario row so the result is
easier to interpret after several runs.

## Scenario A - one permanent location transfer

Using Spain, transfer one permanently owned location to another existing
country through one controlled path such as a peace treaty or another permanent
ownership change. Do not chain multiple transfers in the same run.

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

Using Spain, release one country or create one new country through a path that
permanently moves locations. Wait two days before opening the report.

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

Using Spain, fully annex one controlled country, wait two days, and open the
report.

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

## Recommended record sheet

Capture each run with one row:

| Scenario | Baseline save reloaded | Action path used | Locations transferred | Waited two days | Report result | Log result |
|---|---|---|---|---|---|---|
| A | yes/no | peace / sale / other | fill manually | no | fill manually | fill manually |
| B | yes/no | release / subject / formation | fill manually | yes | fill manually | fill manually |
| C | yes/no | annexation path | fill manually | yes | fill manually | fill manually |

## Log review

Review `error.log`, `game.log`, and `system.log` for unknown on-actions, unset
scopes, invalid delayed targets, or ModeU5 script errors.

Only after the required scenarios establish one non-duplicating location path
and an ordered finalizer contract may TECH-01 `098` become `CONFIRMED` and
CORE-03 stock succession begin.

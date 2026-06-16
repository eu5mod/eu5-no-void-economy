# CORE-03 Lifecycle Hook Runbook

This controlled test verifies TECH-01 `098`. The probe records lifecycle hooks,
scope validity, duplicate location calls, and delayed finalizers. It never
calculates capacity or mutates stock.

The probe now supports two workflows:

```txt
1. synthetic regression for fast probe wiring checks
2. manual vanilla observation for actual TECH-01 coverage evidence
```

## Reproducible baseline

Use one clean baseline save as Spain and reload it before each manual scenario.
The synthetic runner does not need a special save beyond having both SPA and
POR alive.

Suggested manual baseline:

```txt
Start a clean campaign as Spain
Pause immediately
Create one baseline save
Reload that same baseline before manual Scenario A, B, and C
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

## Probe hub

The probe hub is:

```txt
event modeu5_core03_probe.1
```

## Fast synthetic regression

Use the `Run synthetic ...` options when you want a fast automated harness.
Each synthetic run:

```txt
1. resets markers
2. arms one scenario
3. emulates the expected scopes with a fixed SPA/POR fixture
4. opens the report immediately
```

Synthetic coverage:

```txt
Scenario A: Spain capital owner-change to Portugal
Scenario B: one location transfer plus on_new_country_formed and on_released_country
Scenario C: Portugal capital owner-change plus on_annexed and a valid target scope
```

Important boundary:

```txt
Synthetic runs do not change the map
Synthetic runs do not prove vanilla sequencing
Synthetic runs validate probe wiring only
```

## Manual vanilla observation

Use the `Prepare manual ...` options when you want reproducible vanilla
observation. Each manual preparation option:

```txt
1. clears prior markers
2. arms the selected scenario
3. opens a short in-game briefing
```

The plain `Reset lifecycle probe markers` option remains available for ad hoc
testing.

## Manual report flow

For each manual scenario:

```txt
Reload the baseline Spain save
event modeu5_core03_probe.1
```

Then:

```txt
1. choose the matching manual scenario option
2. perform exactly one controlled lifecycle action
3. wait two days only when a country finalizer is expected
4. reopen `event modeu5_core03_probe.1`
5. select `Open lifecycle probe report`
```

The report starts with run mode and scenario rows so the result is easier to
interpret after several runs.

## Manual Scenario A - one permanent location transfer

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

## Manual Scenario B - release or create a country

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

## Manual Scenario C - annexation

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

| Run type | Scenario | Baseline save reloaded | Action path used | Locations transferred | Waited two days | Report result | Log result |
|---|---|---|---|---|---|---|---|
| synthetic | A/B/C | no | built-in SPA/POR emulation | scripted | no | fill manually | optional |
| manual | A | yes/no | peace / sale / other | fill manually | no | fill manually | fill manually |
| manual | B | yes/no | release / subject / formation | fill manually | yes | fill manually | fill manually |
| manual | C | yes/no | annexation path | fill manually | yes | fill manually | fill manually |

## Log review

Review `error.log`, `game.log`, and `system.log` for unknown on-actions, unset
scopes, invalid delayed targets, or ModeU5 script errors.

Only the required manual vanilla scenarios can establish the non-duplicating
location path and ordered finalizer contract needed for TECH-01 `098` to
become `CONFIRMED` and for CORE-03 stock succession to begin.

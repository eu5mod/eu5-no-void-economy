# CORE-03 Lifecycle Hook Runbook

This controlled test verifies TECH-01 `098`. The probe records lifecycle hooks,
scope validity, duplicate location calls, and delayed finalizers. It never
calculates capacity or mutates stock.

The probe now supports two workflows:

```txt
1. scripted deterministic fixtures for visible, reproducible runs
2. manual vanilla observation for actual TECH-01 coverage evidence
```

## Reproducible baseline

Use one clean baseline save as Castile and reload it before each scripted or
manual scenario.

Suggested baseline:

```txt
Start a clean campaign as Castile
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

## Scripted deterministic fixtures

Use the `Run scripted ...` options when you want a reproducible harness that
also changes the visible map state. Each scripted run:

```txt
1. resets markers
2. arms one scenario
3. uses one fixed fixture
4. schedules the report after the relevant delayed-hook window
```

Scripted fixture coverage:

```txt
Scenario A: transfer Huelva from Castile to Portugal
Scenario B: create one Castile subject centered on Leon
Scenario C: create or reuse one Leon-centered Castile subject, then auto-annex it
```

Important boundary:

```txt
Scripted runs are intended to be visible in the UI
Scenario B confirms new-country creation, not release-specific hooks
Release-specific coverage, rebel paths, and tag-formation paths still need manual confirmation
```

New observability aid:

```txt
Scripted runs now emit explicit ModeU5 CORE-03 started/staged/completed/aborted lines in error.log
Observed hooks also emit PASS / FAIL-style lines in error.log
The report shows probe-state rows for reset, manual preparation, and scripted execution
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
Reload the baseline Castile save
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

Ignore unrelated localization noise when reviewing this probe. The validation
target here is whether the deterministic fixture ran, changed the map as
expected, and produced the expected lifecycle markers.

## Scripted Scenario A - Huelva to Portugal

```txt
Reload the baseline Castile save
event modeu5_core03_probe.1
Choose: Run scripted Scenario A - transfer Huelva to Portugal
Unpause until the report opens
```

Expected:

```txt
Huelva visibly changes owner to Portugal
PASS - Location owner-change hook observed
PASS - Distinct loser and winner scopes resolved
PASS - No duplicate location hook observed
NOT OBSERVED - Country lifecycle hook
NOT OBSERVED - Delayed country finalizer
```

## Scripted Scenario B - create Leon vassal

```txt
Reload the baseline Castile save
event modeu5_core03_probe.1
Choose: Run scripted Scenario B - create the Leon vassal
Unpause until the report opens
```

Expected:

```txt
A Castile subject centered on Leon becomes visible on the map
PASS - Location owner-change hook observed
OBSERVED - on_new_country_formed
OBSERVED - Country lifecycle hook
OBSERVED - Delayed country finalizer
PASS - Delayed finalizer observed after a location hook
NOT OBSERVED is acceptable for on_released_country in this scripted creation fixture
```

## Scripted Scenario C - auto-annex Leon

```txt
Reload the baseline Castile save
event modeu5_core03_probe.1
Choose: Run scripted Scenario C - auto-annex Leon
Unpause until the report opens
```

Expected:

```txt
Leon may appear briefly as a visible Castile subject during staging
Leon is then auto-annexed and returns to Castile without any extra click
OBSERVED - One annexation-family hook
PASS - Annexation target scope resolved
OBSERVED - Delayed country finalizer
PASS - Delayed finalizer observed after a location hook
```

Important implementation note:

```txt
This scripted annexation does not rely on vanilla subject-age, opinion, or diplomatic-annexation UI requirements.
It uses a direct scripted annexation path so the fixture stays deterministic.
```

## Manual Scenario A - one permanent location transfer

Using Castile, transfer one permanently owned location to another existing
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

Using Castile, release one country or create one new country through a path that
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

Using Castile, fully annex one controlled country, wait two days, and open the
report.

Recommended visible/manual path when you want a fast UI confirmation:

```txt
Use Castile and annex Leon through a quick military path when your test save provides a valid casus belli.
This is a comfort/manual-observation path, not the deterministic automated fixture.
```

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
| scripted | A | yes | Huelva to Portugal fixture | Huelva | no | fill manually | fill manually |
| scripted | B | yes | Leon subject-creation fixture | Leon | yes | fill manually | fill manually |
| scripted | C | yes | Leon stage then annex fixture | Leon | yes | fill manually | fill manually |
| manual | A | yes/no | peace / sale / other | fill manually | no | fill manually | fill manually |
| manual | B | yes/no | release / subject / formation | fill manually | yes | fill manually | fill manually |
| manual | C | yes/no | annexation path | fill manually | yes | fill manually | fill manually |

## Log review

Review `error.log`, `game.log`, and `system.log` for unknown on-actions, unset
scopes, invalid delayed targets, or ModeU5 script errors.

For scripted deterministic fixtures, grep for:

```txt
ModeU5 CORE-03 scripted Scenario A started/completed
ModeU5 CORE-03 scripted Scenario B started/completed
ModeU5 CORE-03 scripted Scenario C started/staging complete/completed
ModeU5 CORE-03 OBSERVED on_location_changed_owner
ModeU5 CORE-03 OBSERVED on_new_country_formed
ModeU5 CORE-03 OBSERVED on_annexed
ModeU5 CORE-03 OBSERVED on_diplomatic_annexed
ModeU5 CORE-03 OBSERVED delayed country finalizer
ModeU5 CORE-03 manual Scenario A/B/C prepared
```

Only the required manual vanilla scenarios can establish the non-duplicating
location path and ordered finalizer contract needed for TECH-01 `098` to
become `CONFIRMED` and for CORE-03 stock succession to begin.

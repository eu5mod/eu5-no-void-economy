# PERF-15 - Narrow US-00 Monthly Good Dispatch Safely

## User Story

As a ModeU5 maintainer, I want the monthly US-00 pipeline to avoid expensive
record work for goods that have neither current market production nor previous
ModeU5 state, so that the normal monthly tick spends less time on empty
country-market-good combinations without losing cleanup or penalty behavior.

## Context

The generator still emits one static helper per good because EU5 script helper
names and map names are literal identifiers. The safe optimization target is
therefore not removing generated helpers entirely. The safe target is narrowing
what each helper does after it is dispatched.

Before PERF-15, `modeu5_process_us00_monthly_market_good_<good>` loaded the full
US-00 record before it knew whether the good had current production or previous
ModeU5 state. For zero-production goods with no prior record, this meant several
map checks and value reads that could not change gameplay.

## Selected Design

For each generated good:

- read `produced_in_market:<good>` first as the current-production gate;
- if production is positive, load the full US-00 record and process normally;
- if production is zero, probe a lightweight country-scoped active-record marker;
- if the marker is absent, fall back to map-key presence checks for legacy or
  repaired records;
- only load the full US-00 record when current production exists or previous
  ModeU5 state is detected;
- split `modeu5_clear_loaded_void_economy_record_good_<good>` from the public
  clear wrapper so the monthly path does not load the same record twice.

The active marker is stored as:

```txt
modeu5_<good>_us00_active_record_by_market[market] = 1
```

It is a country-scoped helper index for US-00 monthly dispatch. It is not a
stock source, not a market aggregate, and not an active-list replacement.

## Safety Rules

- A good with `produced_in_market:<good> > 0` is always processed.
- A good with previous produced / added / rejected / ratio / void / penalty state
  is always processed, even if current production is zero.
- Previous-month production penalties still apply.
- Previous non-zero US-00 records still clear.
- Zero-value maps remain pruned and missing keys still mean zero.
- `traded_in_market:<good>` remains out of runtime gameplay paths.

## Acceptance Criteria

- [ ] Generated adapters include
      `modeu5_probe_us00_previous_record_activity_good_<good>`.
- [ ] Generated adapters include
      `modeu5_clear_loaded_void_economy_record_good_<good>`.
- [ ] `modeu5_process_us00_monthly_market_good_<good>` reads
      `produced_in_market:<good>` before full US-00 record loading.
- [ ] The monthly path does not call the public clear wrapper after it already
      loaded the record; it calls the loaded-clear helper.
- [ ] Main revalidation still passes.
- [ ] US-00 controlled pipeline and monthly runtime dumps still pass.

## Manual Test Scenario

Static checks:

```sh
./tools/generate_all.sh
./tools/audit_modeu5_per_good_loops.sh
./tools/validate_module_packages.sh
git diff --check
./tools/install_local_packages.sh --check
```

Runtime smoke:

```txt
event modeu5_revalidate_debug.1
Select "Revalidate main operations"
```

After closing EU5:

```sh
./tools/summarize_modeu5_test_logs.sh
```

Expected summary:

```txt
Failed: 0
Blocked: 0
Missing expected scenarios: 0
```

Important dump lines:

```txt
ModeU5 TEST PASS scenario=us00_controlled_pipeline
ModeU5 TEST PASS scenario=us00_monthly_runtime
ModeU5 TEST PASS scenario=main_revalidation_summary
```

## Known Limitations

- The generated all-good dispatcher still exists because static generated
  helpers remain the confirmed safe way to access per-good map names.
- This PR reduces full US-00 record loading and duplicate clear-time loading; it
  does not create a dynamic market-good work queue.
- Runtime profiling still needs commit-specific logs before claiming a measured
  monthly tick improvement.

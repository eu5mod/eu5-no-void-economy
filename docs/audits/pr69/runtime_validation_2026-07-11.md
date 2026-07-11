# PR #69 runtime validation — 2026-07-11

## Tested provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
commit: 56b102dd843314f2f50eb12f4f7e15e19e6c2d5d
runtime mode: debug
source_dirty: yes
```

## Static and installation result

The following completed successfully:

```txt
./tools/generate_all.sh
python3 tools/validate_ci_static_contracts.py
./tools/validate_module_packages.sh
./tools/normalize_cmm_value_links.sh --check
./tools/audit_modeu5_persistent_state.sh
./tools/validate_generators.sh
./tools/validate_modeu5_script_safety.sh
python3 tools/validate_cmm_configuration.py
git diff --check
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
```

## Load-level result

The three previous US-04 generated-script failures were not observed in this rerun:

```txt
Duplicated key modeu5_reset_pop_demand_annual_counters_good_<good>
Cannot read [modeu5_pop_demand_base_consumption_multiplier] as a script value
Failed to read 'min' for add_to_variable_map
```

This is evidence that the generated helper collision, named script-value read and variable-map write fixes loaded successfully.

## Focused runtime result

The focused scenario was launched and reached its first marker, but it did not complete:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_adaptation
```

EU5 raised:

```txt
Tried to localize with localization disabled
```

No US-04 dump, PASS or FAIL marker followed. Therefore the business assertions were not evaluated to completion.

## Root cause

The visible console event called the logging test effect directly from its option. The first `debug_log` therefore executed inside the console command's localization-disabled context.

The passing US-17 focused probe already uses the correct pattern:

```txt
visible console event
  -> hidden days=0 continuation
  -> logging test effect in hidden event immediate
```

## Fix

Commit:

```txt
0c7cf94a6d5c434267a6dd62204e0424b41d87b7
```

changes `modeu5_us04_debug.1` so the visible option schedules hidden event `modeu5_us04_debug.10`, which then runs the US-04 test effect outside the localization-disabled context.

## Status

```txt
Static validation:                         PASS
Installation provenance:                  CONFIRMED, source_dirty=yes
Previous generated-parser blockers:       ABSENT IN THIS RERUN
Focused test launcher:                    ENTERED
Focused test business assertions:         NOT COMPLETED
Focused runtime acceptance:               PENDING RERUN
Live vanilla Pop-demand integration:      NOT_CONFIRMED
```

## Required rerun

```sh
git pull
./tools/generate_all.sh
python3 tools/validate_ci_static_contracts.py
./tools/validate_module_packages.sh
./tools/validate_generators.sh
./tools/validate_modeu5_script_safety.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Then in EU5:

```txt
event modeu5_us04_debug.1
```

Expected markers:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_adaptation
ModeU5 US-04 DUMP ...
ModeU5 US-04 RESULT pop_demand_adaptation PASS
ModeU5 TEST PASS scenario=us04_pop_demand_adaptation
```

Inspect with:

```sh
grep -E "us04_pop_demand_adaptation|ModeU5 US-04|Tried to localize with localization disabled|modeu5_pop_demand_base_consumption_multiplier|Failed to read 'min'|Duplicated key modeu5_.*pop_demand" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/error.log" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/debug.log" || true
```

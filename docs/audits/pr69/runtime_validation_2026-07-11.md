# PR #69 runtime validation — 2026-07-11

## First tested provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
commit: 56b102dd843314f2f50eb12f4f7e15e19e6c2d5d
runtime mode: debug
source_dirty: yes
```

## First static and installation result

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

## First load-level result

The three previous US-04 generated-script failures were not observed in this rerun:

```txt
Duplicated key modeu5_reset_pop_demand_annual_counters_good_<good>
Cannot read [modeu5_pop_demand_base_consumption_multiplier] as a script value
Failed to read 'min' for add_to_variable_map
```

This is evidence that the generated helper collision, named script-value read and variable-map write fixes loaded successfully.

## First focused runtime result

The focused scenario was launched and reached its first marker, but it did not complete:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_adaptation
```

EU5 raised:

```txt
Tried to localize with localization disabled
```

No US-04 dump, PASS or FAIL marker followed. Therefore the business assertions were not evaluated to completion.

## First-run root cause

The visible console event called the logging test effect directly from its option. The first `debug_log` therefore executed inside the console command's localization-disabled context.

The passing US-17 focused probe already uses the correct pattern:

```txt
visible console event
  -> hidden days=0 continuation
  -> logging test effect in hidden event immediate
```

## Launcher fix

Commit:

```txt
0c7cf94a6d5c434267a6dd62204e0424b41d87b7
```

changes `modeu5_us04_debug.1` so the visible option schedules hidden event `modeu5_us04_debug.10`, which then runs the US-04 test effect outside the localization-disabled context.

## Clean pre-runtime rerun after launcher fix

The installation and static suite were rerun from:

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
commit: 87a1e29c1751adbc5955c3ac3be30267ee93f123
runtime mode: debug
source_dirty: no
installed_at_utc: 2026-07-11T10:18:34Z to 2026-07-11T10:18:36Z
```

All requested pre-runtime checks passed:

```txt
ModeU5 CI static contract validation passed
ModeU5 module package validation passed
ModeU5 CMM value-link validation passed
ModeU5 persistent state audit passed with:
  unclassified persistent maps/lists = 0
  direct stock-map write candidates outside adapter = 0
  ownership/rebuild/reset policy gaps = 0
ModeU5 generator and validator convention checks passed
ModeU5 script-safety validation passed
ModeU5 CMM configuration validation passed
git diff --check passed
install_local_packages.sh passed
install_local_packages.sh --check passed
```

All five installed packages reported the exact same clean provenance:

```txt
source_branch=22-us-04-annual-local-pop-demand-adjustment
source_commit=87a1e29c1751adbc5955c3ac3be30267ee93f123
source_dirty=no
```

This removes the provenance weakness from the first run. It proves that the launcher fix and current PR #69 source package cleanly and pass all available static/install-time contracts.

It does not yet prove the US-04 multiplier business assertions, because no post-`event modeu5_us04_debug.1` debug/error log was included with this clean rerun.

### Separate generator observation

Within the same command sequence, generation reported:

```txt
first explicit generate_all.sh:            25 building override files
install-triggered subsequent generation:   26 building override files
```

This indicates a potentially non-idempotent or order-dependent US-09 building-override generation surface. It is not a direct PR #69/US-04 failure, but it should be investigated separately because two consecutive generation passes should normally produce the same artifact count from unchanged tracked source.

## Current status

```txt
Static validation at 87a1e29:              PASS
Installation provenance:                   CONFIRMED, source_dirty=no
Package consistency check:                 PASS
Previous US-04 generated-parser blockers:  ABSENT IN PRIOR LOAD RERUN
Focused launcher fix:                      COMMITTED AND CLEANLY INSTALLED
Focused test business assertions:          PENDING POST-EVENT LOG
Focused runtime acceptance:                PENDING
Live vanilla Pop-demand integration:       NOT_CONFIRMED
Separate US-09 generator idempotence:       REVIEW RECOMMENDED
```

## Required focused runtime step

In EU5:

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
./tools/summarize_modeu5_test_logs.sh

grep -E "us04_pop_demand_adaptation|ModeU5 US-04|Tried to localize with localization disabled|modeu5_pop_demand_base_consumption_multiplier|Failed to read 'min'|Duplicated key modeu5_.*pop_demand" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/error.log" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/debug.log" || true
```

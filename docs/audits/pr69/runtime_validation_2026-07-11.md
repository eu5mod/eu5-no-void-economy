# PR #69 runtime validation — 2026-07-11

## Accepted tested provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
commit: 87a1e29c1751adbc5955c3ac3be30267ee93f123
runtime mode: debug
source_dirty: no
installed_at_utc: 2026-07-11T10:18:34Z to 2026-07-11T10:18:36Z
```

All five installed packages reported the same branch, commit and clean source state.

## Static and installation result

The complete requested pre-runtime sequence passed:

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

Observed results included:

```txt
ModeU5 CI static contract validation passed
ModeU5 module package validation passed
ModeU5 CMM value-link validation passed
Unclassified persistent maps/lists: 0
Direct stock-map write candidates outside generated adapter template: 0
Ownership/rebuild/reset policy gaps: 0
ModeU5 generator and validator convention checks passed
ModeU5 script-safety validation passed
source_dirty=no for all installed packages
```

## Load-level result

The previous direct US-04 parser/load failures were absent:

```txt
Duplicated key modeu5_reset_pop_demand_annual_counters_good_<good>
Cannot read [modeu5_pop_demand_base_consumption_multiplier] as a script value
Failed to read 'min' for add_to_variable_map
Failed to find a valid event target link for the US-04 value block
```

This validates the generated-helper symbol rename, quoted named script-value read and scalar variable-map write pattern.

## Focused US-04 runtime result

The focused event completed successfully at `12:22:27`:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_adaptation
ModeU5 US-04 DUMP base_multiplier=1.2000 wheat_multiplier=1.2120 beer_multiplier=1.1880 cloth_multiplier=1.2000 tools_multiplier=1.2000 wheat_sat=0 wheat_unsat=0 beer_sat=0 beer_unsat=0 cloth_sat=0 cloth_unsat=0 tools_sat=0 tools_unsat=0
ModeU5 US-04 RESULT pop_demand_adaptation PASS
ModeU5 TEST PASS scenario=us04_pop_demand_adaptation
```

The deterministic fixture therefore proves:

```txt
baseline multiplier:                 1.2000
12 satisfied months:                1.2000 × 1.01 = 1.2120
12 unsatisfied months:              1.2000 × 0.99 = 1.1880
mixed year:                         unchanged at 1.2000
zero-observation year:              unchanged at 1.2000
annual counters after adaptation:   reset to 0
```

## Full-revalidation inclusion result

The full chain ran the US-04 scenario again at `12:22:35` and produced the same dump and PASS markers:

```txt
ModeU5 TEST ENTERED scenario=us04_pop_demand_adaptation
ModeU5 US-04 RESULT pop_demand_adaptation PASS
ModeU5 TEST PASS scenario=us04_pop_demand_adaptation
```

This proves the US-04 scenario is correctly integrated into the main revalidation sequence, not only into its focused launcher.

## Full-chain tail caveat

The overall summarizer reported:

```txt
Entered: 16
Passed: 14
Failed: 0
Blocked: 0
Pending: 0
Missing expected full-revalidation scenarios: 1
missing: main_revalidation_summary
```

The scenario trace reaches:

```txt
ModeU5 TEST ENTERED scenario=us17_us20_route_reconciliation
```

but contains no terminal US-17/US-20 PASS/FAIL/BLOCKED marker and no `main_revalidation_summary` marker afterward.

Therefore:

```txt
PR #69 / US-04 runtime acceptance: PASS
entire repository full-revalidation closure: NOT COMPLETE
unresolved tail begins at: us17_us20_route_reconciliation
```

The missing final summary is not evidence of a US-04 failure. The US-04 scenario already produced both focused and full-chain PASS markers before the chain reached the US-17/US-20 tail.

A separate US-17/US-20 log investigation should inspect:

```sh
grep -E "us17_us20_route_reconciliation|US17/US20|ASSERT FAIL|Tried to localize with localization disabled|main_revalidation_summary" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/error.log" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/debug.log" || true
```

## Scope of what is proven

This runtime validation proves:

```txt
location × good multiplier persistence
annual satisfied/unsatisfied branch arithmetic
mixed/no-observation no-change behavior
annual counter reset ordering
CMM disabled/enabled fixture behavior
focused-event launcher behavior
main-revalidation inclusion
```

It does not prove:

```txt
vanilla live Pop requested consumption reads modeu5_pop_demand_multiplier[good]
Pops actually consume 20% more goods at baseline
monthly live Pop outcome counters are produced from a confirmed vanilla Pop-demand endpoint
```

TECH-01 #039 therefore remains `NOT_CONFIRMED` for direct application to vanilla local Pop demand.

## Separate generator observation

The command sequence reported different US-09 building override counts in successive generation paths:

```txt
first explicit generate_all.sh:            25 building override files
install-triggered subsequent generation:   26 building override files
```

This is not a PR #69/US-04 acceptance failure, but it remains a separate idempotence/order-dependency observation for US-09 generation.

## Final PR #69 status

```txt
Static validation:                          PASS
Installation provenance:                   PASS — clean commit 87a1e29
US-04 generated parser/load surface:        PASS
US-04 focused deterministic fixture:        PASS
US-04 main-revalidation scenario:           PASS
US-04 annual arithmetic and counter reset:  PASS
PR #69 runtime acceptance:                 PASS
Live vanilla Pop-demand application:        NOT_CONFIRMED
Repository-wide final summary:              INCOMPLETE — unrelated US-17/US-20 tail
```

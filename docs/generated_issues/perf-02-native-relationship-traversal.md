# PERF-02 - Prefer Native Relationship Traversal

Labels: technical-foundation, performance

Related issue: https://github.com/eu5mod/eu5-no-void-economy/issues/60

## User Story

As a ModeU5 maintainer, I want country-driven stock and capacity flows to use
native country-to-market traversal so that recurring country work does not pay
for repeated global market scans.

## Functional objective

Implement the second performance optimization layer:

```txt
audit country-driven flows
prefer country -> every_market_present_in_country -> goods
build human-relevant market lists from native country-market traversal
add a probe for iterator semantics and owned-location market coverage
```

This PR deliberately does not implement the inverse `market -> countries`
cache. That belongs to the next performance layer.

## Required scopes / values / effects

| Need | Scope | Method | Status | TECH-01 |
|---|---|---|---|---|
| Country-to-market traversal | country → market | `every_market_present_in_country` | CONFIRMED | 117 |
| Human country detection | country | `is_ai = no` | CONFIRMED | 120 |
| Deduplicated relevant market list | global → market list | `add_to_global_variable_list`, `is_target_in_global_variable_list`, `clear_global_variable_list` | CONFIRMED | 111, 121 |
| Per-market capacity recomputation for all goods | country × market → goods | generated wrapper over literal per-good adapters | CONFIRMED | 104 |

## Files expected to change

```txt
tools/generate_stock_good_helpers.sh
tools/templates/modeu5_stock_good_adapter.template.txt
in_game/common/scripted_effects/modeu5_performance_effects.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_perf02_test_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_perf02_debug_events.txt
main_menu/localization/english/modeu5_stock_l_english.yml
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/TEST_PLAN.md
docs/tests/PERF_02_NATIVE_RELATIONSHIP_TRAVERSAL_RUNBOOK.md
```

## Dependencies

- Stacked on PERF-01 while PR #62 is open.
- Uses the CORE-01 literal per-good adapter model.
- Uses US-02 country-market capacity helpers.
- Uses TECH-01 111 variable-list semantics.

## Implementation rules

- Do not change stock arithmetic or stock mutation semantics.
- Do not build the inverse `countries_present_in_market` cache in this PR.
- Keep market-driven full validation and aggregate rebuilds on their existing
  path until PR3 provides the inverse cache.
- Preserve single-good adapters for good-specific callers.
- Use `country -> every_market_present_in_country -> all goods` for shared
  country capacity refresh.
- Keep human-relevant market lists as scheduling/debug data only; they are not
  stock sources.

## Acceptance criteria

- The shared country storage-capacity wrapper iterates native country markets
  once and processes goods inside each market.
- The previous per-good country-market wrapper remains available.
- `modeu5_rebuild_human_relevant_markets` builds a deduplicated global market
  list from human countries using `every_market_present_in_country`.
- A focused PERF-02 debug event validates that owned-location markets for the
  current country are present in the native iterator output.
- TECH-01 documents `is_ai = no`, the iterator sources, and edge-case probe.
- Generated adapters are regenerated and validation passes.

## Manual test scenario

Run:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Then in a disposable campaign as a country with markets, run:

```txt
event modeu5_perf02_debug.1
```

## Known limitations

The probe confirms owned-location market coverage for the current country. It
does not yet prove every edge case for market access, foreign buildings,
market splits, or market reassignment. Those remain documented validation
targets before later performance layers rely on sparse market lists for
gameplay-critical processing.

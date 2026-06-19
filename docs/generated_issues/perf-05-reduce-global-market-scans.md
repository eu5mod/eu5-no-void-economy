# PERF-05 - Reduce Global Market Scans

Labels: technical-foundation, module:core, enhancement

Related issue: https://github.com/eu5mod/eu5-no-void-economy/issues/60

Implements Issue #60 PR 4:

```txt
PR 4 - Reduce Global Market Scans
```

## User Story

As a ModeU5 maintainer, I want validation and repair flows to iterate known
active markets instead of scanning every market for every good so that debug,
audit, and maintenance workloads scale with ModeU5 state rather than with the
full world market list.

## Functional objective

Add sparse active-market scheduling indexes:

```txt
modeu5_<good>_active_markets
modeu5_active_markets_any_good
```

Then use those indexes for active validation:

```txt
active market -> per-good active-list membership -> validate good
```

This complements PERF-04's monthly US-00 loop fusion and keeps the strict
exhaustive audit path available.

## Required scopes / values / effects

| Need | Scope | Method | Status | TECH-01 |
|---|---|---|---|---|
| Deduplicated global market list | global -> market | `add_to_global_variable_list`, `is_target_in_global_variable_list`, `every_in_global_list`, `clear_global_variable_list` | CONFIRMED | 111, 129 |
| Per-good active market list | global -> market | one literal generated list per good | CONFIRMED | 129 |
| Active validation traversal | global active market -> per-good active membership | generated `modeu5_validate_active_market_all_goods` | TO_TEST | 129 |
| Strict exhaustive audit | none -> market | `every_market_in_world` | CONFIRMED | 002 |

## Files expected to change

```txt
tools/generate_stock_good_helpers.sh
tools/templates/modeu5_stock_good_adapter.template.txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_stock_test_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_debug_events.txt
main_menu/localization/english/modeu5_stock_l_english.yml
docs/generated_issues/perf-05-reduce-global-market-scans.md
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/PERF_05_REDUCE_GLOBAL_MARKET_SCANS_RUNBOOK.md
docs/tests/TEST_PLAN.md
```

## Dependencies

- Stacked on PERF-04 monthly US-00 loop fusion.
- Uses TECH-01 111 global variable-list semantics.
- Uses PERF-03 market-country work cache during each validation scan.
- Uses CORE-01.5/CORE-01.6 validation and rebuild arithmetic.

## Implementation rules

- Do not mutate stock outside centralized stock effects.
- Do not remove the strict exhaustive validation function.
- Do not assume `remove_from_global_variable_list` exists.
- Treat active lists as scheduling indexes, not stock sources.
- Active lists may be overinclusive; validation must still read the real maps.
- Dirty reconciliation remains the normal frequent runtime path.
- Active validation is for audit/maintenance contexts that should avoid
  `good -> every_market_in_world` scans.
- Reuse the validation scan result when rebuilding after a detected mismatch.

## Acceptance criteria

- Generated adapters maintain one active-market list per good.
- Generated adapters maintain one global `modeu5_active_markets_any_good` list.
- Stock, transfer, capacity, and rebuild paths mark markets active when they
  leave positive stock/capacity/aggregate state.
- Active validation iterates `modeu5_active_markets_any_good` once, then checks
  each per-good active list inside the market scope.
- `modeu5_validate_all_stock_consistency` remains strict/exhaustive and still
  uses `every_market_in_world`.
- Automatic allowed validation uses dirty validation in normal runtime and
  active validation in audit mode.
- Validation-triggered rebuild reuses the current scan result and no longer
  rescans country sources before writing the corrected market aggregate.
- Deterministic reconciliation tests expose a PASS/FAIL marker for active
  validation.

## Manual test scenario

Run:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Then in a disposable campaign:

```txt
event modeu5_debug.1
choose "Test US-11 dirty-record reconciliation"
```

Expected visible results:

```txt
PASS - Dirty market-good reconciliation
PASS - Active market-good reconciliation
PASS - Empty reconciliation is a no-op
```

Review logs for absence of ModeU5 script-system errors.

## Known limitations

Active lists are additive scheduling indexes. Because no list-item removal
effect is currently confirmed, a market can remain in an active list after the
last stock/capacity entry returns to zero. This is safe but overinclusive:
validation still reads real stock/capacity maps and a strict exhaustive audit
remains available for manual repair.

Initialization still uses `every_market_in_world` where it must discover
vanilla `stockpile_in_market(goods:<good>)`; active lists do not exist before
that discovery.

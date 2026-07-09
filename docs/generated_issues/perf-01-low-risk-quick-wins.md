# PERF-01 - Low-Risk Runtime Quick Wins

Labels: performance, technical-foundation

Related issue: https://github.com/eu5mod/eu5-no-void-economy/issues/60

## User Story

As a ModeU5 maintainer, I want the stock runtime to avoid obviously unnecessary
work so that normal campaigns stay responsive while audit/debug tests remain
fully inspectable.

## Functional objective

Implement the first low-risk optimization layer without changing stock business
rules:

```txt
skip zero-resource market x good pairs before opening-stock country scans
avoid persisting zero-valued map entries
disable persistent debug captures in normal runtime
keep full all-market validation out of frequent/automatic ticks
make normal/debug/audit modes explicit
```

## Required scopes / values / effects

| Need | Scope | Method | Status | TECH-01 |
|---|---|---|---|---|
| Persistent mode flags | global | `set_global_variable` / `has_global_variable` | CONFIRMED | 007 |
| Debug gate | global trigger | `modeu5_debug_capture_enabled_trigger` | CONFIRMED | N/A |
| Audit-only full validation | global trigger | `modeu5_full_validation_allowed_trigger` | CONFIRMED | N/A |
| Missing map entry means zero | country/global map readers | existing safe-default reads | CONFIRMED | 007 |
| Opening stock source | market | `stockpile_in_market(goods:<good>)` | CONFIRMED | existing CORE-02 exposure |

## Files expected to change

```txt
in_game/common/scripted_effects/modeu5_configuration_effects.txt
in_game/common/scripted_triggers/modeu5_configuration_triggers.txt
in_game/common/scripted_effects/modeu5_debug_effects.txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
tools/templates/modeu5_stock_good_adapter.template.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_stock_test_effects.txt
docs/technical/DEBUG_CONVENTIONS.md
docs/tests/TEST_PLAN.md
docs/tests/PERF_01_LOW_RISK_QUICK_WINS_RUNBOOK.md
```

## Dependencies

Depends on CORE-01 map adapters, CORE-02 initialization, US-02 capacity maps,
and the current debug/test package conventions.

## Implementation rules

- Do not alter stock formulas or lifecycle allocation rules.
- Do not add active-market caches or relationship caches in this PR.
- Generated adapters must continue to use literal map names only.
- Writers must remove an old map entry first, then re-add only positive values.
- Debug/test events that intentionally validate reconciliation may explicitly enter test-audit mode; ordinary debug visibility must not imply audit.
- Automatic reconciliation is limited to monthly audit mode and the guarded four-year cadence; startup and normal/debug monthly runtime do not auto-reconcile.

## Acceptance criteria

- Normal runtime sets `modeu5_runtime_mode_normal` when debug is off.
- Basic debug sets `modeu5_runtime_mode_debug`.
- Verbose debug remains a visibility setting only. Deterministic reconciliation fixtures can use test-audit mode.
- Debug capture effects are no-op in normal runtime.
- Zero stock/capacity/aggregate values are not persisted to variable maps by generated adapters.
- Opening-stock initialization avoids country scans for zero-source market x good pairs unless audit mode is active.
- Full all-market validation is not called by startup, normal monthly runtime, verbose debug runtime, or four-year reconciliation.
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

Then follow:

```txt
docs/tests/PERF_01_LOW_RISK_QUICK_WINS_RUNBOOK.md
```

## Known limitations

This PR does not implement the larger issue #60 cache layers. It is intentionally
limited to low-risk guardrails and map hygiene.

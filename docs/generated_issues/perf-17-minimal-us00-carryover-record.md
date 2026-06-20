# PERF-17 - Minimal US-00 Carryover Record

## User Story

As a ModeU5 maintainer, I want normal runtime to persist only the US-00 fields
required for gameplay carryover, so that monthly processing avoids maintaining
full diagnostic ledger maps unless strict/debug/audit mode explicitly needs
them.

## Context

US-00 used to persist every diagnostic field globally after each monthly record
calculation:

- produced;
- added;
- rejected;
- overproduction ratio;
- effective overproduction ratio;
- void wealth;
- void taxable proxy;
- production penalty;
- active marker.

Only `production_penalty` is needed by later gameplay as next-month carryover.
The active marker remains useful for PERF-15 dispatch. The other fields are
diagnostic/full-ledger state.

## Selected Design

- Add `NVE : Accounting Persistence` as a pre-campaign game rule.
- Default to `Minimal`.
- Keep `Strict Full Ledger` available for validation and exact diagnostics.
- Allow full ledger persistence when strict, debug, or audit mode is active.
- In normal minimal runtime, remove stale diagnostic maps and persist only:
  - `modeu5_<good>_production_penalty_by_market`;
  - `modeu5_<good>_us00_active_record_by_market`.
- Keep monthly US-00 arithmetic transaction-local so produced/added/rejected,
  ratios, void wealth, and penalty are calculated in one pass before persistence
  policy is applied.

## Acceptance Criteria

- [ ] Minimal accounting persistence is the default.
- [ ] Strict full-ledger accounting remains selectable.
- [ ] Normal runtime keeps production penalty persistent.
- [ ] Normal runtime does not persist produced/added/rejected after the monthly
      tick.
- [ ] Normal runtime does not persist overproduction ratio, effective ratio,
      void wealth, or taxable proxy after the monthly tick.
- [ ] Debug/audit/strict runtime can still persist the full diagnostic ledger.
- [ ] Existing US-00 test helpers still exercise full ledger through explicit
      test audit mode.

## Manual Test Scenario

Static checks:

```sh
./tools/generate_all.sh
./tools/audit_modeu5_persistent_state.sh
./tools/validate_module_packages.sh
git diff --check
./tools/install_local_packages.sh --check
```

Runtime strict/debug smoke:

```txt
event modeu5_revalidate_debug.1
Select "Revalidate main operations"
```

Expected summary after closing EU5:

```sh
./tools/summarize_modeu5_test_logs.sh
```

```txt
Failed: 0
Blocked: 0
Missing expected scenarios: 0
```

## Known Limitations

- Minimal mode is structurally implemented, but runtime validation must still
  compare strict and minimal campaigns over at least two monthly ticks.
- Human-relevant full-ledger mode is not implemented here; it belongs to
  PERF-19.
- Migration and stale-field reporting are not complete here; they belong to
  PERF-20.


# PERF-20 - Migration, Audit, and Validation Guardrails

## User Story

As a ModeU5 maintainer, I want explicit guardrails for strict/full-ledger to
minimal persistence migration, so that retired diagnostic fields do not survive
as stale authoritative-looking data after the fourth-phase persistence reduction.

## Context

PERF-17 and PERF-19 reduce normal-runtime full-ledger writes. Existing saves or
strict/debug campaigns may still contain old produced/added/rejected/ratio/void
diagnostic maps.

Those fields are useful for strict/debug/audit, but must not be treated as
authoritative in minimal mode.

## Selected Design

- Generate `modeu5_clear_retired_us00_diagnostic_fields_good_<good>`.
- Generate `modeu5_clear_retired_us00_diagnostic_fields_all_goods`.
- Generate `modeu5_migrate_current_country_us00_minimal_persistence`.
- The migration clears:
  - produced;
  - added;
  - rejected;
  - overproduction ratio;
  - effective overproduction ratio;
  - void wealth;
  - void taxable proxy;
  - all-goods market void wealth aggregate;
  - current-month UI diagnostic cache counters.
- The migration deliberately preserves:
  - country stock;
  - market aggregate stock;
  - capacity and capacity breakdown;
  - production penalty carryover;
  - US-00 active marker.

## Acceptance Criteria

- [ ] Migration clear helpers are generated per good.
- [ ] Migration can be run for the current country through a single helper.
- [ ] Migration never clears authoritative stock maps.
- [ ] Migration never clears shared capacity maps.
- [ ] Migration never clears production penalty carryover.
- [ ] Migration never clears the PERF-15 active marker.
- [ ] Static validation fails if the wheat migration fixture disappears.

## Manual Test Scenario

Static checks:

```sh
./tools/generate_all.sh
./tools/audit_modeu5_persistent_state.sh
./tools/validate_module_packages.sh
git diff --check
./tools/install_local_packages.sh --check
```

Runtime migration smoke:

```txt
Start with NVE : Accounting Persistence = Strict Full Ledger.
Run one US-00 monthly runtime scenario so diagnostic ledger maps exist.
Switch to a test save or debug setup where minimal migration can be invoked.
Run modeu5_migrate_current_country_us00_minimal_persistence for the current country.
Run event modeu5_revalidate_debug.1 and select Revalidate main operations.
```

Expected:

```txt
Retired diagnostic maps are absent or ignored.
Production penalty still applies.
Stock conservation still holds.
Capacity still reads from shared country-market maps.
Main revalidation has Failed: 0, Blocked: 0, Missing expected scenarios: 0.
```

## Known Limitations

- This PR adds the migration primitive and static guardrails. It does not add a
  player-facing migration button.
- Runtime migration validation still needs a commit-specific EU5 test comment.
- Strict/debug/audit modes may still recreate full diagnostic ledger fields by
  design.


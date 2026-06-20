# PERF-19 - Human-Relevant Full-Ledger Policy

## User Story

As a ModeU5 maintainer, I want full US-00 diagnostic ledger persistence to be
available only for markets relevant to human countries, so that performance
mode can keep rich diagnostics where a player is likely to inspect them without
forcing global full-ledger writes.

## Context

PERF-17 introduced a minimal default and strict full-ledger mode. Issue #94 also
allows a middle policy: full ledger for human-relevant markets, minimal
carryover elsewhere.

The existing PERF-02 helper already builds `modeu5_performance_relevant_markets`
through confirmed `human country -> every_market_present_in_country` traversal.

## Selected Design

- Add `Human-Relevant Full Ledger` to `NVE : Accounting Persistence`.
- Keep `Minimal` as default.
- Keep `Strict Full Ledger` as global diagnostic fallback.
- Rebuild human-relevant markets once per calendar month when the
  human-relevant policy is active.
- Allow generated US-00 adapters to persist full diagnostic ledger fields only
  when the current market is in the human-relevant list, or when strict/debug/
  audit mode is active.

## Acceptance Criteria

- [ ] Human-relevant full-ledger mode is selectable as a game rule.
- [ ] Strict global full-ledger mode remains selectable.
- [ ] Human-relevant markets use confirmed native country-to-market traversal.
- [ ] Human-relevant list rebuild is guarded by a monthly stamp.
- [ ] Full-ledger persistence remains non-authoritative and does not control
      stock conservation, capacity, or next-month penalty behavior.
- [ ] Non-human-relevant markets keep minimal carryover.

## Manual Test Scenario

Static checks:

```sh
./tools/generate_all.sh
./tools/audit_modeu5_persistent_state.sh
./tools/validate_module_packages.sh
git diff --check
./tools/install_local_packages.sh --check
```

Runtime smoke:

```txt
Start a disposable campaign with NVE : Accounting Persistence = Human-Relevant Full Ledger.
Wait one month.
Run event modeu5_revalidate_debug.1 and select Revalidate main operations.
```

Expected:

```txt
ModeU5 human-relevant market list is rebuilt once for the month.
Main revalidation has Failed: 0, Blocked: 0, Missing expected scenarios: 0.
Full US-00 diagnostic values remain available in human-relevant markets.
AI-only markets remain minimal unless debug/audit/strict mode is active.
```

## Known Limitations

- Human-relevant markets are based on country market presence, not a custom UI
  selection hook.
- Non-sticky clear-on-exit cleanup is completed by PERF-20 migration/guardrails.
- This mode is a diagnostic persistence policy only; it must not alter stock,
  capacity, production penalty, or demand resolution.


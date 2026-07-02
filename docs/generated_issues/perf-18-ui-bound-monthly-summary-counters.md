# PERF-18 - UI-Bound Monthly Summary Counters

## User Story

As a ModeU5 maintainer, I want player-facing monthly overproduction diagnostics
to have a compact human-country cache boundary that follows the latest US-10-UI
spec, so that future UI work can display current values without forcing global
produced/added/rejected/ratio/void persistence or guessing missing resolver
values.

## Context

Issue #94 selects a minimal normal-runtime UI surface:

- `modeu5_<good>_ui_monthly_surplus_by_market`
- `modeu5_<good>_ui_monthly_consumption_by_market`

The latest US-10-UI reference is:

```txt
docs/generated_issues/us-10-ui-visibility-of-stock-resolution.md
at commit a558f2bd98de837368f80b5eab9d05fdc42777ca
```

That spec says the player-facing `Overproduction` column is current monthly
surplus after stock resolution:

```txt
monthly_surplus = monthly_production - monthly_consumption - monthly_net_transfers_out
```

It also says the UI must not create a second authoritative stock, capacity,
production, consumption, transfer, resolver, or modifier map. Therefore these
maps are treated only as current-month cached diagnostics. They are not
authoritative economy state and must not be populated from rejected production
or stock-over-capacity values.

## Selected Design

- Generate literal per-good UI diagnostic cache maps.
- Store counters only for human countries.
- Clear the current market/good UI cache during monthly processing so stale
  current-month values do not leak into the next month.
- Provide a generated storage helper for US-10 to write real
  `monthly_surplus` and `monthly_consumption` values after resolution.
- Do not write rejected production into the UI surplus cache.
- Do not derive missing consumption or transfer values from stock snapshots.
- Keep full formula-component counters out of normal runtime.

## Acceptance Criteria

- [ ] Generated adapters include
      `modeu5_<good>_ui_monthly_surplus_by_market`.
- [ ] Generated adapters include
      `modeu5_<good>_ui_monthly_consumption_by_market`.
- [ ] UI counters are country-scoped and market-keyed.
- [ ] UI counters are written only for human country scope when an explicit
      US-10/debug writer provides current-month values.
- [ ] UI counters are cleared before current-month rewrite.
- [ ] The audit allows these approved UI counters while still blocking
      unclassified UI shadow maps.
- [ ] Rejected production is not stored as the player-facing overproduction
      surplus.

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
event modeu5_revalidate_debug.1
Select "Revalidate main operations"
```

Expected summary:

```txt
Failed: 0
Blocked: 0
Missing expected scenarios: 0
```

## Known Limitations

- Until US-10 writes consumption and transfer counters, the compact
  overproduction value remains unavailable. The UI must hide or mark the column
  unavailable rather than guessing.
- PERF-18 provides the current-month cache boundary and lifecycle. A later
  US-10 PR must write the final
  `monthly_surplus = production - consumption - net_transfers_out` value after
  resolution.
- Missing historical diagnostic ledger values must remain unavailable, not
  guessed from stock snapshots.

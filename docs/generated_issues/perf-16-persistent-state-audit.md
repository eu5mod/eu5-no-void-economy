# PERF-16 - Persistent-State Audit

## User Story

As a ModeU5 maintainer, I want every persistent variable map and variable list
to be classified by purpose before fourth-phase persistence changes begin, so
that future performance PRs can remove or narrow diagnostic state without
silently losing authoritative gameplay state.

## Context

Issue #94 moves the optimization discussion from generated helper count to
persistent-state cost. A logical country x market x good record expands into a
family of static maps, so each additional field has runtime, save-state, and
maintenance cost.

PERF-16 does not change gameplay. It creates the audit and validation guard that
later PERF-17 through PERF-20 PRs must satisfy.

## Selected Design

- Add `docs/technical/PERSISTENT_STATE_AUDIT.md`.
- Add `tools/audit_modeu5_persistent_state.sh`.
- Classify each structured ModeU5 persistent map/list by owner, key, lifecycle,
  reader group, persistence reason, and fourth-phase target.
- Wire the audit into `tools/validate_module_packages.sh`.
- Keep scalar runtime flags and debug result variables out of this audit.

## Acceptance Criteria

- [ ] A persistent-state audit document exists.
- [ ] Every maintained ModeU5 persistent variable map family is classified.
- [ ] Every maintained ModeU5 variable-list family is classified.
- [ ] The audit reports zero UI shadow maps.
- [ ] Validation fails if a new structured map/list family appears without
      audit classification.

## Manual Test Scenario

Static checks:

```sh
./tools/generate_all.sh
./tools/audit_modeu5_persistent_state.sh
./tools/validate_module_packages.sh
git diff --check
./tools/install_local_packages.sh --check
```

Expected audit summary:

```txt
ModeU5 persistent state audit
Stock maps: kept
Capacity maps: kept/shared
Capacity breakdown maps: kept
US-00 gameplay carryover maps: kept
US-00 full diagnostic ledger maps: strict/debug/audit or human-relevant only
UI monthly counter maps: human country current-month only
UI shadow maps: 0
Unclassified persistent maps: 0
```

## Known Limitations

- No EU5 runtime validation is required because this PR is documentation and
  static validation only.
- It does not remove or migrate any map.
- It does not implement minimal persistence; that belongs to PERF-17.

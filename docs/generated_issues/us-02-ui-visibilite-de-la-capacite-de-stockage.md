# US-02-UI — Visibilité de la capacité de stockage

Labels: none

## User Story

```txt
US-02-UI — Visibilité de la capacité de stockage
```

As a player, I want to understand where storage capacity comes from and why it changes.

## Functional objective

Show capacity contributions from locations and confirmed building categories, plus used and available storage and saturation risk.

## Runtime position

```txt
Monthly step: read after capacity recalculation
Depends on counters from: US-02 and US-01
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Capacity breakdown inputs | country × market | confirmed location/building iterators plus US-02 counters | CONFIRMED | 033-035 |
| Used/available storage | ModeU5 | US-01 values | CONFIRMED | 015-018 |
| Debug/localized display | event/UI | event triggers, logs, tooltips, and localization keys | CONFIRMED | 013-014 |

## Files expected to change

```txt
in_game/events/
in_game/localization/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-01, US-02, TECH-01
Blocks: visible capacity diagnosis
Related US: US-01-UI, US-03-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and project debug conventions.
- Keep the display read-only.
- Separate base, commercial, logistic, and confirmed foreign contributions.
- Show fallback/excluded contribution categories.
- Do not require a complete custom stock ledger.

## US-specific boundary checks

- [ ] Displayed totals exactly match the capacity used by stock effects.
- [ ] Unconfirmed building categories are not shown as active.

## Acceptance criteria

- [ ] Capacity origin, used storage, and available storage are readable.
- [ ] A building/location loss produces an explainable delta.
- [ ] Saturation risk is visible before production rejection.
- [ ] Debug reports excluded or fallback contributions.

## Manual test scenario

### Setup

```txt
Record a market capacity breakdown
Add and remove one confirmed storage-contributing building
```

### Expected result

```txt
The relevant contribution and total change by the configured amount
Used and available storage remain consistent with US-01
```

## Known limitations

MVP may use a debug event rather than custom UI. Building contribution exposure remains gated by TECH-01.

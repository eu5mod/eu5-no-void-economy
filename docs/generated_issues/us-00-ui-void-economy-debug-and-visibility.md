# US-00-UI — Void Economy Debug and Visibility

Labels: `blocked:engine-exposure`

## User Story

```txt
US-00-UI — Void Economy Debug and Visibility
```

As a player or modder, I want to see where production is rejected, what it is worth, and what future penalty it causes.

## Functional objective

Provide mandatory debug visibility for the complete US-00 pipeline and, where feasible, a tooltip or ModeU5 panel without making custom GUI a prerequisite for MVP.

## Runtime position

```txt
Monthly step: reads US-00 outputs after steps 15-17
Depends on counters from: US-00.1 through US-00.4
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Debug/test event | country/global | event/console event | TO_TEST | 013 |
| Localized modifier/tooltip | UI/localization | localization files | TO_TEST | 014 |
| Production-source diagnostics | source × location × good → producing country × market × good | US-00.1 attribution debug | TO_TEST | 003-006, 021, 081 |
| US-00 keyed outputs | country × market × good | variable maps, scoped variables, or generated keys | TO_TEST | 007, 025 |
| Optional custom panel | UI | ModeU5 window | TO_TEST | new entry |

## Files expected to change

```txt
in_game/events/
in_game/localization/
in_game/common/modifiers/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-00.1, US-00.2, US-00.3, US-00.4, TECH-01
Blocks: transparent balancing and validation of EPIC US-00
Related US: US-05.1, US-05-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and `DEBUG_CONVENTIONS.md`.
- Debug is mandatory; a complete custom GUI is not.
- Show produced, added, rejected, ratios, buffer, penalty, modifier mode, price source, and void wealth.
- Show the production source, source location, credited producing country, and derived market ledger key when source-level data is available.
- Show market and country aggregates.
- Make fallback, theoretical-only behavior, and slider correction status explicit.
- Never perform economic reconciliation from the display layer.

## US-specific boundary checks

- [ ] The display does not imply rejected output directly reduces Estate income.
- [ ] The player can distinguish applied, fallback, and theoretical-only penalties.
- [ ] Possible double penalties are visible.

## Acceptance criteria

- [ ] A controlled test can inspect all mandatory US-00 values.
- [ ] Market/good sources of void wealth are identifiable.
- [ ] Price source and fallback mode are shown.
- [ ] Next-month penalty and application mode are shown.
- [ ] Market and country aggregates reconcile with detailed values.
- [ ] UI/debug confirms whether US-05.1 receives void wealth.
- [ ] No reconciliation is hidden.

## Manual test scenario

### Setup

```txt
Create one fully stockable good and one capacity-rejected good
Run the month-end US-00 pipeline
Open the supported debug event, tooltip, or panel
```

### Expected result

```txt
Both goods display produced/added/rejected values
Only significant effective overproduction shows a penalty
Void wealth, price source, aggregation, and modifier mode are readable
No value is silently reconciled
```

## Known limitations

MVP may be debug-only. Custom GUI work remains outside scope unless separately approved; any UI exposure discovered must be recorded in TECH-01.

# US-06-UI — Visibilité du coût logistique du trade

Labels: `blocked:engine-exposure`

## User Story

```txt
US-06-UI — Visibilité du coût logistique du trade
```

As a player, I want to see how transport cost changes effective trade profitability and who pays it.

## Functional objective

Expose gross income when available, transport cost, monthly reconciliation, estimated effective income, payer, missing data, imputation mode, and display mode.

## Runtime position

```txt
Monthly step: read after US-06 reconciliation
Depends on counters from: US-06
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| US-06 outputs | trade/country | accumulators and debug records | TO_TEST | 047-061 |
| Visible UI path | modifier/tooltip/window | country modifier/custom UI/debug | TO_TEST | 062 |
| Localization | UI | localization files | TO_TEST | 014 |

## Files expected to change

```txt
in_game/common/modifiers/
in_game/events/
in_game/localization/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-06, TECH-01
Blocks: transparent transport reconciliation
Related US: US-05-UI, US-10-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and no-hidden-reconciliation rules.
- Debug visibility is mandatory; native trade-line integration is not.
- Show payer and direct/reconciliation/skipped mode.
- Show missing-data reasons.
- Keep UI read-only.

## US-specific boundary checks

- [ ] Displayed basis is transferred quantity when provided by US-10.2.
- [ ] Same-market stock resolution is never shown as a charged trade.

## Acceptance criteria

- [ ] The player can identify costly routes and the paying country.
- [ ] Direct and monthly reconciliation modes are distinguishable.
- [ ] Missing-data skips are visible.
- [ ] Monthly transport total and reconciliation reconcile.
- [ ] No cost is hidden.

## Manual test scenario

### Setup

```txt
Create one valid charged transfer and one skipped missing-data trade
Open the supported modifier, report, or debug window
```

### Expected result

```txt
Valid cost, payer, basis, and effective estimate are shown
Skipped item and reason are shown
Monthly total matches US-06
```

## Known limitations

MVP may use a visible modifier or debug report rather than native trade tooltips. UI exposure remains `TO_TEST`.

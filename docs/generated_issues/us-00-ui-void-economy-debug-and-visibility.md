# US-00-UI — Folded into US-10-UI Super Visibility Story

Labels: `module:core`, `superseded-by:US-10-UI`

## Status

US-00 UI/debug visibility is retained as a mandatory diagnostic requirement but
is no longer a separate implementation story. Its requirements are folded into
US-10-UI so the player/modder visibility layer covers the full stock lifecycle:
production admission, rejected production, void wealth, penalties, demand
resolution, transfers, and unsatisfied quantities.

## User Story

```txt
US-00-UI — Folded into US-10-UI Super Visibility Story
```

As a player or modder, I want to see where production is rejected, what it is worth, and what future penalty it causes.

## Functional objective

Provide mandatory debug visibility for the complete US-00 pipeline through the US-10-UI super visibility story. A custom GUI remains optional; deterministic logs and debug events are sufficient for MVP validation.

## Runtime position

```txt
Monthly step: reads US-00 outputs after steps 8 and 13-15
Depends on counters from: US-00.1 through US-00.4
Feeds counters to: US-10-UI player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Debug/test event and logs | effect scope | `trigger_event_silently`, `trigger_event_non_silently`, `debug_log` | CONFIRMED | 013 |
| Localized modifier/tooltip hooks | UI/localization | `custom_tooltip`, modifier `desc`, object localization keys | CONFIRMED | 014 |
| Location production diagnostics | country × location × market × good | US-00.1 `goods_output(goods:<good>)` / `raw_material_output` aggregation debug | CONFIRMED | 021 |
| Ledger-country attribution diagnostics | country-rooted cycle → owned location | current country plus owned-location and market context | CONFIRMED | 003-005, 011, 081 |
| US-00 logical record | country × market × good | direct reads of ledger, ratio, void-wealth, and penalty fields through the confirmed map family | CONFIRMED | 007, 025 |
| Optional custom panel | UI | custom ModeU5 window | OUT_OF_SCOPE | N/A |

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
Blocks: none directly; requirements inherited by US-10-UI
Related US: US-10-UI, US-05-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and `DEBUG_CONVENTIONS.md`.
- Debug is mandatory; a complete custom GUI is not.
- Show produced, added, rejected, ratios, buffer, penalty, modifier mode, price source, and void wealth.
- Show the location, current ledger country, derived market, good, and aggregated output value.
- Show market and country aggregates.
- Read authoritative US-00 maps directly; do not maintain a second UI/debug copy.
- Use generated per-good readers where the physical map name is good-specific.
- Make fallback, theoretical-only behavior, and production-modifier application status explicit through the US-10-UI diagnostic surface.
- Never perform an economic adjustment from the display layer.

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
- [ ] UI/debug distinguishes tracked void wealth from the US-05 Economic Base.
- [ ] No economic correction is hidden in the display layer.

## Manual test scenario

### Setup

```txt
Create one fully stockable good and one capacity-rejected good
Run the month-end US-00 pipeline
Open the supported US-10-UI debug event, tooltip, or panel
```

### Expected result

```txt
Both goods display produced/added/rejected values
Only significant effective overproduction shows a penalty
Void wealth, price source, aggregation, and modifier mode are readable
No value is silently adjusted
```

## Known limitations

MVP may be debug-only. Custom GUI work remains outside scope unless separately approved; any UI exposure discovered must be recorded in TECH-01. This file remains for traceability only and should not be implemented as a standalone UI ticket.

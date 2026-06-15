# US-09 — Production Efficiency de +5 % bonus

Labels: `module:economy`

## User Story

```txt
US-09 — Production Efficiency de +5 % bonus
```

As a player, I want a global +5% Production Efficiency compensation for ModeU5's stock, decay, and production-correction constraints.

## Functional objective

Apply a clearly identified global `+5%` production-efficiency modifier to all eligible countries at the normative monthly position, while retaining compatibility with stock-aware transformation chains.

## Module / availability

```txt
Package: Rebalance Economy
Activation: optional companion package
Behavior when absent:
  apply no ModeU5 Production Efficiency compensation modifier
  Core stock constraints and void-economy correction remain active
```

## Runtime position

```txt
Monthly step: 2
Depends on: confirmed production-efficiency modifier and application effect
Feeds counters to: vanilla production read at step 4
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Production efficiency modifier | country | `global_production_efficiency` | CONFIRMED | 066 |
| Iterate/apply to countries | none → country | `every_country` plus `add_country_modifier` | CONFIRMED | 001, 009 |
| Monthly invocation at runtime step 2 | country | `monthly_country_pulse` → shared ModeU5 monthly dispatcher | CONFIRMED | 011 |
| Transformation compatibility | ModeU5 production chain | apply before production read; preserve stock-add contract | CONFIRMED | internal |

## Files expected to change

```txt
in_game/common/modifiers/
in_game/common/scripted_effects/
in_game/common/on_action/
in_game/localization/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: confirmed modifier/application exposure, TECH-01
Blocks: US-09-UI
Related US: US-00.3, stock-aware production pipeline
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/MODULE_OPTION_MODEL.md`; do not apply or retain the modifier when the Rebalance Economy package is absent.
- Use exactly the confirmed modifier semantics.
- Apply the compensation before monthly production is read.
- Keep it distinct from national/technology bonuses.
- Do not use this issue to redesign transformation formulas beyond compatibility.
- Use the confirmed shared `monthly_country_pulse` dispatcher; do not register a second monthly mechanism.

## US-specific boundary checks

- [ ] The modifier is compensation, not a hidden replacement for US-00 penalties.
- [ ] Stock mutation remains centralized.

## Acceptance criteria

- [ ] Every eligible country receives exactly +5% through the confirmed path.
- [ ] Application timing is before monthly production measurement.
- [ ] The bonus does not bypass capacity or stock rules.
- [ ] Transformation outputs remain compatible with stock entry.
- [ ] Debug and localization identify ModeU5 as the source.

## Manual test scenario

### Setup

```txt
Compare controlled eligible production with the modifier disabled/enabled
Keep other modifiers constant
```

### Expected result

```txt
Confirmed production-efficiency behavior changes by +5%
Stock capacity/rejection rules still apply afterward
```

## Known limitations

The exact `global_production_efficiency` modifier, country modifier effect, and `monthly_country_pulse` are documented. The shared monthly dispatcher must apply the compensation at runtime step 2.

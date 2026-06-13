# US-05.1 — Exclusion of Void Wealth from Slider Cost Base (Outside MVP because optional since the solution is to bring a negative production modifier)

Labels: `blocked:engine-exposure`

## User Story

```txt
US-05.1 — Exclusion of Void Wealth from Slider Cost Base (Outside MVP because optional since the solution is to bring a negative production modifier)
```

As a player, I want tracked void wealth excluded from relevant slider costs so unstockable production is not penalized twice.

## Functional objective

Optionally subtract US-00.4 void wealth from the US-05 base, bounded at zero, only when this correction is enabled or required to prevent double penalty.

## Runtime position

```txt
Monthly step: 20, only when enabled/needed
Depends on counters from: US-00.4 and US-05
Feeds counters to: US-05-UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Country void wealth | ModeU5 | `modeu5_total_void_wealth` | CONFIRMED | 046 |
| Market void wealth | ModeU5 | `modeu5_void_wealth_by_market` | CONFIRMED | 046 |
| Read vanilla slider cost | country/slider | current Stability/Court cost value | NOT_CONFIRMED | 041 |
| Monthly trade-income input | country | `monthly_trade_income` | CONFIRMED | 042 |
| Country wealth input | country | country `wealth` or reliable aggregate | NOT_CONFIRMED | 043 |
| Replace slider cost base | country/slider | direct cost-base hook | NOT_CONFIRMED | 044 |
| Visible correction | country/UI | direct base or visible reconciliation | NOT_CONFIRMED | 045 |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/common/modifiers/
in_game/localization/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-00.4, US-05, confirmed correction path
Blocks: optional double-penalty prevention
Related US: US-00.3, US-05-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Treat this issue as optional/MVP+ unless needed to prevent double penalty.
- Calculate corrected base as `max(0, slider_base - void_wealth)`.
- Affect only the two US-05 sliders.
- Make direct, reconciliation, or debug-only mode visible.
- Do not mutate stock or hide correction.

## US-specific boundary checks

- [ ] Void wealth cannot both raise slider cost and trigger the future production penalty.
- [ ] Optional status is documented in player/modder-facing output.

## Acceptance criteria

- [ ] Corrected base never becomes negative.
- [ ] Country or market correction uses the matching US-00.4 aggregation.
- [ ] Only Stability and qualifying Court/Government Power are affected.
- [ ] Vanilla, target, void wealth, corrected base, reconciliation, and net cost are visible.
- [ ] Disabled mode leaves US-05 behavior unchanged.

## Manual test scenario

### Setup

```txt
US-05 base 1,000; total void wealth 200
Compare enabled and disabled correction modes
```

### Expected result

```txt
Enabled corrected base: 800
Disabled base: 1,000
The correction mode and effective cost are visible
```

## Known limitations

This issue remains outside the required MVP unless double-penalty prevention demands it. Monthly trade income is documented, but slider-cost reading, country wealth, base replacement, and a confirmed visible correction path remain `NOT_CONFIRMED`; debug-only calculation is acceptable.

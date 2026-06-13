# US-05 — Economic Base fondée sur Wealth + Trade Income

Labels: `blocked:engine-exposure`

## User Story

```txt
US-05 — Economic Base fondée sur Wealth + Trade Income
```

As a player, I want Stability and legitimacy-producing Court/Government Power costs based on Wealth plus Trade Income rather than Tax Base.

## Functional objective

Calculate `modeu5_slider_cost_base = Wealth + Trade Income` for only the two specified sliders; replace their base directly when exposed or apply a visible monthly reconciliation otherwise.

## Runtime position

```txt
Monthly step: 19
Depends on counters from: country wealth and trade income
Feeds counters to: US-05.1 and US-05-UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Vanilla slider cost | country/slider | readable Stability/Court cost value | NOT_CONFIRMED | 041 |
| Monthly trade income | country | `monthly_trade_income` | CONFIRMED | 042 |
| Country wealth | country | country `wealth` or reliable aggregate | NOT_CONFIRMED | 043 |
| Replace slider base | slider/static script | direct slider cost-base hook | NOT_CONFIRMED | 044 |
| Visible reconciliation | country/UI | sized modifier or gold effect with visible presentation | NOT_CONFIRMED | 045 |

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
Depends on: confirmed wealth, trade-income, slider, and reconciliation exposure
Blocks: US-05.1, US-05-UI
Related US: US-00.4, US-06
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Affect only Stability Investment and legitimacy-producing Court/Government Power.
- Prefer direct base replacement when confirmed.
- Otherwise use one visible monthly reconciliation fallback.
- Never silently reconcile a slider.
- Do not modify other expected expenses in MVP.

## US-specific boundary checks

- [ ] Tax Base is excluded from the ModeU5 target calculation.
- [ ] Diplomatic, military, fort, subsidy, minting, and food sliders remain unchanged.

## Acceptance criteria

- [ ] Target base equals Wealth plus Trade Income.
- [ ] Only the two specified sliders use the target.
- [ ] Direct and reconciliation modes produce traceable effective cost.
- [ ] Reconciliation mode is visible in UI/debug/modifier/tooltip.
- [ ] Other sliders are unchanged.
- [ ] Missing exposure and fallback choice are recorded in TECH-01.

## Manual test scenario

### Setup

```txt
Country A: high Wealth/low Tax Base
Country B: low Wealth/high Tax Base
Control equal relevant slider settings
```

### Expected result

```txt
ModeU5 target costs follow Wealth + Trade Income, not Tax Base
Only Stability and qualifying Court/Government Power differ
Any reconciliation is visible
```

## Known limitations

Monthly trade income is documented. Vanilla slider cost, country wealth, direct base replacement, and a confirmed visible reconciliation path remain `NOT_CONFIRMED`; debug-only calculation is required until one safe path is accepted.

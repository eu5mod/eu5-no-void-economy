# US-05 — Economic Base definition

Labels: `blocked:engine-exposure`, `module:economy`

## User Story

```txt
US-05 — Economic Base definition
```

As a player, I want Stability and legitimacy-producing Court/Government Power costs based on Wealth plus Trade Income rather than Tax Base.

## Functional objective

Replace the Economic Base formula used by Stability Investment and legitimacy-producing Court/Government Power with `modeu5_slider_cost_base = Wealth + Trade Income`. Do not implement monthly reconciliation as an alternative path.

## Module / availability

```txt
Package: Rebalance Economy
Activation: optional companion package
Behavior when absent:
  leave the vanilla Economic Base formula and all affected slider costs untouched
```

## Runtime position

```txt
Monthly step: 16
Depends on counters from: country wealth and trade income
Feeds counters to: US-05-UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Vanilla slider cost | country/slider | not required by direct formula replacement | OUT_OF_SCOPE | 041 |
| Monthly trade income | country | `monthly_trade_income` | CONFIRMED | 042 |
| Country wealth | country | script equivalent to GUI `Country.GetTotalWealth`, or confirmed aggregate | TO_TEST | 043 |
| Economic Base replacement hook | economy/slider formula context | controlled call site using `modeu5_slider_cost_base = Wealth + monthly_trade_income` | TO_TEST | 044 |
| Visible reconciliation | country/UI | not used by direct formula replacement | OUT_OF_SCOPE | 045 |

## Files expected to change

```txt
in_game/common/script_values/
in_game/common/scripted_effects/
in_game/common/on_action/
in_game/common/modifiers/
in_game/localization/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: confirmed wealth, trade-income, and Economic Base formula-hook exposure
Blocks: US-05-UI
Related US: US-00.4
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/MODULE_OPTION_MODEL.md`; do not replace the formula when the Rebalance Economy package is absent.
- Affect only Stability Investment and legitimacy-producing Court/Government Power.
- Replace the confirmed Economic Base formula/call site with `modeu5_slider_cost_base`.
- Do not read the final vanilla slider cost merely to reverse-engineer or reconcile it.
- Do not create a monthly gold/modifier reconciliation path.
- Do not modify other expected expenses in MVP.

## US-specific boundary checks

- [ ] Tax Base is excluded from the ModeU5 target calculation.
- [ ] Diplomatic, military, fort, subsidy, minting, and food sliders remain unchanged.

## Acceptance criteria

- [ ] Target base equals Wealth plus Trade Income.
- [ ] Only the two specified sliders use the target.
- [ ] The replaced Economic Base formula and both inputs are traceable.
- [ ] No reconciliation modifier or gold adjustment is applied.
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
No reconciliation is applied
```

## Known limitations

Monthly trade income is confirmed and local vanilla GUI proves total country wealth exists through `Country.GetTotalWealth`. The gameplay-script wealth value and the modifiable Stability/Court Economic Base call site remain `TO_TEST`. Reading final slider costs and visible reconciliation are out of scope for the direct-formula design.

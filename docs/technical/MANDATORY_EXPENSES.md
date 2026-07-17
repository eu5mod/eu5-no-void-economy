# Mandatory expenses

## Stability MVP

The Rebalance Economy package changes Stability investment from an optional
bonus into a budget commitment with a vanilla-neutral midpoint.

```txt
slider contribution = slider position x 1.0
mandatory baseline = -0.5
positive-Stability offset = max(0, Stability / 100)
net contribution = slider contribution - 0.5 + positive-Stability offset
```

Therefore:

```txt
At Stability 0:

0% slider   -> -0.5
50% slider  ->  0.0 (vanilla zero-investment baseline)
100% slider -> +0.5 (vanilla maximum positive contribution)

At Stability +25:

0% slider   -> -0.25
50% slider  -> +0.25
100% slider -> +0.75
```

`STABILITY_INVEST_FACTOR = 1` doubles the vanilla positive range. The permanent
`cbp_mandatory_stability_expense` country modifier supplies the additive
`stability_investment = -0.5` baseline. The
`cbp_positive_stability_expense_offset` auto-modifier scales a unit
`stability_investment` contribution by `Stability x 0.01`, and is active only
while Stability is positive. Together they implement
`-0.5 + max(0, Stability / 100)`. `stability_decay` is intentionally left
unchanged because it is Vanilla's percentage movement toward zero, not a flat
monthly expense.

The define is grouped with the other expense-slider and Economic Base tuning in
`loading_screen/common/defines/cbp_slider_defines.txt`.

The modifier is package-owned. It is applied to all countries on game start and
game load, then guarded on each monthly country pulse so newly created countries
receive it without repeatedly replacing existing modifiers.

No reconciliation fallback is implemented. TECH-01 151 remains runtime-pending
until the Economy interface confirms the `-0.5` modifier contribution and the
slider reaches `+1.0` before the baseline is applied.

## Court and government power

Vanilla Court spending has a fixed `-1` monthly decay and a slider maximum of
`+2`, producing a net range from `-1` to `+1`. CBP adds another `-1` baseline
and increases `GOV_POWER_INVEST_FACTOR` to `3.0`:

```txt
slider contribution = slider position x 3.0
total baseline = vanilla -1 + CBP -1
net contribution = slider contribution - 2
```

Therefore:

```txt
0% slider     -> -2.0
50% slider    -> -0.5
66.7% slider  ->  0.0 (maintenance point)
100% slider   -> +1.0 (vanilla maximum monthly increase)
```

The package applies the additional `-1` to every government-power variant so
the shared Court slider remains symmetric across government forms and through
government changes:

```txt
monthly_legitimacy
monthly_republican_tradition
monthly_devotion
monthly_horde_unity
monthly_tribal_cohesion
```

The modifiers are always present; the engine uses the power relevant to the
country's current government form. Runtime validation must confirm the active
government power's tooltip and monthly result. No reconciliation is provided.

This deliberately follows vanilla's own generic-country modifier pattern. For
example, `ruler_primary_culture`, `ruler_accepted_culture`, and their related
static modifiers declare Legitimacy, Republican Tradition, Devotion, Horde
Unity, and Tribal Cohesion together without a government-type condition. A CBP
government-type dispatch would duplicate engine selection, require a fragile
inventory of government forms, and risk a missing baseline during government
transitions.

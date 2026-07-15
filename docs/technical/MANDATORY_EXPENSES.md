# Mandatory expenses

## Stability MVP

The Rebalance Economy package changes Stability investment from an optional
bonus into a budget commitment with a vanilla-neutral midpoint.

```txt
slider contribution = slider position x 1.0
mandatory baseline = -0.5
net contribution = slider contribution - 0.5
```

Therefore:

```txt
0% slider   -> -0.5
50% slider  ->  0.0 (vanilla zero-investment baseline)
100% slider -> +0.5 (vanilla maximum positive contribution)
```

`STABILITY_INVEST_FACTOR = 1` doubles the vanilla positive range. The permanent
`cbp_mandatory_stability_expense` country modifier supplies the additive
`stability_investment = -0.5` baseline. `stability_decay` is intentionally not
used because it is a percentage decay toward zero, not a flat monthly expense.

The modifier is package-owned. It is applied to all countries on game start and
game load, then guarded on each monthly country pulse so newly created countries
receive it without repeatedly replacing existing modifiers.

No reconciliation fallback is implemented. TECH-01 151 remains runtime-pending
until the Economy interface confirms the `-0.5` modifier contribution and the
slider reaches `+1.0` before the baseline is applied.

## Legitimacy

Legitimacy and equivalent government-power expenses retain vanilla tuning in
this PR. A later extension requires a separately approved baseline, slider
surface, and neutral-point rule; it must not infer them from Stability.

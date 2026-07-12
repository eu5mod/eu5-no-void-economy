# US-06 — War Exhaustion Political-Pressure Test

This test document describes how to validate the ModeU5 rework of War Exhaustion.
The feature neutralizes vanilla morale/production penalties and applies monthly
political pressure to Stability, Legitimacy and Rebel Threshold instead. It
conforms to the guidelines in `AGENTS.md` and the user story in issue #68.

## Setup

1. Load Core and enable the War Exhaustion rework through the CMF/Core activation toggle.
2. Confirm the activation marker used by the current branch is set: `modeu5_war_rebalance_loaded`.
3. Choose any test country and enter an active war.
4. Set or observe `war_exhaustion` at `0`, `5` and `10`.
5. Enable ModeU5 debug logging and inspect `error.log` after monthly ticks.

## Expected behaviour

| War exhaustion | Stability pressure | Legitimacy pressure | Rebel-threshold pressure |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| 5 | `5 × WAR_EXHAUSTION_STABILITY_MODIFIER`, capped | `5 × WAR_EXHAUSTION_LEGITIMACY_MODIFIER`, capped | `5 × WAR_EXHAUSTION_REBEL_THRESHOLD_MODIFIER`, capped |
| 10 | `10 × WAR_EXHAUSTION_STABILITY_MODIFIER`, capped | `10 × WAR_EXHAUSTION_LEGITIMACY_MODIFIER`, capped | `10 × WAR_EXHAUSTION_REBEL_THRESHOLD_MODIFIER`, capped |

Vanilla morale, production, trade/import and population-growth penalties from
`war_exhaustion_impact` must be absent. No duplicate War Exhaustion variable is
introduced; vanilla `war_exhaustion` remains the source of truth.

When the CMF/Core activation toggle is disabled, the monthly reconciliation must
perform no political-pressure adjustment and must not emit `MODEU5_WE_REWORK`
application lines.

## Debug output

For every country and month where War Exhaustion pressure is applied, `error.log`
should contain:

```txt
MODEU5_WE_REWORK current_war_exhaustion=<value> stability_pressure=<value> legitimacy_pressure=<value> rebel_threshold_pressure=<value> endpoint_mode=monthly_reconciliation vanilla_war_exhaustion_impact_neutralized=yes
```

## Exposure notes

If `add_stability`, `add_legitimacy`, `add_rebel_threshold`, `clamp_variable` or
`war_exhaustion_impact` override behaviour fails in script_docs or local tests,
record the limitation in `docs/technical/TECH-01_engine_exposure_matrix.md`
before shipping the fallback.

This rework does not change how War Exhaustion is gained or lost. It does not
implement Call for Peace or forced capitulation changes.

# US-19 — Imperial Hubris / Imperial Complacency

## Functional Objective

Great Powers that spend too long in comfortable peace accumulate Imperial
Complacency. Complacency represents softened military institutions, bloated
administration, ceremonial military habits, and reduced pressure to reform.

When the country is dragged into a war against another Great Power, that
complacency is burned down quickly. Minor wars only slow the decay because they
do not challenge the imperial myth in the same way.

The story is part of the Early Blobbing balance package and should make
unchecked long-peace empires less permanently stable without adding a constant
monthly global scan.

## Module / Availability

```txt
Package: Rebalance Early Blobbing
Activation: optional companion package selected before campaign start
Behavior when absent: no Imperial Complacency variables, hooks, modifiers, or debug events are loaded
```

This story belongs to `packages/modeu5_war_rebalance`, not Core. Companion
package selection remains the source of truth. There is no runtime game-rule
toggle that disables the static modifier while the package is loaded.

## Runtime Position

```txt
Monthly step: country monthly pulse reads the cached Great-Power-war state and applies complacency growth/recovery.
War hooks: war declaration, joining war, losing war, and ending war refresh the cached Great-Power-war state.
Depends on counters from: vanilla country military/economic state.
Feeds counters to: country modifier `modeu5_imperial_complacency` and debug dumps.
```

Performance rule: the monthly tick must not scan all countries or all wars to
discover whether a country has a Great Power war. That state is maintained by
war lifecycle hooks in `modeu5_has_great_power_war`, then read as a cheap country
variable during the monthly pulse.

## Required Scopes / Values / Effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Monthly country update | country | `monthly_country_pulse` | CONFIRMED | 011 |
| Great Power membership/rank | country | `great_power_ranking <= 8` | CONFIRMED | 136 |
| War lifecycle cache refresh | country / war hook | `on_war_declared`, `on_join_war`, `on_losing_war`, `on_ending_war` | CONFIRMED | 137 |
| Current enemy scan used only inside hook refresh | country -> country | `every_country_at_war_with` | CONFIRMED | 138 |
| Comfort / war pressure inputs | country | `months_since_war`, `monthly_balance`, `manpower_percentage`, `stability_percentage`, `army_tradition`, `war_exhaustion` | CONFIRMED | 139 |
| Static military penalties | static modifier | `discipline`, `army_maintenance_efficiency`, `mercenary_maintenance_efficiency`, `army_tradition_decay`, `experience_decay`, `global_manpower_modifier`, `global_army_levy_size_modifier`, `global_levy_recruitment_speed_modifier`, `mercenary_units_preference_modifier` | CONFIRMED | 140 |

## Persistent Storage / Variable-Map Contract

US-19 owns only scalar country variables. It does not require variable maps.

```txt
logical dimensions: country
logical record and fields:
  modeu5_imperial_complacency
  modeu5_imperial_last_army_tradition
  modeu5_months_since_gp_loss
  modeu5_imperial_complacency_floor
  modeu5_has_great_power_war
owner scope: country
tuple/key: none
confirmed physical storage: country variables
physical value type: numeric
default value: zero, except last army tradition initializes from `army_tradition`
write owner: US-19 scripted effects and war hooks
readers: US-19 monthly update and debug event
reset/rebuild lifecycle: refreshed on game start for current wars, on war declaration, on joining war, on losing war, and on ending war
```

## Files Expected To Change

```txt
packages/modeu5_war_rebalance/in_game/common/scripted_effects/
packages/modeu5_war_rebalance/in_game/common/on_action/
packages/modeu5_war_rebalance/in_game/events/
packages/modeu5_war_rebalance/in_game/localization/
packages/modeu5_war_rebalance/main_menu/common/static_modifiers/
docs/technical/
docs/tests/
```

## Dependencies

```txt
Depends on: CORE-00 package contract and confirmed game-rule/package model
Blocks: none
Related US: US-13, Early Blobbing balance package
```

## Implementation Rules

- Do not add US-19 files to Core.
- Do not create a fake `has_great_power_war` trigger.
- Do not scan all countries from the monthly pulse.
- Maintain `modeu5_has_great_power_war` from war lifecycle hooks.
- Monthly runtime reads the cached state and applies the modifier only for Great Powers.
- Static modifier keys must be confirmed vanilla modifier types.
- Debug output must show the state-machine result and variables used by the probe.

## Business Rules

- Great Powers are countries where `great_power_ranking <= 8`.
- Comfortable peace begins after `months_since_war > 120`.
- Comfortable peace increases complacency by:
  - `+1` base monthly after ten years of peace,
  - `+1` if `monthly_balance > 0`,
  - `+1` if `manpower_percentage > 0.85`,
  - `+1` if `stability_percentage > 0.75`.
- War against another Great Power reduces complacency by roughly `8.333` monthly,
  plus up to `3` additional pressure from army tradition gains, manpower stress,
  and war exhaustion.
- If the country has not lost a Great Power war for 100 years
  (`modeu5_months_since_gp_loss >= 1200`), complacency has a floor of `100` and
  Great-Power-war recovery is slower.
- Losing a war against another Great Power resets
  `modeu5_months_since_gp_loss` and applies a one-time myth-breaking reduction.
- Complacency is clamped to `[0, 200]`.

## Acceptance Criteria

- [ ] The Early Blobbing package loads without Core manufacturing its package marker.
- [ ] `event modeu5_us19_debug.1` exposes a deterministic US-19 probe.
- [ ] The probe emits `ModeU5 US-19 DUMP state_machine ...` in `debug.log`.
- [ ] The probe emits `ModeU5 TEST PASS scenario=us19_imperial_complacency`.
- [ ] A Great Power war declaration or join updates `modeu5_has_great_power_war`.
- [ ] A war ending refreshes `modeu5_has_great_power_war` for winner and loser.
- [ ] Losing a Great Power war resets `modeu5_months_since_gp_loss`.
- [ ] Monthly pulse applies `modeu5_imperial_complacency` only to Great Powers.
- [ ] `error.log` has no new blocking ModeU5 script error.
- [ ] TECH-01 documents every vanilla exposure used by the implementation.

## Manual Test Scenario

### Setup

```txt
Packages: No Void Economy + Rebalance Early Blobbing
Country: a Great Power such as a top-8 country in the current start date
Debug command: event modeu5_us19_debug.1
Runtime scenario: Great Power war declaration, joining war, peace, and losing war if practical
```

### Expected Result

```txt
Deterministic probe:
  debug.log contains ModeU5 TEST ENTERED scenario=us19_imperial_complacency
  debug.log contains ModeU5 US-19 DUMP state_machine complacency_after=<150 gp_war_state=1
  debug.log contains ModeU5 TEST PASS scenario=us19_imperial_complacency

Runtime hooks:
  modeu5_has_great_power_war becomes 1 when the country is at war with another Great Power
  modeu5_has_great_power_war returns to 0 when that war ends and no other GP war remains
  modeu5_months_since_gp_loss resets to 0 when a GP loses to another GP
  modeu5_imperial_complacency modifier appears only when complacency is positive
```

## Known Limitations

- EU5 runtime validation has not yet been run on this commit.
- The deterministic probe validates the state-machine and dump output; it does
  not itself force a real diplomatic war.
- Great Power ranking is read from the confirmed `great_power_ranking` trigger.
  If a future EU5 version changes Great Power ranking semantics, TECH-01 and the
  hook filters must be revisited.
- Modifier sign and balance scale are intentionally conservative and must be
  validated in-game. The removed `reform_progress_speed` concept is not used
  because that modifier key is not confirmed.
- Mid-campaign package enable/disable remains unsupported by the module model.

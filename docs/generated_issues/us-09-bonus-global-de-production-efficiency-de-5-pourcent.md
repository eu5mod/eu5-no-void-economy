# US-09 — Production Efficiency de +5 % bonus

Labels: `module:economy`

## User Story

```txt
US-09 — Production Efficiency de +5 % bonus
```

As a player, I want a global +5% Production Efficiency compensation for ModeU5's stock, decay, and production-correction constraints.

## Functional objective

Restore a target `+X%` effective production compensation for the Rebalance Economy package while preserving the stock-aware production chain. The generator-backed static override path is package-shipped only when generated files preserve the exact vanilla relative file path, so EU5 replaces the vanilla definitions instead of loading duplicate keys.

Because US-09, US-07, and US-08/US-05.3 can all edit vanilla
`common/building_types` static files, the US-09 generated Economy override
composes the overlapping changes directly into the exact-path generated files.
This avoids competing package overrides for the same static definitions.

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
Monthly step: static package load before runtime; runtime additive fallback would run at monthly step 3
Depends on: selected static override path and confirmed supporting exposure
Feeds counters to: vanilla production read at step 4
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Production efficiency modifier | country | `global_production_efficiency` | CONFIRMED | 066 |
| Iterate/apply to countries | none → country | `every_country` plus `add_country_modifier` | CONFIRMED | 001, 009 |
| Monthly invocation at runtime step 3 | country | `monthly_country_pulse` → shared ModeU5 monthly dispatcher | CONFIRMED | 011 |
| Transformation compatibility | ModeU5 production chain | apply before production read; preserve stock-add contract | CONFIRMED | internal |
| Static production output field | local vanilla `common/building_types` | `output = <float>` inside production definitions; loaded duplicate-key override path | NOT_CONFIRMED | 118 |
| Static merchant-capacity fields | local vanilla `common/building_types` | `local_merchant_capacity`, `merchant_capacity_from_building`; exact-path package override path. `local_trades_per_burgher` is intentionally left unchanged. | TO_TEST | 118 |
| Composed US-07 trade-building estate-power field | local vanilla `common/building_types/trade_buildings.txt` | `local_burghers_estate_power x 0.5`; exact-path package override path | TO_TEST | 083 |
| Composed US-08/US-05.3 building maintenance quantities | local vanilla `common/building_types` | goods inside `category = building_maintenance` blocks multiplied by `0.7`, or `0.5` for enclosing `trade_category` buildings; exact-path package override path | CONFIRMED | 153 |
| Static RGO expansion price entries | local vanilla `common/prices/00_hardcoded.txt` | `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, `expand_rgo_forestry`; loaded duplicate-key override path | NOT_CONFIRMED | 119 |

## Probe implementation path

Probe solution:

```txt
Generate exact-path override files from vanilla `.../game/in_game/common/building_types`
Increase each eligible `output =` value by configurable `X%`.
Increase each eligible `local_merchant_capacity` and `merchant_capacity_from_building` value by `MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT` when configured, otherwise by the same `X%`. `local_trades_per_burgher` is intentionally not increased by US-09.
Compose the overlapping US-07 `trade_buildings.txt` `local_burghers_estate_power` reduction as `value x 0.5`
Compose US-08/US-05.3 building maintenance by multiplying every good quantity inside a `category = building_maintenance` method by `0.7`, except maintenance inside enclosing `trade_category` buildings which uses `0.5`
Generate an exact-path `common/prices/00_hardcoded.txt` override for the five `expand_rgo_*` entries
Override each targeted RGO expansion gold value by `gold x (1 / (1 + X))`
```

Rationale:

```txt
This path changes source output and trade-capacity-like static fields directly when the Economy package is loaded.
Trade-capacity compensation is independently configurable so local tests can use, for example, output/RGO `+10%` with trade capacity `+15%`.
It also carries the approved US-07 marketplace estate-power reduction for the same exact-path trade-building file.
It therefore scales correctly with downstream national or technological production modifiers.
It matches the intended compensation logic better than a flat additive `global_production_efficiency = +5%`, but it is not currently runtime-safe.
```

Constraints:

```txt
Do not edit installed vanilla files in place.
Use vanilla files only as scaffolding input.
Generated override files that are shipped in the loaded ModeU5 Economy package must keep the exact vanilla relative path and filename.
Keep the compensation rate configurable in the generator, not hand-edited across overrides.
```

### Option matrix

1. Preferred: generate exact-path `common/building_types` output/trade-capacity overrides with configurable `X%`, compose the overlapping US-07 `trade_buildings.txt` `local_burghers_estate_power x 0.5` reduction, plus exact-path `common/prices/00_hardcoded.txt` overrides for `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, and `expand_rgo_forestry` with the matching `gold x (1 / (1 + X))` formula.

   Status: implemented as package-shipped exact-path overrides. Non-vanilla filenames such as `expand_rgo_prices.txt` or `zzzz_cbp_us09_*` are rejected because they load duplicate keys instead of replacing vanilla definitions.

2. Country-level additive-modifier path: read current `global_production_efficiency` and `global_<good>_production_modifier`, then increase them by `5%`.

   Status: blocked on confirmed read exposure and exact runtime semantics

3. Local-level additive-modifier path: same as option 2, but applied closer to the production source.

   Status: blocked on confirmed local read/apply exposure and likely higher maintenance

4. Ignore the issue and accept the current lower effective production baseline under ModeU5 constraints.

   Status: fallback only if all supported compensation paths are rejected

5. Other targeted implementation paths may be added during the probe, but each new option must state its balance model, exposed hook/value requirements, and maintenance cost.

### Why option 2 is not currently preferred

An additive `global_production_efficiency = +5%` path may underdeliver if production efficiency participates in an additive modifier stack.

Worked example:

```txt
Base production = 100
Existing production modifiers = +50%
Current multiplier = 1.50
After adding +5% production efficiency = 1.55
Final output = 150 -> 155
Effective gain = +3.33%, not +5%
```

This is acceptable only if design explicitly accepts approximate compensation. The currently preferred balance model remains the scaffolded-source solution, but the runtime replacement endpoint is not confirmed.

## Files expected to change

```txt
tools/generated/us09_economy_overrides/common/building_types/
tools/generated/us09_economy_overrides/common/prices/
tools/
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
- Follow `docs/technical/MODULE_OPTION_MODEL.md`; do not load or retain these overrides when the Rebalance Economy package is absent.
- Treat exact-path generated package overrides as the only approved loaded static-override shape; non-vanilla filenames remain rejected because they create duplicate keys.
- Do not edit files under the installed vanilla game directory; read them only as scaffolding input.
- Generated candidate overrides that are loaded by the package must use the same relative file path as the vanilla source file.
- Keep the compensation percentage configurable in one generation path; do not hand-edit hundreds of output values.
- Do not switch to the additive-modifier options unless their read semantics are confirmed and documented in TECH-01.
- Apply the compensation before monthly production is read.
- Keep it distinct from national/technology bonuses.
- Do not use this issue to redesign transformation formulas beyond compatibility; the generated path is limited to approved composed static candidates for `building_types` output/trade fields, building-maintenance quantities, and the five `expand_rgo_*` entries in `common/prices/00_hardcoded.txt`.
- Use the confirmed shared `monthly_country_pulse` dispatcher; do not register a second monthly mechanism.

## US-specific boundary checks

- [ ] The compensation is not a hidden replacement for US-00 penalties.
- [ ] Stock mutation remains centralized.
- [ ] Vanilla install files are never modified in place.

## Acceptance criteria

- [ ] Generated package files increase every targeted `output =` value by the configured `X%`.
- [ ] Generated package files increase every targeted `local_merchant_capacity` and `merchant_capacity_from_building` value by the configured trade-capacity percent, falling back to `X%` when no independent value is configured, while leaving `local_trades_per_burgher` unchanged.
- [ ] The generated exact-path `trade_buildings.txt` file composes the approved US-07 `local_burghers_estate_power x 0.5` reduction without changing `local_merchant_power`.
- [ ] Generated package files divide every building-maintenance good quantity by exactly `2`.
- [ ] Generated package files scale `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, and `expand_rgo_forestry` by `gold x (1 / (1 + X))`.
- [ ] The generator is idempotent and removes stale non-vanilla override filenames that would create duplicate keys.
- [ ] Runtime logs show no duplicate-key errors for the generated exact-path static overrides.
- [ ] No installed vanilla file is edited in place.

## Manual test scenario

### Setup

```txt
Review the selected implementation path against a few representative vanilla production building files
Check whether the compensation acts on source output or only on additive country modifiers
Check whether the paired `expand_rgo_*` overrides cleanly support the `gold x (1 / (1 + X))` formula
```

### Expected result

```txt
The generated probe building files apply the configured source-output increase
The generated probe RGO expansion price file applies the inverse gold scaling to the five `expand_rgo_*` entries
The additive-modifier alternatives remain visible but unselected
```

## Known limitations

The current implementation ships paired static overrides in the Economy package using exact vanilla relative file paths.
The generated building candidate surface includes files that use the approved US-09 fields or contain building-maintenance methods.
The US-07 composition is intentionally limited to `trade_buildings.txt` `local_burghers_estate_power`; `local_merchant_power` remains vanilla until a concrete US-07 target value is approved.
The US-08/US-05.3 maintenance composition is intentionally limited to goods inside explicit `category = building_maintenance` blocks.
Runtime load tests showed non-vanilla package-local filenames are rejected or noisy because they create duplicate keys, so stale names such as `common/prices/expand_rgo_prices.txt` must remain absent.
The exact `global_production_efficiency` modifier, country modifier effect, and `monthly_country_pulse` exposure are documented for a possible runtime additive path, but that path remains unselected until read/runtime stacking semantics are confirmed and explicitly approved.

# Edit : Additional RGO size fixe
Apply a first 10% Max RGO Size base formula component without using additive percentage modifiers.

## User Story

As a mod maintainer,I want to increase the effective Max RGO Size contribution from base, population, and development by 10%,so that the balance change behaves as a true pre-modifier increase and is not diluted by EU5 additive percentage modifier stacking.

## Context

The current Max RGO Size formula includes a pre-modifier component equivalent to:

base + population_contribution + development_contribution

where:

base = 2
population_contribution = population * 0.00025
development_contribution = development * 0.1

A simple modifier such as:

global_max_rgo_size_modifier = 0.10

is not acceptable because EU5 percentage modifiers are additive with existing modifiers. This means the effective increase may be lower than 10% when other Max RGO Size modifiers already apply.

The desired implementation should therefore avoid the additive percentage modifier bucket.

## Target Formula

The desired bonus is:

10% * (base + population_contribution + development_contribution)

which expands to:

0.2 + population * 0.000025 + development * 0.01

Technical Strategy

The implementation should use scaffolding wherever possible.

Current implemented layer:

```txt
cbp_us09_base_rgo_size_10_percent_bonus
  local_max_rgo_size = 1
```

The Economy package applies this static location modifier with a computed `size`.
Initial campaign/load backfill uses `cbp_apply_us09_base_rgo_size_bonus`, then the
monthly country pulse refreshes owned locations through
`cbp_refresh_us09_base_rgo_size_bonus_for_current_country`.

The display-equivalent source formula is:

```txt
200 + location population * 0.025
```

The applied bonus remains the approved 10% increase and is stored in normalized
`local_max_rgo_size`/PopCaps units:

```txt
0.2 + population * 0.000025
```

The modifier is applied with `mode = replace`, so monthly refreshes revalue the
same modifier instead of stacking duplicate bonuses.

Deferred scaffold layer:

The development contribution remains deferred:

development * 0.01

The population contribution is now live and refreshed monthly from location
`population`.

The base component is a special case:

base = 2
10% * base = 0.2

Since the base Max RGO Size value is not changed directly through defines, CBP
applies a scalable location modifier whose monthly `size` is recomputed from
the current location population.

## Implementation Requirements

### 1. Current base modifier

Implemented:

```txt
cbp_us09_base_rgo_size_10_percent_bonus = {
    game_data = {
        category = location
    }

    local_max_rgo_size = 1
}
```

### 2. Current base application

Implemented:

```txt
every_location_in_the_world = {
    cbp_refresh_us09_base_rgo_size_bonus_for_current_location = yes
}
```

Monthly owned-location refresh:

```txt
every_owned_location = {
    cbp_refresh_us09_base_rgo_size_bonus_for_current_location = yes
}

cbp_refresh_us09_base_rgo_size_bonus_for_current_location = {
    save_temporary_scope_value_as = {
        name = cbp_us09_base_rgo_size_bonus_modifier_size
        value = {
            value = population
            multiply = 0.000025
            add = 0.2
            min = 0.2
        }
    }

    add_location_modifier = {
        modifier = cbp_us09_base_rgo_size_10_percent_bonus
        years = -1
        mode = replace
        size = scope:cbp_us09_base_rgo_size_bonus_modifier_size
        recalculate_immediately = yes
    }
}
```

### 3. Deferred development contribution

The remaining unimplemented part of the target formula is:

```txt
development * 0.01
```

That contribution still needs either a confirmed dynamic `development` monthly
refresh path or a deterministic generated setup source. It is intentionally not
folded into this monthly population refresh.

## Acceptance Criteria

The implementation does not use global_max_rgo_size_modifier = 0.10 as the main balance mechanism.

The implementation does not rely on additive percentage Max RGO Size modifiers.

The current PR applies the base and population contribution through the scalable
`cbp_us09_base_rgo_size_10_percent_bonus` location modifier.

The population contribution is refreshed monthly from current location
`population`; the development contribution remains deferred.

The minimum base contribution adds exactly 0.2 Max RGO Size per eligible
location.

The modifier is applied with `mode = replace`; monthly refreshes must not stack
additional copies of the bonus.

The base modifier and application effect are deterministic and reproducible.

Generated files do not require manual editing.

The generated/static output is compatible with the existing package installation pipeline.

The implementation can be validated by checking that the Economy package applies `cbp_us09_base_rgo_size_10_percent_bonus` through `every_location_in_the_world` at campaign start and that runtime logs do not report an invalid modifier or effect.

## Validation Scenario

Given a location with:

base = 2
population = 40,000
development = 10

The original pre-modifier component is:

2 + 40,000 * 0.00025 + 10 * 0.1
= 2 + 10 + 1
= 13

The expected 10% bonus is:

13 * 0.10 = 1.3

The scaffolded/generated flat bonus should therefore be:

base_bonus + population_bonus + development_bonus
= 0.2 + 40,000 * 0.000025 + 10 * 0.01
= 0.2 + 1 + 0.1
= 1.3

## Non-Goals

Do not change RGO output.

Do not change RGO construction time.

Do not change AI RGO expansion priority.

Do not use percentage Max RGO Size modifiers for this feature.

Do not require dynamic recalculation every month.

Do not attempt to perfectly track population changes after game start unless a later feature explicitly requires it.

## Technical Notes

This approach intentionally favors scaffolded static values over runtime script calculations.

The expected advantages are:

better game performance;

deterministic generated data;

easier validation;

no dilution from additive percentage modifier stacking;

compatibility with existing generated package workflows.

Population-based values are based on starting population. This means the population component is accurate at game start but will not dynamically follow population growth or decline unless a future recalculation system is added.

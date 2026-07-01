# US-09 — Production Efficiency de +5 % bonus

Labels: `module:economy`

## User Story

```txt
US-09 — Production Efficiency de +5 % bonus
```

As a player, I want a global +5% Production Efficiency compensation for ModeU5's stock, decay, and production-correction constraints.

## Functional objective

Restore a target `+X%` effective production compensation for the Rebalance Economy package while preserving the stock-aware production chain. The generator-backed static override path is currently probe-only until EU5 static replacement semantics are confirmed.

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
| Static RGO expansion price entries | local vanilla `common/prices/00_hardcoded.txt` | `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, `expand_rgo_forestry`; loaded duplicate-key override path | NOT_CONFIRMED | 119 |

## Probe implementation path

Probe solution:

```txt
Scaffold candidate override files from vanilla `.../game/in_game/common/building_types`
Increase each eligible `output =` value by a configurable `X%`
Scaffold candidate `common/prices/00_hardcoded.txt` overrides for the five `expand_rgo_*` entries
Override each targeted RGO expansion gold value by `gold x (1 / (1 + X))`
```

Rationale:

```txt
This path would change source output directly if a valid package replacement surface is confirmed.
It would therefore scale correctly with downstream national or technological production modifiers.
It matches the intended compensation logic better than a flat additive `global_production_efficiency = +5%`, but it is not currently runtime-safe.
```

Constraints:

```txt
Do not edit installed vanilla files in place.
Use vanilla files only as scaffolding input.
Keep scaffolded files outside the loaded ModeU5 Economy package until clean duplicate-key-free loading is confirmed.
Keep the compensation rate configurable in the generator, not hand-edited across overrides.
```

### Option matrix

1. Preferred: scaffold `common/building_types` output overrides with configurable `X%` plus scaffold `common/prices/00_hardcoded.txt` overrides for `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, and `expand_rgo_forestry` with the matching `gold x (1 / (1 + X))` formula.

   Status: probe-only. Runtime loading of generated duplicate-key package files produced errors, so the files are no longer shipped in the loaded Economy package.

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
- Treat the scaffolded static-override path as a probe until a future branch confirms a clean replacement mechanism.
- Do not edit files under the installed vanilla game directory; read them only as scaffolding input.
- Generated candidate overrides must stay outside the loaded package unless a branch is explicitly probing static replacement behavior.
- Keep the compensation percentage configurable in one generation path; do not hand-edit hundreds of output values.
- Do not switch to the additive-modifier options unless their read semantics are confirmed and documented in TECH-01.
- Apply the compensation before monthly production is read.
- Keep it distinct from national/technology bonuses.
- Do not use this issue to redesign transformation formulas beyond compatibility; the probe path is limited to paired static candidates for `building_types` `output =` values and the five `expand_rgo_*` entries in `common/prices/00_hardcoded.txt`.
- Use the confirmed shared `monthly_country_pulse` dispatcher; do not register a second monthly mechanism.

## US-specific boundary checks

- [ ] The compensation is not a hidden replacement for US-00 penalties.
- [ ] Stock mutation remains centralized.
- [ ] Vanilla install files are never modified in place.

## Acceptance criteria

- [ ] Generated probe files increase every targeted `output =` value by the configured `X%`.
- [ ] Generated probe files scale `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, and `expand_rgo_forestry` by `gold x (1 / (1 + X))`.
- [ ] The generator is idempotent and keeps candidate overrides outside the loaded Economy package by default.
- [ ] A clean runtime replacement mechanism is confirmed before generated static candidates are shipped.
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

The current implementation keeps the paired static scaffold path as an offline probe only.
The generated building candidate surface may include event-only or uncommon production files whenever they use the same `output =` production field.
Runtime load tests showed duplicate-key package-local scaffolds are rejected or noisy, so US-09 gameplay compensation remains unimplemented until the correct replacement endpoint is confirmed.
The exact `global_production_efficiency` modifier, country modifier effect, and `monthly_country_pulse` exposure are documented for a possible runtime additive path, but that path remains unselected until read/runtime stacking semantics are confirmed and explicitly approved.

# Edit : Additional RGO size fixe
Scaffold a 10% increase of the Max RGO Size base formula component without using additive percentage modifiers.

## User Story

As a mod maintainer,I want to increase the effective Max RGO Size contribution from base, population, and development by 10%,so that the balance change behaves as a true pre-modifier increase and is not diluted by EU5 additive percentage modifier stacking.

## Context

The current Max RGO Size formula includes a pre-modifier component equivalent to:

base + population_contribution + development_contribution

where:

base = 2
population_contribution = population * 0.000025
development_contribution = development * 0.1

A simple modifier such as:

global_max_rgo_size_modifier = 0.10

is not acceptable because EU5 percentage modifiers are additive with existing modifiers. This means the effective increase may be lower than 10% when other Max RGO Size modifiers already apply.

The desired implementation should therefore avoid the additive percentage modifier bucket.

## Target Formula

The desired bonus is:

10% * (base + population_contribution + development_contribution)

which expands to:

0.2 + population * 0.0000025 + development * 0.01

Technical Strategy

The implementation should use scaffolding wherever possible.

The scaffold should generate flat local_max_rgo_size modifiers for the variable parts of the formula:

population * 0.0000025
development * 0.01

The generated values should be based on the source map/setup data used by the mod scaffolding pipeline.

The base component is a special case:

base = 2
10% * base = 0.2

If the base Max RGO Size value cannot be changed directly through scaffolding or defines, then a fallback script must apply a flat local_max_rgo_size = 0.2 modifier to every eligible location at game start.

## Implementation Requirements

### 1. Scaffold generated location modifiers

For each eligible location, generate a static flat modifier representing:

population_bonus + development_bonus

where:

population_bonus = starting_population * 0.0000025
development_bonus = starting_development * 0.01

Example:

nve_location_123_rgo_size_scaffold_bonus = {
    game_data = {
        category = location
    }

    local_max_rgo_size = 0.1375
}

### 2. Apply scaffolded modifiers to locations

Each generated modifier must be applied to its matching location through generated setup script.

Example:

123 = {
    add_location_modifier = {
        modifier = nve_location_123_rgo_size_scaffold_bonus
        days = -1
        mode = replace
        recalculate_immediately = yes
    }
}

### 3. Add fallback base modifier

Create a generic static modifier for the fixed base component:

nve_rgo_base_size_10_percent_bonus = {
    game_data = {
        category = location
    }

    local_max_rgo_size = 0.2
}

4. Apply base modifier at game start

If the base RGO size cannot be changed directly through defines or generated location setup, apply the base modifier to all eligible locations at game start:

every_location = {
    add_location_modifier = {
        modifier = nve_rgo_base_size_10_percent_bonus
        days = -1
        mode = replace
        recalculate_immediately = yes
    }
}

If the final implementation supports fully scaffolded per-location application, the generated per-location modifier may instead include the 0.2 base component directly:

local_max_rgo_size = 0.2 + population_bonus + development_bonus

In that case, the game-start fallback modifier is not needed.

## Acceptance Criteria

The implementation does not use global_max_rgo_size_modifier = 0.10 as the main balance mechanism.

The implementation does not rely on additive percentage Max RGO Size modifiers.

The scaffold generates flat local_max_rgo_size values for population and development contributions.

The fixed base contribution adds exactly 0.2 Max RGO Size per eligible location.

If the base value cannot be changed through scaffolding or defines, the 0.2 base contribution is applied once at game start.

Generated modifiers are deterministic and reproducible.

Generated files do not require manual editing.

The generated output is compatible with the existing mod generation pipeline.

The implementation can be validated on at least one rural and one non-rural location.

## Validation Scenario

Given a location with:

base = 2
population = 40,000
development = 10

The original pre-modifier component is:

2 + 40,000 * 0.000025 + 10 * 0.1
= 2 + 1 + 1
= 4

The expected 10% bonus is:

4 * 0.10 = 0.4

The scaffolded/generated flat bonus should therefore be:

base_bonus + population_bonus + development_bonus
= 0.2 + 40,000 * 0.0000025 + 10 * 0.01
= 0.2 + 0.1 + 0.1
= 0.4

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

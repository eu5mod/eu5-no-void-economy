# US-09 — Production Efficiency de +5 % bonus

Labels: `module:economy`

## User Story

```txt
US-09 — Production Efficiency de +5 % bonus
```

As a player, I want a global +5% Production Efficiency compensation for ModeU5's stock, decay, and production-correction constraints.

## Functional objective

Restore a target `+X%` effective production compensation for the Rebalance
Economy package while preserving the stock-aware production chain. The
generator chooses the source ownership mode from the requested result:

- complete exact-path Vanilla source files for structural changes such as
  production output or maintenance;
- sparse `INJECT:<building>` objects containing `target - Vanilla` when the
  source has proven additive modifier fields only.

Complete `REPLACE:<building>` objects were rejected after runtime showed
duplicate nested production-method registrations. Nested production-method
containers never receive a `REPLACE:` or `INJECT:` prefix.

Because US-09, US-07, and US-08/US-05.3 can all edit vanilla
`common/building_types` static objects, the generated Economy override composes
all changes for one source before choosing its materialization mode. If any
rule requires structural replacement, every change is folded into that one
complete exact-path source. Otherwise, additive modifier changes share sparse
injections.

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
| Static production output field | local Vanilla `common/building_types` | prefixed `cbp_us09_*` alternative inside a sparse `INJECT:<building>`; same Vanilla inputs/category and multiplied `output` | CONFIRMED_STATIC / TO_TEST_RUNTIME | 118 |
| Static merchant-capacity fields | local Vanilla `common/building_types` | `local_merchant_capacity`, `merchant_capacity_from_building`; sparse additive `INJECT:<building>` delta unless another rule makes the building structural. `local_trades_per_burgher` is intentionally left unchanged. | CONFIRMED_STATIC / TO_TEST_RUNTIME | 118 |
| Composed US-07 trade-building estate-power field | local Vanilla `common/building_types/trade_buildings.txt` | `local_burghers_estate_power x 0.5`; additive delta in `INJECT` or composed target value in an exact-path structural source | CONFIRMED_STATIC / TO_TEST_RUNTIME | 083 |
| Composed US-08/US-05.3 building maintenance quantities | local Vanilla `common/building_types` | goods inside `category = building_maintenance` blocks multiplied by their configured ordinary or trade-building multiplier; complete exact-path source | CONFIRMED_STATIC / TO_TEST_RUNTIME | 153 |
| Static RGO expansion price entries | local Vanilla `common/prices/00_hardcoded.txt` | selected `REPLACE:expand_rgo_*` entries for mining, farming, hunting, gathering, and forestry | CONFIRMED_STATIC / TO_TEST_RUNTIME | 119 |

## Probe implementation path

Probe solution:

```txt
Generate complete exact-path sources for mandatory non-additive changes and CBP-prefixed sparse `INJECT:<building>` objects for additive fields and production alternatives.
Clone each eligible productive method as a `cbp_us09_*` alternative whose `output` is increased by configurable `X%`; retain the Vanilla method as an accepted competing option.
Mirror each Vanilla advance `unlock_production_method` for the corresponding CBP alternative.
Increase each eligible `local_merchant_capacity` and `merchant_capacity_from_building` value by `MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT` when configured, otherwise by the independent default `15%`. `local_trades_per_burgher` is intentionally not increased by US-09.
Compose the overlapping US-07 `trade_buildings.txt` `local_burghers_estate_power` reduction as `value x 0.5`
Compose US-08/US-05.3 building maintenance by multiplying every good quantity inside a `category = building_maintenance` method by `0.7`, except maintenance inside enclosing `trade_category` buildings which uses `0.5`
Generate `common/prices/cbp_00_hardcoded.txt` with `REPLACE:` entries for the five `expand_rgo_*` objects
Override each targeted RGO expansion gold value by `gold x (1 / (1 + P))`, where `P` is the independent `MODEU5_US09_RGO_PRICE_OFFSET_PERCENT` configuration.
```

Rationale:

```txt
This path adds improved production-method alternatives and changes trade-capacity-like static fields directly when the Economy package is loaded.
Production, RGO expansion-price compensation, and trade-capacity compensation are independently configurable. Local tests can use, for example, production `+8%`, RGO price offset `8%`, and trade capacity `+15%` without coupling those policies.
It also carries the approved US-07 marketplace estate-power reduction in the same composed building entry.
It therefore scales correctly with downstream national or technological production modifiers.
It matches the intended compensation logic better than a flat additive `global_production_efficiency = +5%`; runtime validation remains required.
```

Constraints:

```txt
Do not edit installed vanilla files in place.
Use vanilla files only as scaffolding input.
Generated additive/alternative building outputs use CBP-prefixed filenames.
Structural outputs preserve the complete Vanilla source file.
Modifier entries contain only additive deltas calculated as target minus Vanilla.
Production entries contain only new `cbp_us09_*` method names and never redeclare a Vanilla method.
Production alternatives inherit the timing of every explicit Vanilla advance unlock.
A source may emit both an exact-path structural file and a non-overlapping injection file.
Keep the compensation rate configurable in the generator, not hand-edited across overrides.
```

### Option matrix

1. Preferred: compose all requested changes per source, emit a complete
   exact-path source for mandatory non-additive changes and sparse
   `INJECT:<building>` deltas/prefixed production alternatives, plus selected
   `REPLACE:` price objects for the five `expand_rgo_*` entries.

   Status: implemented as package-shipped hybrid outputs.

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
- Use the hybrid building contract in
  `docs/technical/BUILDING_OVERRIDE_GENERATION.md`: mandatory non-additive
  changes require complete exact-path sources; additive fields and uniquely
  prefixed production alternatives use sparse `INJECT` entries.
- Do not edit files under the installed vanilla game directory; read them only as scaffolding input.
- Do not generate complete `REPLACE:<building>` objects for structural
  mutations or prefix nested production-method containers.
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

- [ ] Generated package files add one uniquely prefixed alternative for every targeted productive method, preserving its Vanilla inputs/category and increasing its `output` by configured `X%`.
- [ ] Every explicit Vanilla advance unlock for a targeted method also unlocks its CBP alternative; no advanced method becomes available early.
- [ ] Generated package files increase every targeted `local_merchant_capacity` and `merchant_capacity_from_building` value by the configured trade-capacity percent, falling back to the independent default `15%` when no value is configured, while leaving `local_trades_per_burgher` unchanged.
- [ ] Generated `trade_buildings.txt` composes the approved US-07 `local_burghers_estate_power x 0.5` reduction without changing `local_merchant_power`.
- [ ] Generated package files apply the configured ordinary or trade-building
  maintenance multiplier to every covered maintenance-good quantity.
- [ ] Generated package files scale `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, and `expand_rgo_forestry` by `gold x (1 / (1 + X))`.
- [ ] The generator is idempotent and removes stale non-vanilla override filenames that would create duplicate keys.
- [ ] Runtime logs show no duplicate building keys, duplicated production methods, or unexpected tokens from generated building files.
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

The current implementation ships exact-path structural sources and
CBP-prefixed additive `INJECT` outputs in the Economy package. Exact-path
sources necessarily retain unchanged buildings from that Vanilla source.
The US-07 composition is intentionally limited to `trade_buildings.txt`
`local_burghers_estate_power`; `local_merchant_power` remains Vanilla until a
concrete US-07 target value is approved.
The US-08/US-05.3 maintenance composition is intentionally limited to goods
inside explicit `category = building_maintenance` blocks.
Selected flat database entries such as RGO prices still use explicit
`REPLACE:` declarations in CBP-prefixed files; that does not establish the
same semantics for nested building production-method registries.
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

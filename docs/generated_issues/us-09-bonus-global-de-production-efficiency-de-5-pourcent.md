# US-09 — Production Efficiency de +5 % bonus

Labels: `module:economy`

## User Story

```txt
US-09 — Production Efficiency de +5 % bonus
```

As a player, I want a global +5% Production Efficiency compensation for ModeU5's stock, decay, and production-correction constraints.

## Functional objective

Restore a target `+X%` effective production compensation for the Rebalance Economy package while preserving the stock-aware production chain. The selected implementation path is a generator-backed static override package for production outputs and paired RGO expansion prices.

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
| Static production output field | local vanilla `common/building_types` | `output = <float>` inside production definitions | CONFIRMED | 118 |
| Static RGO expansion price entries | local vanilla `common/prices/00_hardcoded.txt` | `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, `expand_rgo_forestry` | CONFIRMED | 119 |

## Selected implementation path

Preferred solution:

```txt
Scaffold override files from vanilla `.../game/in_game/common/building_types`
Increase each eligible `output =` value by a configurable `X%`
Scaffold `common/prices/00_hardcoded.txt` overrides for the five `expand_rgo_*` entries
Override each targeted RGO expansion gold value by `gold x (1 / (1 + X))`
```

Rationale:

```txt
This path changes source output directly.
It therefore scales correctly with downstream national or technological production modifiers.
It matches the intended compensation logic better than a flat additive `global_production_efficiency = +5%`.
```

Constraints:

```txt
Do not edit installed vanilla files in place.
Use vanilla files only as scaffolding input.
Emit static override files inside the ModeU5 Economy package.
Keep the compensation rate configurable in the generator, not hand-edited across overrides.
```

### Option matrix

1. Preferred: scaffold `common/building_types` output overrides with configurable `X%` plus scaffold `common/prices/00_hardcoded.txt` overrides for `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, and `expand_rgo_forestry` with the matching `gold x (1 / (1 + X))` formula.

   Status: selected and scaffolded in this branch

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

This is acceptable only if design explicitly accepts approximate compensation. The selected implementation path in this branch is the scaffolded-source solution instead.

## Files expected to change

```txt
packages/modeu5_economy_rebalance/in_game/common/building_types/
packages/modeu5_economy_rebalance/in_game/common/prices/
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
- Treat the scaffolded static-override path as the selected implementation until a future branch explicitly replaces it.
- Do not edit files under the installed vanilla game directory; read them only as scaffolding input.
- If a generator is introduced, generated overrides must live in `packages/modeu5_economy_rebalance/`.
- Keep the compensation percentage configurable in one generation path; do not hand-edit hundreds of output values.
- Do not switch to the additive-modifier options unless their read semantics are confirmed and documented in TECH-01.
- Apply the compensation before monthly production is read.
- Keep it distinct from national/technology bonuses.
- Do not use this issue to redesign transformation formulas beyond compatibility; the preferred implementation path is limited to paired static overrides for `building_types` `output =` values and the five `expand_rgo_*` entries in `common/prices/00_hardcoded.txt`.
- Use the confirmed shared `monthly_country_pulse` dispatcher; do not register a second monthly mechanism.

## US-specific boundary checks

- [ ] The compensation is not a hidden replacement for US-00 penalties.
- [ ] Stock mutation remains centralized.
- [ ] Vanilla install files are never modified in place.

## Acceptance criteria

- [ ] Generated package overrides increase every targeted `output =` value by the configured `X%`.
- [ ] Generated package overrides scale `expand_rgo_mining`, `expand_rgo_farming`, `expand_rgo_hunting`, `expand_rgo_gathering`, and `expand_rgo_forestry` by `gold x (1 / (1 + X))`.
- [ ] The generator is idempotent and keeps all overrides inside the Economy package.
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
The generated building override files apply the configured source-output increase
The generated RGO expansion price override file applies the inverse gold scaling to the five `expand_rgo_*` entries
The additive-modifier alternatives remain visible but unselected
```

## Known limitations

The current implementation uses the paired static scaffold path described above.
The generated building override surface may include event-only or uncommon production files whenever they use the same `output =` production field.
The exact `global_production_efficiency` modifier, country modifier effect, and `monthly_country_pulse` exposure are documented for a possible runtime additive path, but that path remains unselected until read/runtime stacking semantics are confirmed and explicitly approved.

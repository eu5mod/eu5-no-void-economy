# Building Override Generation

CBP keeps EU5-compatible exact-path building files, but plans their contents at
top-level-building granularity.

## Source Of Truth

`tools/transform_cbp_economy_building_overrides.py` is the only applicability
and transformation engine for building overrides. The shell orchestrator must
not maintain a second regex or field list deciding which vanilla files apply.

For every vanilla `building_types` file, the transformer:

1. parses top-level buildings and fails closed on an ambiguous structure;
2. calculates all registered field and structural changes;
3. skips the file when the change plan is empty;
4. preserves unrelated building content;
5. emits the exact-path override and a deterministic JSON manifest.

The generator stages every building output before publishing it. A parse or
transformation failure leaves the existing package outputs untouched.

## Manifest Contract

Distribution manifests live under:

```txt
packages/cbp_economy_rebalance/cbp_generated/us09_buildings/
```

Each manifest records source and generated SHA-256 fingerprints, changed and
unchanged building counts, and every changed field or structural action with
its old and new value. A generated building file without a matching manifest,
an undeclared change, or a stale manifest is a validation failure.

## Registered Transformations

The current registry covers:

- US-09 production output and merchant-capacity scaling;
- US-07 trade-building Burgher estate-power scaling;
- US-08 ordinary and trade-building maintenance scaling;
- marketplace-chain maintenance alignment;
- disabling `maximum_stockpile_capacity` assignments;
- disabling `market_warehouse` through explicit potential blocks;
- US-177 building `minting_income_factor` scaling.

New building transformations must be added to this engine and its manifest
plan. Do not add a prefilter or an unregistered post-generation mutation.

## Local Balance Inputs

Local regeneration reads both maintenance multipliers from `.cbp.local.env`:

```txt
MODEU5_US08_BUILDING_MAINTENANCE_MULTIPLIER=0.7
MODEU5_US08_TRADE_BUILDING_MAINTENANCE_MULTIPLIER=0.5
```

The first applies to non-trade buildings and the second to trade buildings.
`.cbp.local.env.template` defines the committed configuration names and
defaults.

## Validation

```bash
python3 -m unittest tools.tests.test_building_override_transformer
./tools/generate_all.sh
./tools/validate_module_packages.sh
```

CI fixtures cover empty applicability, numeric and maintenance changes,
structural-only changes, unchanged-building preservation, deterministic output,
stockpile removal, and fail-closed parsing.

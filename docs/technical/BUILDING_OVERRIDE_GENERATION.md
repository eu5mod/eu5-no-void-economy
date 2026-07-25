# Building Override Generation

CBP publishes two kinds of CBP-prefixed building files:

- complete `REPLACE:<building>` entries for structural mutations;
- sparse `INJECT:<building>` entries for proven additive modifier deltas.

Each changed top-level building is emitted once in exactly one of those modes.
Unchanged buildings are left to Vanilla and are not redeclared.

The earlier exact-path full-file packaging was unsafe: EU5 loaded those files
beside Vanilla and reported duplicate building and nested production-method
registrations. EU5 database-entry modes avoid that file-level collision, but
the correct mode depends on the requested result. `REPLACE` substitutes the
whole building. `INJECT` adds content to the existing building; modifier values
therefore compose with Vanilla and must be emitted as `target - vanilla`, not
as the absolute target.

## Source Of Truth

`tools/transform_cbp_economy_building_overrides.py` is the only applicability
and transformation engine for building overrides. The shell orchestrator must
not maintain a second regex or field list deciding which vanilla files apply.

For every vanilla `building_types` file, the transformer:

1. parses top-level buildings and fails closed on an ambiguous structure;
2. calculates all registered field and structural changes;
3. skips the file when the change plan is empty;
4. preserves every field inside each changed building unless a registered rule
   modifies it;
5. classifies each changed building by mutation semantics;
6. emits complete structural replacements to `cbp_<source>.txt`;
7. emits additive modifier deltas to `cbp_inject_<source>.txt`;
8. records both output modes in deterministic JSON manifests.

The generator stages every building output before publishing it. A parse or
transformation failure leaves the existing package outputs untouched. Generated
files use a CBP-prefixed source basename, for example
`cbp_market_buildings.txt` and `cbp_inject_market_buildings.txt`.

`REPLACE` remains mandatory when a rule changes `output`, maintenance goods,
availability trigger blocks, or removes a nested entry. Those mutations touch
`unique_production_methods` or replace trigger structure, for which recursive
field replacement is not a proven engine contract.

`INJECT` is used only for modifier blocks whose numeric entries are additive.
The adapter calculates the delta needed to obtain the configured final value.
For example, changing Vanilla `local_merchant_capacity = 5` to `5.75` emits
`local_merchant_capacity = 0.75`. Cancelling a Vanilla
`maximum_stockpile_capacity = 50` emits `-50`.

## Rule Ownership Versus Output Ownership

Business responsibilities remain segregated in the CBG policy:

```txt
production output rule
trade-capacity rule
building-maintenance rule
estate-power rule
stockpile-capacity rule
minting rule
```

The adapter composes every applicable rule before materialization. If any rule
requires structural replacement, all changes for that building are folded into
one complete `REPLACE` object. Otherwise, all modifier deltas are folded into
one sparse `INJECT` object. Do not publish one building copy per business rule.

Database-entry modes operate on the building entry, not on arbitrary scalar
fields inside it. A construct such as `INJECT:brewery = { output = 1.15 }`
does not provide a proven recursive replacement contract for an existing
production-method `output`. Nested `REPLACE:output = ...` syntax is not a
supported production assumption.

## Manifest Contract

Distribution manifests live under:

```txt
packages/cbp_economy_rebalance/cbp_generated/us09_buildings/
```

Each manifest records source and generated SHA-256 fingerprints, changed and
unchanged building counts, and every changed field or structural action with
its old and new value. The CBG manifest records the prefixed output, Vanilla
fingerprint, and `REPLACE` or `INJECT` database-entry mode. A generated building
file without a matching manifest, an undeclared change, a stale manifest, an
exact-path Vanilla copy, a structural mutation rendered as `INJECT`, or an
additive delta rendered as a complete replacement is a validation failure.

## Registered Transformations

The current registry covers:

- US-09 production output and merchant-capacity scaling;
- US-07 trade-building Burgher estate-power scaling;
- US-08 ordinary and trade-building maintenance scaling;
- marketplace-chain maintenance alignment;
- cancelling `maximum_stockpile_capacity` contributions;
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
structural-only changes, additive-delta calculation, unchanged-building
preservation, deterministic output, stockpile cancellation, and fail-closed
parsing.

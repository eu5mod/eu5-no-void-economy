# Building Override Generation

CBP exposes two strategies through `MODEU5_BUILDING_GENERATION_MODE`:

- `override` is the default, proven strategy. Every affected Vanilla source is
  emitted at the same relative path as a complete file with all configured
  transformations already composed.
- `compatibility` minimizes broad file ownership. It emits an exact-path source
  only when a non-additive structural or maintenance mutation requires it, one
  sparse `cbp_<field>_<source>.txt` file per additive modifier family, and one
  sparse `cbp_us09_production_methods_<source>.txt` file for prefixed US-09
  production-method alternatives.

An exact-path file owns the complete Vanilla source path. It contains plain
top-level building keys and plain nested fields. An additive file owns only the
declared deltas and leaves all other Vanilla data loaded.

`REPLACE:<building>` is not used by CBP building generation. Runtime testing
showed that replacing a complete building which reuses Vanilla nested
production-method names leaves duplicate nested registrations and can produce
`Unexpected token` errors. A top-level replacement is not evidence that the
engine recursively replaces every registry inside the building.

## Source Of Truth

`tools/transform_cbp_economy_building_overrides.py` is the applicability and
transformation engine for mandatory maintenance, structure, and additive
building fields. `tools/cbg/adapters/cbp/generate_cbp_cbg_building_spec.py`
composes that plan, discovers productive methods, creates their prefixed
alternatives, mirrors matching advance unlocks, and emits CBG rules. Shell
orchestrators must not maintain a second regex or field list deciding which
Vanilla files apply.

For every Vanilla `building_types` file, the transformer and adapter:

1. parse top-level buildings and fail closed on ambiguous structure;
2. calculate all registered field and structural changes;
3. skip the file when the change plan is empty;
4. preserve every field unless a registered rule modifies it;
5. classify the source by the strongest mutation it contains;
6. in compatibility mode, clone each productive Vanilla inline method as a
   uniquely prefixed `cbp_us09_*` alternative with the configured output
   multiplier;
7. in compatibility mode, mirror every Vanilla `unlock_production_method` that
   targets a cloned method, so the alternative cannot bypass progression;
8. emit a complete exact-path source when a non-additive structural or
   maintenance mutation requires it;
9. in compatibility mode, emit each additive modifier delta to its own
   field-family file and emit prefixed production alternatives separately;
10. record the output mode and source fingerprints in deterministic manifests.

The generator stages every building output before publishing it. A parse or
transformation failure leaves the existing package outputs untouched.
Structural files use the Vanilla source path, for example
`building_types/market_buildings.txt`. Compatibility outputs use CBP-prefixed
basenames, for example
`cbp_local_merchant_capacity_pirate_buildings.txt`.

In compatibility mode, exact-path ownership is mandatory when a rule replaces
maintenance goods, availability trigger blocks, or removes a nested entry.
US-09 output scaling is the deliberate exception: it appends a new
`cbp_us09_*` method under the existing plain `unique_production_methods`
container.

`INJECT` is used only for modifier blocks whose numeric entries are additive.
The adapter calculates the delta needed to obtain the configured final value.
For example, changing Vanilla `local_merchant_capacity = 5` to `5.75` emits
`local_merchant_capacity = 0.75`. Cancelling a Vanilla
`maximum_stockpile_capacity = 50` emits `-50`.

In override mode, `comment_out` removes the active assignment because the
complete generated source replaces the Vanilla source path. In compatibility
mode, a comment inside an INJECT fragment would not remove Vanilla behavior,
so the adapter compiles the same intent into the opposite additive delta.

Each compatibility output has one field-family responsibility. If global and
foreign capacity policies both affect `merchant_capacity_from_building`, the
adapter first composes their final target and then emits one delta. Runtime
file order therefore cannot change the result.

## Two-Dimensional Packaging Model

Building compatibility depends on two independent choices:

1. whether the mod file uses the exact Vanilla relative path or a new custom
   filename;
2. whether the top-level building entry is plain, `REPLACE:`, or `INJECT:`.

The filename and the database-entry directive are not interchangeable.

### File-Path Axis

| File form | Load behavior | Typical use | Compatibility cost |
|---|---|---|---|
| Exact Vanilla relative path and filename | Owns that source-file slot; entries inside remain plain | Change existing nested production methods or remove existing structure | Competes with every mod owning the same Vanilla file |
| New CBP-prefixed/custom filename | Loads beside the Vanilla source | Add new uniquely named objects or apply explicit top-level `INJECT`/`REPLACE` operations | Can coexist when object operations do not conflict |

The inspected M&T package uses both strategies. Eight building files share a
Vanilla basename and contain plain building definitions, including
`production_tools.txt`, where M&T changes inline
`unique_production_methods`. Its files that use `REPLACE:<building>` or
`INJECT:<building>` have custom names such as
`MnT_unique_buildings.txt`, `mnt_building_caps.txt`, and
`epbm_estate_building_maintenance.txt`.

### Entry-Mode Axis

| Top-level form | Meaning used by this project | Safe scope |
|---|---|---|
| `building = { ... }` in an exact-path file | Complete source-file ownership | Existing nested structure, including reused Vanilla method names |
| `cbp_new_building = { ... }` in a custom file | New uniquely named entry | New CBP-owned building only |
| `REPLACE:building = { ... }` in a custom file | Replace the top-level building entry | Only when no reused inline nested registry key can collide |
| `INJECT:building = { ... }` in a custom file | Merge or append content into the existing building | Additive scalar/modifier values or append-only references to new methods |

### Combined Decision Matrix

| File path | Building form | Nested operation | Decision |
|---|---|---|---|
| Exact Vanilla path | Plain complete buildings | Modify existing maintenance, triggers, or removals | Current CBP non-additive strategy |
| Exact Vanilla path | `REPLACE:` or `INJECT:` | Any | Avoid; file ownership already supplies the replacement boundary |
| Custom/prefixed path | Plain existing Vanilla building name | Any | Forbidden; creates a duplicate top-level entry |
| Custom/prefixed path | Plain new CBP building name | New uniquely prefixed nested keys | Supported for genuinely new content after adding an explicit ownership/uniqueness allowlist |
| Custom/prefixed path | `REPLACE:<building>` | Reuse an existing inline Vanilla method key | Rejected by CBP runtime tests |
| Custom/prefixed path | `REPLACE:<building>` | No inline reused key; references existing external methods or defines only new keys | Observed in M&T, but not selected for CBP structural generation |
| Custom/prefixed path | `INJECT:<building>` | Additive scalar or modifier delta | Supported |
| Custom/prefixed path | `INJECT:<building>` | Add a uniquely prefixed method under plain `unique_production_methods` | Supported US-09 alternative-method pattern |
| Custom/prefixed path | `INJECT:<building>` | Plain `possible_production_methods` referencing a new external method | Supported append-only pattern |
| Any path | Any building form | Nested `REPLACE:` or `INJECT:` on a production-method container | Unsupported and forbidden |

Database-entry modes operate on a top-level database entry, not on arbitrary
fields nested inside it. CBP therefore does not generate:

```txt
REPLACE:unique_production_methods = { ... }
INJECT:unique_production_methods = { ... }
REPLACE:production_methods = { ... }
INJECT:production_methods = { ... }
REPLACE:possible_production_methods = { ... }
INJECT:possible_production_methods = { ... }
```

No such nested prefix was found in the inspected M&T `in_game` tree.

## Extra Production Method Pattern

Yes: the observed M&T pattern is **custom/prefixed file + top-level
`INJECT:<building>` + plain method-reference field + extra uniquely named
production method**.

The building-side file contains:

```txt
INJECT:toll_castle = {
    possible_production_methods = { epbm_toll_castle_maintenance }
}
```

A separate custom file under `common/production_methods` contains:

```txt
epbm_toll_castle_maintenance = {
    stone = 0.05
    tools = 0.05
    category = building_maintenance
}
```

M&T uses this form 35 times in the inspected Estate-maintenance file. It is a
strong choice when the business rule is **add a new available method**. It
keeps Vanilla content intact, gives the new method clear ownership, and avoids
copying the full building source.

It is not by itself a replacement for an existing Vanilla method. `INJECT`
appends the new method and leaves Vanilla available. This is acceptable for
US-09 because its business rule explicitly permits a competing improved
production method. It is not acceptable for mandatory maintenance scaling,
where retaining the cheaper Vanilla method would defeat the rule.

## Current CBP Application

| CBP rule | Operation on Vanilla | Selected packaging |
|---|---|---|
| Scale production output | Add a `cbp_us09_*` clone with the same inputs/category and multiplied `output`; retain the Vanilla method | Custom file with `INJECT:<building>` and plain `unique_production_methods` |
| Scale building-maintenance goods | Replace quantities inside existing Vanilla methods | Exact-path source |
| Remove a maintenance good | Remove an existing nested assignment | Exact-path source |
| Disable `market_warehouse` availability | Replace existing trigger structure | Exact-path source |
| Change a modifier value in a source that has no structural mutation | Apply `target - Vanilla` | Custom file with `INJECT:<building>` |
| Add an external production-method slot | Not currently requested | M&T-style building injection plus separately declared prefixed method |

This matches the two observed M&T practices:

- M&T uses same-name files such as `production_tools.txt` when it changes
  existing inline methods.
- M&T uses `epbm_estate_building_maintenance.txt` plus
  `epbm_estate_maintenance_pms.txt` when it adds methods that Vanilla did not
  already provide.

The adapter discovers 214 productive inline methods in the inspected Vanilla
version and emits one uniquely named US-09 alternative for each. Exact-path
ownership is consequently limited to files with maintenance, removal, or
availability changes. Ten of those methods have explicit Vanilla advance
unlocks; CBP mirrors those unlocks through sparse `INJECT:<advance>` entries.
Maintenance is intentionally not migrated to optional alternatives because the
unchanged cheaper method could remain selectable.

## Rule And Output Ownership

Business responsibilities remain segregated in the CBG policy:

```txt
production output rule
trade-capacity rule
building-maintenance rule
estate-power rule
stockpile-capacity rule
minting rule
```

The adapter composes every applicable rule before materialization. Non-additive
changes are folded into one complete exact-path file. Prefixed production
alternatives and, where possible, modifier deltas are folded into sparse
`INJECT` objects. One source may therefore produce both outputs, but their
responsibilities do not overlap.

Do not publish one complete building copy per business rule. A construct such
as `INJECT:brewery = { output = 1.15 }` does not provide a proven recursive
replacement contract. The production rule instead injects only newly named
methods; it never redeclares a Vanilla method key.

## Decision Record

| Attempt | Static result | Runtime result | Decision |
|---|---|---|---|
| CBP-prefixed full building copies without a database-entry mode | Generated values looked correct | Duplicate top-level building definitions | Rejected |
| Complete `REPLACE:<building>` objects reusing Vanilla production-method keys | Object parity and static validators passed | Duplicate production-method names and `Unexpected token` errors | Rejected for CBP building mutation |
| Nested `REPLACE:` or `INJECT:` on production-method containers | No experienced-mod example found; engine contract unconfirmed | Not promoted to runtime | Forbidden until a focused probe proves exact semantics |
| Sparse `INJECT:<building>` with additive modifier deltas | Static composition and M&T examples agree | Retained for additive-only sources | Supported |
| `INJECT:<building>` with plain `possible_production_methods` referencing a new, externally declared, uniquely prefixed method | Observed in M&T | Not currently needed by CBP | Supported append-only pattern with an ownership/uniqueness validator |
| `INJECT:<building>` with plain `unique_production_methods` containing only new `cbp_us09_*` keys | Static parser and generated uniqueness checks pass | Runtime confirmation pending | Selected US-09 production strategy; Vanilla remains an accepted alternative |
| Prefixed method added without mirroring its Vanilla advance unlock | Method is structurally valid but may bypass progression | Not promoted to runtime | Rejected; mirror every matching `unlock_production_method` |
| Complete exact-path source files after a clean deployment | Static source parity passes | Clean runtime confirmation still required after the failed `REPLACE` trial | Current structural strategy |

The install directory must be removed before copying a newly generated package.
Otherwise stale `cbp_<source>.txt` and exact-path `<source>.txt` files can load
together and invalidate the test. A result from a non-clean deployment must
not be used to infer file-override semantics.

## Manifest Contract

Distribution manifests live under:

```txt
packages/cbp_economy_rebalance/cbp_generated/us09_buildings/
```

Each manifest records source and generated SHA-256 fingerprints, changed and
unchanged building counts, and every changed field or structural action with
its old and new value. The CBG manifest records the exact or prefixed output,
the Vanilla fingerprint, and an `INJECT` database-entry mode for additive
fields and prefixed production alternatives. An exact-path entry has no
database-entry mode.

A generated building file without a matching manifest, an undeclared change,
a stale manifest, a structural mutation rendered as `INJECT`, a prefixed
structural file, or a prefixed nested production-method container is a
validation failure.

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

Local regeneration reads both maintenance multipliers from the local
configuration:

```txt
MODEU5_US08_BUILDING_MAINTENANCE_MULTIPLIER
MODEU5_US08_TRADE_BUILDING_MAINTENANCE_MULTIPLIER
```

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
parsing. Runtime validation must additionally confirm that a clean installation
contains no duplicate production-method or unexpected-token errors.

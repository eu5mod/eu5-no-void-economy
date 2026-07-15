# Community Balance Generator

## Purpose

The Community Balance Generator (CBG) builds one exact-path EU5 compatibility
mod from the declared balance intentions of multiple mods. It is a build-time
tool, not a runtime framework: participating mods publish small JSON specs and
the player or modpack maintainer generates one compatibility layer loaded last.

This avoids several mods independently overriding the same Vanilla file.

## Operations

| Operation | Meaning |
|---|---|
| `replace` | Set a fixed number, boolean, identifier, or script-value token. |
| `multiply` | Multiply the current value, initially Vanilla. |
| `add` | Add a signed delta to the current value. |
| `clamp` | Apply an optional numeric `min` and/or `max`. |
| `comment_out` | Preserve the Vanilla/current line as a comment. |
| `remove` | Remove the field from the generated object. |
| `add_field` | Add a known engine field absent from the Vanilla object. |
| `add_custom` | Add a mod-owned field declared in `custom_fields`. |
| `upsert_block` | Replace or insert a simple scalar child block. |

`add_field` and `add_custom` deliberately differ. The former uses an existing
engine endpoint. The latter requires an ownership declaration so two mods
cannot silently claim the same custom identifier.

Fixed and inserted scalar values are restricted to one safe token. Arithmetic
operations accept finite numbers only. `upsert_block` accepts a non-empty map
of safe scalar children; arbitrary script injection remains outside the MVP.

## Conflict policy

Every transformation defaults to `conflict: error`. When multiple mods target
the same `file + object + field`, generation fails unless all participants opt
into a compatible policy:

- `compose`: apply operations in spec/entry order;
- `last_wins`: permit an intentional terminal override;
- `error`: fail closed and require arbitration.

For example, `multiply 0.7` followed by `multiply 0.5` produces
`Vanilla × 0.7 × 0.5`. A `comment_out` or `remove` cannot be composed with
another operation unless the terminal entry explicitly selects `last_wins`.

## Strict selectors

Files may be exact paths, arrays of exact paths, or game-root-relative globs. Object paths use `/`, for
example `marketplace/modifier`. Each selected object and existing field must
match exactly once. Ambiguous or missing targets stop generation.

Bulk field rules use `"object": "**"` together with
`"occurrences": "all"`. Numeric values are transformed directly. A symbolic
value multiplied by a coefficient is replaced with a deterministic generated
script-value alias in `cbg_generated_scalars.txt`.

`exclude_values` may list symbolic values that a bulk rule must leave intact.
This prevents a centrally transformed symbol from receiving the same factor
again at direct call sites. Block-valued assignments remain transformable
because their internal expression is a separate calculation.

`exclude_files` defines explicit non-gameplay boundaries such as debug or
effect-localization trees. Therefore one master rule can discover every current
and future Vanilla occurrence without carrying a generated file inventory:

```json
{
  "file": "in_game/common/**/*.txt",
  "exclude_files": ["in_game/common/effect_localization/**/*.txt"],
  "object": "**",
  "field": "monthly_legitimacy",
  "operation": "multiply",
  "value": 0.2,
  "occurrences": "all",
  "on_missing": "skip"
}
```

Conditional bulk selectors use `where.inside` and `where.not_inside`. Each
clause matches a direct assignment on an enclosing object. `exclude_objects`
can reserve named top-level objects for a more specific policy. CBP uses this
to distinguish trade-building maintenance from other maintenance while giving
the marketplace family one inherited-base rule.

## Usage

```bash
python3 tools/community_balance_generator.py \
  --game-root "/path/to/Europa Universalis V/game" \
  --spec mods/mod-a/community_balance.json \
  --spec mods/mod-b/community_balance.json \
  --output-root generated/community_balance_compatibility
```

The output preserves Vanilla BOM handling, emits exact relative paths, adds
inline provenance comments, and writes `cbg_manifest.json` with source/output
hashes and the complete transformation chain.

The manifest is also the output ownership contract. CBG refuses to overwrite a
file absent from its previous manifest or a generated file changed since the
previous run. Obsolete outputs are removed only while their hash still matches
the previous generated hash.

## CBP parity migration

### Phase 1: central default values

The first publication milestone is deliberately limited to:

```txt
CBG master policy
  -> main_menu/common/script_values/default_values.txt
  -> byte-identical output to the corrected #188 generator
  -> no other generated file
```

Run the focused release gate with an installed Vanilla tree:

```bash
./tools/validate_cbp_cbg_default_values_parity.sh
```

The normal local generator validation runs this gate automatically:

```bash
./tools/validate_generators.sh
```

When `.cbp.local.env` provides `EU5_GAME_COMMON_DIR`, an invalid Vanilla path or
any parity difference fails the local validation. GitHub Actions intentionally
has no proprietary Vanilla source: the same command emits an explicit `SKIP`
there and continues with the CBG unit tests and static master-spec contract.

The command generates its spec and candidate output in a temporary directory.
It verifies that the manifest owns exactly one file and compares that file
byte-for-byte with the current #188 package output. It never materializes CBG
output in the repository.

The dedicated static-modifier, define, building, and other #188 generators
remain authoritative until each surface receives its own bounded parity gate.
In particular, CBG must not replace `cbp_location.txt` with a Vanilla exact-path
copy or publish a complete `00_defines.txt` as part of this phase.

The complete CBP balance configuration is versioned at
`tools/specs/cbp_pr188_balance.generated.json`. Its exporter discovers targets
from the installed Vanilla tree and the `.cbp.local.env` balance parameters.
It does not consume #188 generated manifests.

With EU5 installed and `.cbp.local.env` configured, run:

```bash
./tools/validate_cbp_cbg_parity.sh
```

This exports and checks the tracked spec, generates a clean exact-path mod,
resolves generated script-value aliases, and compares it with current CBP
outputs. It fails on any semantic mismatch. The latest PR #189 reference run
checked 381 political files, 236 non-political master-field surfaces, and 46
exact scalar/block targets with zero mismatches and no declared structural gap.

The political surface is expressed by 20 master field rules and building
maintenance by 148 good/policy rules. Production, merchant capacity, stockpile
capacity, minting, food production, food price, RGO prices, Pop promotion,
marketplace inheritance, and Market Warehouse availability are also generated
from Vanilla-derived rules. Matching Vanilla occurrences are discovered at
generation time; broad policies do not carry generated file inventories.

GitHub Actions runs `validate_cbg_master_spec.py` to enforce this discovery
contract without proprietary game files. Full output parity remains a local or
self-hosted release gate because `validate_cbp_cbg_parity.sh` requires the
installed Vanilla tree.

The comparison intentionally preserves #188 semantics during the tooling
migration. Changing a questionable balance result belongs in a separate
functional change.

### Experimental full-surface comparison

The broad `cbp_pr188_balance.generated.json` spec remains an analysis and
migration aid. It is not a publication authority and must not be used to replace
the package wholesale. The #188 generators remain the package materializer and
their manifests remain audit evidence. Each future migration must first achieve
a bounded, byte-identical parity gate before its ownership boundary can move.

## MVP boundary

The parser supports named Clausewitz/Jomini blocks and scalar assignments while
preserving untouched text. It intentionally rejects duplicate object paths,
duplicate fields, unsupported expressions, and ambiguous insertion anchors.
Future versions may add typed engine-field catalogs, load-order metadata,
semantic list operations, and a standalone repository/package.

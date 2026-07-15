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

`add_field` and `add_custom` deliberately differ. The former uses an existing
engine endpoint. The latter requires an ownership declaration so two mods
cannot silently claim the same custom identifier.

Fixed and inserted values are restricted to one safe scalar token. Arithmetic
operations accept finite numbers only; blocks and arbitrary script injection
are outside the MVP.

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

The complete CBP balance configuration is versioned at
`tools/specs/cbp_pr188_balance.generated.json`. It is exported from current CBP
generator manifests rather than maintained as a second hand-written source.

With EU5 installed and `.cbp.local.env` configured, run:

```bash
./tools/validate_cbp_cbg_parity.sh
```

This exports and checks the tracked spec, generates a clean exact-path mod,
resolves generated script-value aliases, and compares it with current CBP
outputs. It fails on any semantic mismatch. The PR #189 master-rule reference
run checked 380 political files and 845 scalar targets with zero mismatches.

The political surface is expressed by 20 master field rules. Their matching
Vanilla occurrences are discovered at generation time; the config does not
enumerate those files. Exact entries remaining in the exported spec represent
structural building-specific policies that do not yet share one safe selector.

The comparison intentionally preserves #188 semantics during the tooling
migration. Changing a questionable balance result belongs in a separate
functional change.

## MVP boundary

The parser supports named Clausewitz/Jomini blocks and scalar assignments while
preserving untouched text. It intentionally rejects duplicate object paths,
duplicate fields, unsupported expressions, and ambiguous insertion anchors.
Future versions may add typed engine-field catalogs, load-order metadata,
semantic list operations, and a standalone repository/package.

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

Files may be exact paths or game-root-relative globs. Object paths use `/`, for
example `marketplace/modifier`. Each selected object and existing field must
match exactly once. Ambiguous or missing targets stop generation.

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

## MVP boundary

The parser supports named Clausewitz/Jomini blocks and scalar assignments while
preserving untouched text. It intentionally rejects duplicate object paths,
duplicate fields, unsupported expressions, and ambiguous insertion anchors.
Future versions may add typed engine-field catalogs, load-order metadata,
semantic list operations, and a standalone repository/package.

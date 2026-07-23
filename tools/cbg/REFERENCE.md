# CBG Reference

## Specification shape

```json
{
  "schema_version": 1,
  "mod_id": "unique-mod-id",
  "business_rule": "Explain the player-facing balance intention.",
  "custom_fields": [],
  "transformations": []
}
```

Each transformation selects a Vanilla source and declares one operation. Files
are relative to the EU5 `game` directory.

`business_rule` is optional presentation metadata. CBG displays it in the
generation summary so reviewers can connect technical mutations to their
intended gameplay effect. When several specifications are composed, each
specification's rule is listed separately.

## Selectors

| Key | Purpose |
|---|---|
| `file` | Exact path, list of paths, or game-root-relative glob. |
| `exclude_files` | Globbed source paths excluded from a broad rule. |
| `object` | Named object path such as `marketplace/modifier`; `**` selects all objects. |
| `exclude_objects` | Named objects reserved from a broad rule. |
| `field` | Assignment to transform. |
| `occurrences` | Use `all` for deliberate bulk transformation. |
| `where.inside` | Require an assignment on an enclosing object. |
| `where.not_inside` | Reject an assignment on an enclosing object. |
| `on_missing` | `error` by default; `skip` for discovery rules. |

Exact selectors fail when missing or ambiguous. Broad discovery rules should
declare `occurrences: all` and decide explicitly whether a missing match is an
error or a valid no-op.

## Operations

| Operation | Meaning |
|---|---|
| `replace` | Set a fixed scalar value. |
| `multiply` | Scale the current value, initially Vanilla. |
| `add` | Add a signed numeric delta. |
| `clamp` | Apply an optional numeric minimum or maximum. |
| `comment_out` | Preserve the current assignment as a disabled comment. |
| `remove` | Remove the selected assignment. |
| `add_field` | Insert a known engine field. |
| `add_custom` | Insert a mod-owned field declared in `custom_fields`. |
| `upsert_block` | Replace or insert a simple scalar child block. |

Arithmetic accepts finite numbers only. Scalar insertion accepts safe tokens,
not arbitrary script fragments.

## Conflict policy

Transformations default to `conflict: error`.

- `error` stops when multiple mods target the same file, object, and field;
- `compose` applies compatible arithmetic operations in specification order;
- `last_wins` permits a deliberate terminal override.

For example, `multiply 0.7` followed by `multiply 0.5` with `compose` produces
`Vanilla x 0.7 x 0.5`. Structural operations such as `remove` or `comment_out`
must not compose accidentally.

## Symbolic values

Bulk arithmetic can encounter a symbolic script value instead of a number.
CBG emits a deterministic alias in `cbg_generated_scalars.txt` rather than
rewriting the original shared symbol. `exclude_values` reserves symbols that
are already transformed centrally and prevents double scaling at call sites.

## Provenance and ownership

Generated output can retain inline Vanilla provenance. The output manifest
records source hashes, output hashes, applied transformations, and owned paths.

CBG refuses to overwrite:

- an existing file absent from its previous manifest;
- a generated file modified since the previous run.

Obsolete generated files are removed only when their current hash still equals
the hash recorded by CBG. These checks protect hand-authored and foreign files.

## Version migration

Specifications describe intentions rather than frozen Vanilla copies. To move
from one EU5 version to another, run the same specifications against the new
game root. Relative operations use the new base values, broad selectors find
new occurrences, and strict failures expose structural changes requiring human
review.

## Command

```bash
python3 tools/cbg/community_balance_generator.py \
  --game-root "/path/to/Europa Universalis V/game" \
  --spec mod-a/community_balance.json \
  --spec mod-b/community_balance.json \
  --output-root generated/community_balance
```

The result is an ordinary EU5 compatibility mod plus `cbg_manifest.json`.

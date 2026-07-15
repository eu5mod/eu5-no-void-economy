# Community Balance Generator

Community Balance Generator (CBG) is a build-time tool for EU5 modders. A mod
declares balance intentions in JSON; CBG reads the installed Vanilla files and
generates one ordinary compatibility mod.

Use CBG when you need to:

- apply one rule across many events, laws, reforms, privileges, or technologies;
- regenerate a mod safely after a Vanilla version update;
- combine several modders' balance specifications without silent load-order conflicts;
- preserve source hashes, transformation history, and Vanilla provenance.

CBG has no campaign runtime cost.

## Five-minute example

Create `half_stability_rewards.json`:

```json
{
  "schema_version": 1,
  "mod_id": "half-stability-rewards",
  "transformations": [
    {
      "file": [
        "in_game/common/**/*.txt",
        "in_game/events/**/*.txt"
      ],
      "exclude_files": [
        "in_game/common/effect_localization/**/*.txt"
      ],
      "object": "**",
      "field": "add_stability",
      "operation": "multiply",
      "value": 0.5,
      "occurrences": "all",
      "on_missing": "skip"
    }
  ]
}
```

Generate the compatibility mod:

```bash
python3 tools/cbg/community_balance_generator.py \
  --game-root "/path/to/Europa Universalis V/game" \
  --spec half_stability_rewards.json \
  --output-root generated/half_stability_rewards
```

CBG discovers every matching Vanilla effect, halves it, preserves unrelated
content, and writes `cbg_manifest.json`. Load the generated compatibility mod
after the participating balance mods.

## Multiple modders

Pass each mod's specification to one generation command:

```bash
python3 tools/cbg/community_balance_generator.py \
  --game-root "/path/to/Europa Universalis V/game" \
  --spec mods/stability/community_balance.json \
  --spec mods/trade/community_balance.json \
  --output-root generated/community_balance
```

Independent changes are combined. Conflicting changes fail closed unless the
specifications explicitly allow composition or a last-wins policy.

## Version migration

After an EU5 update, point the same specifications at the new game directory
and regenerate. Relative operations such as `multiply` use the new Vanilla
values. Strict selectors expose removed or ambiguous targets instead of
silently retaining obsolete copied files.

## Operations

CBG supports `replace`, `multiply`, `add`, `clamp`, `comment_out`, `remove`,
`add_field`, `add_custom`, and `upsert_block`.

See [the example specification](examples/community_balance_spec.example.json)
and [the CBG reference](REFERENCE.md) for the complete selector, provenance,
conflict, and ownership contracts.

## Tests

From the repository root:

```bash
python3 -m unittest tools.cbg.tests.test_community_balance_generator
```

Everything outside `tools/cbg/` is integration code for the host mod and is not
required to understand or reuse the CBG core. This directory is the clean link
to share with other modders.

Host integrations that compile complex business policy into CBG JSON live
under [`adapters/`](adapters/). They are namespaced by host and are examples,
not yet a stable adapter SDK.

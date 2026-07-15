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

## Console output

Each materialization ends with a compact summary of generated files, expanded
rule candidates, applied mutations, and the manifest path. Existing manifest
metadata is also grouped into useful EU5 surfaces such as events, buildings,
laws, government reforms, estate privileges, parliament, advances, goods, and
script values. These are file and mutation counts; CBG does not rescan Vanilla
objects merely to decorate the console.

Colors are enabled automatically on an interactive terminal and omitted from
redirected logs and CI output. Standard and explicit controls are supported:

```bash
NO_COLOR=1 ./tools/generate_all.sh
CBG_COLOR=always ./tools/generate_all.sh
CBG_COLOR=never ./tools/generate_all.sh
```

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

## When to create an adapter

A direct JSON rule is enough when the desired change maps cleanly to CBG
selectors and operations. Create a host adapter when the policy first needs to
discover or classify Vanilla objects, combine several rules, or preserve a
host-specific edge case before CBG can apply deterministic mutations.

The current adapter contract is intentionally small:

```txt
host policy -> adapter -> resolved CBG JSON -> CBG -> generated mod + manifest
```

For a new host called `my_mod`, use this layout:

```txt
tools/cbg/adapters/my_mod/generate_my_mod_spec.py
tools/cbg/validator/my_mod/validate_my_mod_spec.py
```

The adapter should only compile policy. It must write an ordinary CBG
specification and leave file parsing, mutation, provenance, conflict handling,
and output ownership to `community_balance_generator.py`.

Minimal adapter outline:

```python
#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def build_spec() -> dict:
    return {
        "schema_version": 1,
        "mod_id": "my-mod-half-stability",
        "transformations": [{
            "file": ["in_game/common/**/*.txt", "in_game/events/**/*.txt"],
            "object": "**",
            "field": "add_stability",
            "operation": "multiply",
            "value": 0.5,
            "occurrences": "all",
            "on_missing": "skip",
        }],
    }


parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output.write_text(json.dumps(build_spec(), indent=2) + "\n")
```

## Add a validator

An adapter validator checks the compiled policy before Vanilla files are
mutated. It should fail closed when required selectors, operations, values, or
edge-case exclusions disappear. Keep it host-namespaced beside the adapter,
because those assertions describe the host mod rather than the reusable CBG
engine.

Minimal validator outline:

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path


spec = json.loads(Path(sys.argv[1]).read_text())
rules = spec.get("transformations", [])
expected = [
    rule for rule in rules
    if rule.get("field") == "add_stability"
    and rule.get("operation") == "multiply"
    and rule.get("value") == 0.5
]
if len(expected) != 1 or expected[0].get("occurrences") != "all":
    raise SystemExit("my_mod stability adapter contract failed")
print("my_mod stability adapter contract passed")
```

Run the complete path explicitly:

```bash
python3 tools/cbg/adapters/my_mod/generate_my_mod_spec.py \
  --output build/my_mod.json
python3 tools/cbg/validator/my_mod/validate_my_mod_spec.py build/my_mod.json
python3 tools/cbg/community_balance_generator.py \
  --game-root "/path/to/Europa Universalis V/game" \
  --spec build/my_mod.json \
  --output-root generated/my_mod
```

Adapters are policy compilers, not alternate generators. Validators secure the
compiled intent; generic CBG tests continue to secure parsing, mutation,
provenance, and conflict behavior.

## License

CBG is source-available under the
[PolyForm Noncommercial License 1.0.0](LICENSE.md). Noncommercial modding,
experimentation, study, and community collaboration are permitted by that
license. Commercial use requires separate permission from the author; contact
`ph.ausseil@gmail.com` to discuss a commercial license.

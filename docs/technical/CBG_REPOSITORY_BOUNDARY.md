# CBG Repository Boundary

## Shareable tool

`tools/cbg/` is the standalone Community Balance Generator surface:

```txt
tools/cbg/
  README.md
  REFERENCE.md
  community_balance_generator.py
  adapters/
    cbp/
      helpers/
  validator/
    cbp/
  examples/
  tests/
```

The core, documentation, examples, and tests must remain free of CBP, ModeU5,
US-story, and PR-migration policy. Host-specific policy is isolated under a
namespaced `adapters/<host>/` directory. `tools/cbg/` remains the directory
linked to external modders.

## CBP integration

The following namespaced families integrate CBP with the generic CBG core:

```txt
tools/cbg/adapters/cbp/generate_cbp_cbg_*_spec.py
tools/cbg/adapters/cbp/generate_cbp_community_balance_spec.py
tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh
tools/cbg/validator/cbp/validate_cbp_cbg_*_parity.sh
tools/cbg/validator/cbp/compare_cbp_cbg_outputs.py
tools/cbg/validator/cbp/validate_cbp_cbg_master_spec.py
```

They discover CBP targets, compile business exclusions and edge cases, invoke
CBG, and prove that the generated runtime files preserve approved behaviour.

## Retained legacy compilers

These #188-era tools are still functional policy authorities. The US-09
compiler has already moved beside the CBG adapter that consumes its discovery
plans; the remaining tools stay at repository root until their other callers
can be migrated without obscuring package ownership:

```txt
generate_political_reward_overrides.py
tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh
generate_us177_food_goods_manifest.py
generate_us177_minting_overrides.py
```

They no longer own Vanilla-derived runtime publication where the migration
matrix names CBG as materializer. They remain because they encode reviewed
edge cases such as symbolic-value centralization, Honor exclusion, block
effects, building inheritance, stockpile comments, and source discovery.

Removing one requires replacing its policy compiler, proving byte or semantic
parity, and updating `CBG_VANILLA_GENERATION_MATRIX.md`. A filename containing
`generate` is not by itself evidence that the file is dead.

## Migration evidence

Tracked `cbg_*_spec.json`, parity scripts, and the broad PR188 comparison
specification are CBP release evidence. They are deliberately outside
`tools/cbg/` because other CBG users do not need them.

`cbg_*_manifest.json` files are local execution receipts. They are regenerated
from the tracked specs, ignored by Git, and must not be used as policy sources
or committed release evidence. Static CI verifies output ownership from each
spec's `scope_contract.owned_outputs`; local Vanilla-backed parity runs verify
the generated manifests and byte-level outputs.

Once a retained compiler is replaced by declarative CBG policy, remove its
focused parity harness in a separate cleanup change after one release cycle.

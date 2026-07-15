# CBG Repository Boundary

## Shareable tool

`tools/cbg/` is the standalone Community Balance Generator surface:

```txt
tools/cbg/
  README.md
  REFERENCE.md
  community_balance_generator.py
  examples/
  tests/
```

It must remain free of CBP, ModeU5, US-story, and PR-migration policy. This is
the directory linked to external modders.

## CBP integration

The following root `tools/` families are CBP adapters, not part of CBG:

```txt
generate_cbp_cbg_*_spec.py
generate_cbp_community_balance_spec.py
validate_cbp_cbg_*_parity.sh
compare_cbp_cbg_outputs.py
validate_cbg_master_spec.py
```

They discover CBP targets, compile business exclusions and edge cases, invoke
CBG, and prove that the generated runtime files preserve approved behaviour.

## Retained legacy compilers

These #188-era tools are still functional policy authorities:

```txt
generate_political_reward_overrides.py
generate_us09_economy_overrides.sh
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

Tracked `cbg_*_spec.json`, `cbg_*_manifest.json`, parity scripts, and the broad
PR188 comparison specification are CBP release evidence. They are deliberately
outside `tools/cbg/` because other CBG users do not need them.

Once a retained compiler is replaced by declarative CBG policy, remove its
focused parity harness in a separate cleanup change after one release cycle.

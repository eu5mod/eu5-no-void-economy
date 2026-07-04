# Q3 — Code redundancy and generation

## Conclusion

Not every repetition is a problem. In ModeU5, some redundancy is required because the EU5 engine needs literal identifiers per good, map, or widget. The refactor must remove uncontrolled duplication, not intentional generated expansions.

## Repetition classification

| Repeated element | Type | Status | Refactor rule | Priority |
|---|---|---|---|---|
| Per-good adapters | Necessary generated repetition | Keep | Use `tools/modeu5_goods.sh`, template, and validation; do not factor by hand | P0 |
| Per-good map families | Engine / variable-map limitation | Keep | Full literal identifiers; no runtime map name parameter | P0 |
| Generated block templates | Controlled repetition | Strengthen | Add/adapt a template if a repeated block becomes a divergence source | P1 |
| `modeu5_debug_last_*` dumps | Standardized debug | Document | Central naming convention, no business wrapper hiding inputs | P2 |
| core_tests probe scenarios | Separate business tests | Keep carefully | Factor logging helpers, not scenarios | P2 |
| Map read/delete/rewrite | Map-imposed pattern | Encapsulate | Centralize record-level helpers; do not bypass | P1 |
| Initialization/schema guard | Fail-closed | Tolerate | Single trigger only if already confirmed and more readable | P1 |
| Runtime/audit/debug gates | Similar intent | Clarify | Name config/audit/performance/debug explicitly | P1 |
| Active cache rebuild/validation | Repair / scheduling | Audit | Declare the owner of each repair | P2 |
| CMM reset wrappers | UI/config | Tolerate | Keep while CMM names remain explicit | P3 |

## Current tooling contract

The standard generation model is:

```txt
tools/modeu5_tool_lib.sh      shared helpers
tools/modeu5_goods.sh         canonical goods registry
tools/templates/              generated block templates
tools/generate_all.sh         generation entry point
tools/validate_generators.sh  generator convention validation
```

An agent must extend this existing model. It must not create a standalone generator with its own goods list, its own renderer, or repeated blocks assembled by hand.

## Acceptable redundancy vs redundancy to fix

| Case | Acceptable? | Decision |
|---|---:|---|
| 74 literal adapters from the same template | Yes | Keep; the diff is large but auditable |
| 74 hand-copied blocks in a non-generated file | No | Replace with template/generator |
| Literal `modeu5_<good>_...` family in a generated file | Yes | Required for EU5 |
| Scripted-effect parameter containing a map name to construct | No | Generate a literal helper per good |
| Two similar probes covering two business contracts | Yes | Keep distinct |
| Two identical probes differing only by dump format | No | Factor the dump |
| Union cache + per-good cache | Yes | Scheduling scopes differ |
| Cache duplicating a source without clear rebuild/reset | No | Classify or delete after readers are identified |

## Refactor checklist for agents

Before deleting or factoring a repetition:

```txt
1. Is this repetition imposed by EU5 literal identifiers?
2. Is it generated from a single template?
3. Does tools/validate_generators.sh cover it?
4. Does the repetition protect a distinct business test?
5. Are all runtime/UI/debug readers identified?
6. Could the factorization introduce an unsupported dynamic name?
```

If the answer to 1 or 6 is yes, do not factor into runtime dynamic code. Generate literal code instead.

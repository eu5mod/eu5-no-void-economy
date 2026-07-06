# Q1 — Q8 file architecture and refactor surfaces

## Purpose

Q8 is a refactoring / standard-setting track after PR126. Its objective is not to rediscover the whole architecture, but to define where the next optimisation layers may change runtime code and where they must not.

This document is the Q8-owned equivalent of the PR126 Q1 document. It is maintained inside `docs/audits/q8` so Q8 stacked PRs can evolve their own standards without rewriting historical PR126 audit notes.

## Current post-PR126 file ownership

| Area | Current files | Q8 ownership interpretation | Refactor rule |
|---|---|---|---|
| Monthly entry / stock cycle | `in_game/common/on_action/modeu5_stock_on_actions.txt`, `in_game/common/scripted_effects/modeu5_stock_effects.txt` | country monthly framework | Keep as entry framework unless a later probe proves a safer global/monthly market pass. |
| Promoted-market local orchestration | `in_game/common/scripted_effects/modeu5_promoted_market_cycle_effects.txt` | logical market-local work, physically launched through country/market-center workaround | Do not duplicate this dispatcher. Change it only when a stacked PR proves ordering and owner semantics. |
| Capacity | `in_game/common/scripted_effects/modeu5_capacity_effects.txt` | country-owned pool + country-market record refresh | Optimise by separating reusable country facts from market-specific capacity contribution. |
| Runtime mode/config triggers | `in_game/common/scripted_triggers/modeu5_configuration_triggers.txt` | feature gates and debug/audit/runtime switches | Add gates here rather than scattering runtime-mode checks across generated bodies. |
| Generated active-good dispatch | `tools/generate_pr71_active_good_dispatch_helpers.sh`, `tools/templates/modeu5_pr71_active_good_dispatch_good.template.txt`, generated scripted effects | generated literal per-good guard surface | Keep generated names literal. Do not hand-edit generated output unless the generator is updated. |
| Validation and tooling | `tools/validate_generators.sh`, `tools/audit_modeu5_persistent_state.sh` | machine-checkable standards | Any new generator convention or persistent-state family needs validator/audit coverage. |
| Test-package Q8 probes | `packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_q8_probe_effects.txt`, `packages/modeu5_core_tests/in_game/events/modeu5_q8_probe_debug_events.txt` | isolated test/probe surface | May test unproven exposure or candidate scopes, but must not alter gameplay runtime. |
| Q8 methodology docs | `docs/audits/q8/Q*.md` | current Q8 standards | Update these documents when stacked PRs alter Q8 architecture/cache/loop/flow contracts. |

## Q8 file-change standard

```txt
1. Runtime code changes must name their owning surface: country prep, promoted-market local branch, country trade pass, validation, debug/probe, or tooling.
2. Generated runtime changes must start in the generator/template, not in generated output alone.
3. Large dispatcher files should not be edited if changing a public helper can make the same behaviour apply safely to all callers.
4. New Q8 standards belong in docs/audits/q8/Qx_*.md, not in inherited PR126 Qx docs.
5. Historical PR126 documents should only be changed to fix historical inaccuracies, not to document new Q8 implementation details.
6. Test-package probes may exercise unproven exposure only when isolated from live runtime.
```

## Q8.0 baseline decision

Q8.0 creates this Q8-owned Q1–Q5 document set.

No runtime file ownership changes are made by Q8.0.

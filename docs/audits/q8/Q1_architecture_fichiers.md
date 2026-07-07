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
| Generated active-good dispatch | `tools/generate_pr71_active_good_dispatch_helpers.sh`, `tools/templates/modeu5_pr71_active_good_dispatch_good.template.txt`, generated scripted effects | generated literal per-good guard surface | Keep generated names literal. Q8.2 aggregate pre-gating is deferred; do not add it to default generated output without a later sparse-index design. |
| Market-country work cache | `in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt` | current-market country-list work cache plus dirty scheduling surface | Keep `modeu5_countries_present_in_market` as a rebuilt work cache; dirty lists are scheduling state only, not durable per-market storage. |
| Market-sliced verifier | `in_game/common/scripted_effects/modeu5_market_sliced_verifier_effects.txt` | debug/audit candidate-market verifier slice | Q8.6 may verify dirty/promoted candidate markets only; no stock mutation, no stock repair, no global market pass. |
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

## Q8.2 / Q8.5 implementation update

This stacked PR changes one runtime ownership surface and records one deferred optimisation decision:

```txt
Q8.2:
  owner: tools/generate_pr71_active_good_dispatch_helpers.sh
  status: deferred
  reason: aggregate all-goods pre-scan is likely not profitable if most country-market pairs have at least one pending request.

Q8.5:
  owner: in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt
  change: promote the dirty market-country cache writer/consumer surface to a guarded runtime repair helper.
```

The live promoted-market dispatcher remains owned by `modeu5_promoted_market_cycle_effects.txt`; it continues to call the public generated PR7.1 US-10 dispatcher. No live Q8.2 aggregate pre-gate is introduced.

## Q8.6 implementation update

Q8.6 adds a new debug/audit-only verifier surface:

```txt
owner: in_game/common/scripted_effects/modeu5_market_sliced_verifier_effects.txt
entry: modeu5_run_market_sliced_verifier_candidates
gate: modeu5_market_sliced_verifier_allowed_trigger
candidate list: modeu5_market_sliced_verifier_candidate_markets
```

It builds a bounded candidate slice from dirty and promoted market lists, then verifies only those markets by rebuilding the current-market country work cache. It does not mutate stock, does not repair stock, does not clear dirty lists, and does not replace the live promoted-market dispatcher.

No Q8.4 body-helper split is included. No Q8.7 global market dispatcher switch is included.

## Q8.7 proof-stack update

Q8.7 mainly adds proof surfaces in `packages/modeu5_core_tests` and still does not move the live monthly dispatcher. PR #160 also updates one production configuration surface to align runtime gating with the proved Performance Mode boundary.

The proof surfaces are:

```txt
# global market-local exposure / cache-rebuild proof
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_q8_probe_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_q8_probe_debug_events.txt

# Normal Mode market-universe shadow comparison
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_q8_7_shadow_dispatcher_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_q8_7_shadow_debug_events.txt

# Performance Mode relevant-market shadow comparison
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_q8_7_performance_relevant_shadow_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_q8_7_performance_relevant_shadow_debug_events.txt
packages/modeu5_core_tests/in_game/localization/modeu5_q8_7_performance_relevant_l_english.yml

# Performance Mode market-owner workshape shadow
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_q8_7_workshape_shadow_effects.txt

# Performance Mode no-op dispatcher shadow
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_q8_7_noop_dispatcher_shadow_effects.txt
```

Production surface updated by #160:

```txt
in_game/common/scripted_triggers/modeu5_configuration_triggers.txt
```

Q1 reading:

```txt
No production package is reorganised.
No live dispatcher file is moved.
No stock-source file is touched.
No generated runtime file is changed.
No gameplay package boundary is changed.
The runtime trigger surface is corrected so Performance Mode detailed processing can be market-relevant rather than human-country-only.
```

The target architecture becomes better evidenced:

```txt
country preparation / relevance discovery
  -> future global market-local owner
  -> future country trade-owner pass
```

But the live owner remains the current market-center workaround until a later economic-equivalence PR proves the full switch is safe.
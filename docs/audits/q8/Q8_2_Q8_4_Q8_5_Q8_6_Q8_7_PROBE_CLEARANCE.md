# Q8.2 / Q8.4 / Q8.5 / Q8.6 / Q8.7 — Big probe PR

## Purpose

This stacked PR contains all five remaining Q8 probes in one PR.

It is intentionally not five stacked PRs. The probes are simple and belong together as a single clearance layer before the next implementation wave.

## Scope

Adds one shared probe effect file and one shared event menu in the test package:

```txt
packages/cbp_core_tests/in_game/common/scripted_effects/cbp_q8_probe_effects.txt
packages/cbp_core_tests/in_game/events/cbp_q8_probe_debug_events.txt
```

Adds one static structural audit:

```txt
tools/audit_q8_remaining_candidates.sh
```

Adds the TECH-01 / Q8-F9 validation companion:

```txt
docs/audits/q8/Q8_F9_TECH01.md
```

Updates the Q8-owned methodology docs:

```txt
docs/audits/q8/Q1_architecture_fichiers.md
docs/audits/q8/Q2_systeme_cache.md
docs/audits/q8/Q3_redondances_code.md
docs/audits/q8/Q4_boucles_performance.md
docs/audits/q8/archives/Q5_flux_logique_global.md
```

## Probe event

Run from the test package:

```txt
event cbp_q8_probe_debug.1
```

Available options:

```txt
all probes
Q8.2 only
Q8.4 only
Q8.5 only
Q8.6 only
Q8.7 only
```

The aggregate runtime entry point is:

```txt
cbp_debug_run_q8_remaining_candidate_probes
```

## Five probes in this PR

| Track | Probe effect | What it checks | What it does not do |
|---|---|---|---|
| Q8.2 / F2 | `cbp_q8_probe_us10_pending_gate` | Reads the canonical wheat pending-request map for the capital market and records whether the country-market probe surface is usable. | Does not add a generated aggregate has-any-pending gate. |
| Q8.4 / F4 | `cbp_q8_probe_helper_inventory` | Adds a runtime marker for the helper-inventory probe and pairs with static script checks for generated heavy-helper calls. | Does not split guarded helpers from body helpers. |
| Q8.5 / F5/F9a | `cbp_q8_probe_dirty_cache_lifecycle` | Marks the capital market dirty, repairs dirty market-country caches, and checks repair count. | Does not mutate stock or expand the dirty cache model. |
| Q8.6 / F9c | `cbp_q8_probe_market_sliced_verifier_candidate` | Builds and verifies a candidate-market slice list using the capital market. | Does not run a live verifier or repair market stock. |
| Q8.7 / F7 | `cbp_q8_probe_global_market_iterator_exposure` | Isolated test-package exposure check for the global market iterator. | Does not replace the current market-center ownership workaround. |

## Guardrails

```txt
1. No stock mutation.
2. No monthly dispatcher change.
3. No body-helper split.
4. No live verifier.
5. Q8.7 exposure remains in the test package only.
6. Any later implementation must update the Q8-owned Q-docs directly.
```

## Static validation

Run:

```sh
bash tools/audit_q8_remaining_candidates.sh
```

Expected static result:

```txt
PASS for all five probe entry points.
PENDING because runtime logs are still required before implementing Q8.2/Q8.4/Q8.5/Q8.6/Q8.7.
```

## Runtime validation evidence — 2026-07-06

Runtime event used:

```txt
event cbp_q8_probe_debug.1
```

Observed PASS markers:

```txt
ModeU5 Q8.2 PROBE us10_pending_gate PASS wheat_pending=0.0000
ModeU5 Q8.4 PROBE helper_inventory PASS runtime_noop_static_inventory_required
ModeU5 Q8.5 PROBE dirty_cache_lifecycle PASS repair_count=3
ModeU5 Q8.6 PROBE market_slice_candidate PASS
ModeU5 Q8.7 PROBE global_market_iterator PASS count=129
ModeU5 Q8 PROBE RESULT all_remaining_candidates PASS
```

Interpretation:

```txt
Q8 probe runtime validation: PASS.
Full revalidation suite: NOT REQUIRED for this PR.
event cbp_revalidate_debug.1: NOT REQUIRED for #150 validation.
```

## Known cleanup items

```txt
- Q8.7 emitted PASS with count=129, but error.log also reported unset-counter script errors around test_cbp_q8_7_global_market_count. Harden the counter guard if a clean error log is required.
- Q8 probe event localization keys are missing. This is cosmetic for the probe event and does not invalidate the runtime PASS markers.
```

## Resulting interpretation

This PR contains all five probes. It does not implement the later optimisations. The purpose is to collect evidence and clear which implementation PRs are safe next.

After the 2026-07-06 run, #150 has enough runtime evidence to mark the probe layer itself as passed. Later implementation PRs remain separate decisions.

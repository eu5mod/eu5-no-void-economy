# Q8.2 / Q8.4 / Q8.5 / Q8.6 / Q8.7 — Big probe PR

## Purpose

This stacked PR contains all five remaining Q8 probes in one PR.

It is intentionally not five stacked PRs. The probes are simple and belong together as a single clearance layer before the next implementation wave.

## Scope

Adds one shared probe effect file and one shared event menu in the test package:

```txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_q8_probe_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_q8_probe_debug_events.txt
```

Adds one static structural audit:

```txt
tools/audit_q8_remaining_candidates.sh
```

## Probe event

Run from the test package:

```txt
event modeu5_q8_probe_debug.1
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
modeu5_debug_run_q8_remaining_candidate_probes
```

## Five probes in this PR

| Track | Probe effect | What it checks | What it does not do |
|---|---|---|---|
| Q8.2 / F2 | `modeu5_q8_probe_us10_pending_gate` | Reads the canonical wheat pending-request map for the capital market and records whether the country-market probe surface is usable. | Does not add a generated aggregate has-any-pending gate. |
| Q8.4 / F4 | `modeu5_q8_probe_helper_inventory` | Adds a runtime marker for the helper-inventory probe and pairs with static script checks for generated heavy-helper calls. | Does not split guarded helpers from body helpers. |
| Q8.5 / F5/F9a | `modeu5_q8_probe_dirty_cache_lifecycle` | Marks the capital market dirty, repairs dirty market-country caches, and checks repair count. | Does not mutate stock or expand the dirty cache model. |
| Q8.6 / F9c | `modeu5_q8_probe_market_sliced_verifier_candidate` | Builds and verifies a candidate-market slice list using the capital market. | Does not run a live verifier or repair market stock. |
| Q8.7 / F7 | `modeu5_q8_probe_global_market_iterator_exposure` | Isolated test-package exposure check for the global market iterator. | Does not replace the current market-center ownership workaround. |

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

## Runtime validation expectations

Expected log markers:

```txt
ModeU5 Q8.2 PROBE us10_pending_gate PASS
ModeU5 Q8.4 PROBE helper_inventory PASS
ModeU5 Q8.5 PROBE dirty_cache_lifecycle PASS
ModeU5 Q8.6 PROBE market_slice_candidate PASS
ModeU5 Q8.7 PROBE global_market_iterator PASS
ModeU5 Q8 PROBE RESULT all_remaining_candidates PASS
```

If Q8.7 fails to parse or run, Q8.7 remains blocked and the current market-center ownership workaround remains authoritative.

## Resulting interpretation

This PR contains all five probes. It does not implement the later optimisations. The purpose is to collect evidence and clear which implementation PRs are safe next.

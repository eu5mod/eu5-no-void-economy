# Q8.2 / Q8.4 / Q8.5 / Q8.6 / Q8.7 — Probe clearance PR

## Purpose

This stacked PR clears the remaining Q8 candidates by converting each one into an explicit probe decision.

It is intentionally not a gameplay refactor PR:

```txt
- no stock mutation;
- no dispatcher switch;
- no body-helper split;
- no live verifier;
- no broad monthly world scan.
```

The goal is to decide which later implementation PRs are justified, which need runtime evidence, and which must stay deferred.

## Clearance matrix

| Track | Candidate | Probe outcome expected from this PR | Next allowed PR |
|---|---|---|---|
| Q8.2 / F2 | US-10 aggregate pending-request gate | static + metric-snapshot probe; determine whether a country-market has-any-pending gate is needed before generated per-good dispatch | `audit/q8-us10-gating` or `feature/q8-us10-aggregate-gate` |
| Q8.4 / F4 | split guarded helpers from body helpers | static caller-inventory probe; do not split until all generated helper callers are classified | `audit/q8-helper-caller-inventory` |
| Q8.5 / F5/F9a | dirty derived-cache architecture | confirm existing dirty-market producers/consumers before inventing new cache model | `probe/q8-dirty-derived-caches` |
| Q8.6 / F9c | market-sliced verifier | clear only candidate/dirty market slicing as probe scope; no live verifier | `probe/q8-f9c-market-slicing` |
| Q8.7 / F7 | native global market-local pass | exposure probe only; no switch from market-center owner workaround | `probe/q8-global-market-pass` |

## Static probe command

```sh
bash tools/audit_q8_remaining_candidates.sh
```

The script checks repository structure and prints PASS/PENDING/FAIL classifications. PENDING is expected for runtime-only questions; FAIL is reserved for missing guardrails or accidental live usage.

## Runtime evidence still required

The static probe cannot prove EU5 runtime behaviour. The later probe PRs should add/run runtime evidence for:

```txt
Q8.2 — debug/audit monthly PR7.1 counters: considered vs pending-hit vs processed.
Q8.5 — dirty-market producer lifecycle and repair count on an actual market.
Q8.6 — candidate/dirty market slice coverage and save/reload stability.
Q8.7 — whether every_market_in_world is valid from a safe once-per-month global surface.
```

## Guardrails

```txt
1. Probes may write debug/profile variables only.
2. Probes must not mutate stock.
3. Probes must not alter the monthly dispatcher.
4. Probes must not add every_market_in_world to live runtime files.
5. Probes must not use every_location_in_the_world as a monthly verifier substitute.
6. Any later implementation must update the Q8-owned Q-docs directly.
```

## Resulting interpretation

This PR does not implement Q8.2, Q8.4, Q8.5, Q8.6, or Q8.7. It clears their next-step classification so the stack can proceed without ambiguity.

# Q8.6 — market-sliced verifier implementation

## Purpose

Q8.6 promotes the PR150 candidate market-slice probe into a bounded debug/audit verifier surface.

It does not implement stock repair and does not mutate stock.

## Implemented shape

New runtime verifier file:

```txt
in_game/common/scripted_effects/cbp_market_sliced_verifier_effects.txt
```

New configuration trigger:

```txt
cbp_market_sliced_verifier_allowed_trigger
  -> debug runtime OR audit runtime
```

Entry point:

```txt
cbp_run_market_sliced_verifier_candidates
```

Candidate list:

```txt
cbp_market_sliced_verifier_candidate_markets
```

Candidate sources:

```txt
cbp_market_country_cache_dirty_markets
cbp_promoted_markets_this_cycle
```

Verifier action per candidate market:

```txt
cbp_rebuild_countries_present_in_market
```

This verifies the current-market country work-cache path for selected markets only.

## Counters

```txt
cbp_market_sliced_verifier_candidates_built
cbp_market_sliced_verifier_candidates_checked
cbp_market_sliced_verifier_candidates_passed
cbp_market_sliced_verifier_candidates_failed
cbp_market_sliced_verifier_last_run_skipped
cbp_market_sliced_verifier_last_run_empty
cbp_market_sliced_verifier_last_run_failed
cbp_market_sliced_verifier_last_run_passed
```

These counters are diagnostic state only.

## Guardrails

```txt
- No stock mutation.
- No stock repair.
- No generated goods helper split.
- No global market iterator.
- No live dispatcher replacement.
- No durable per-market country-list storage.
- Dirty market scheduling list is copied as candidate input and not cleared by the verifier.
```

## Validation

Static validation to run before merge:

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_cbp_persistent_state.sh
git diff --check
```

Runtime smoke suggested after static checks:

```txt
event cbp_q8_probe_debug.1
```

Debug/audit runtime validation should also call:

```txt
cbp_run_market_sliced_verifier_candidates = yes
```

Expected interpretation:

```txt
No candidates: SKIP no_candidate_markets.
Candidate markets exist: pass/fail counters record market-country work-cache rebuild status.
Failure means the verifier slice found a market-country work-cache rebuild problem, not a stock repair result.
```

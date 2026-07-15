# Q8.2 / Q8.5 — implementation status

## Purpose

This stacked PR implements Q8.5 and records the Q8.2 decision reached during review.

```txt
Q8.5 / F5  — implemented: guarded dirty market-country cache repair consumer
Q8.2 / F2  — deferred: aggregate US-10 pending pre-gate is not live
```

The Q8.2 aggregate pre-gate is deferred because it is only profitable when no-request country-market pairs dominate. If most market countries have at least one good in pending demand, an aggregate all-goods pre-scan adds work before the existing per-good pending dispatcher.

It deliberately does not implement:

```txt
Q8.2 — live aggregate pre-gate
Q8.4 — body-helper split
Q8.6 — live verifier
Q8.7 — global market-local dispatcher replacement
```

## Q8.2 decision — deferred

Rejected live shape for now:

```txt
cbp_pr71_process_us10_monthly_market_pending_goods
  -> scan all supported goods to determine whether any pending request exists
  -> if any pending exists:
       run the existing generated per-good US-10 dispatcher
```

Reason:

```txt
If pending demand is common, this adds an all-goods pre-scan before the existing per-good wrapper surface.
That can be neutral-negative or anti-optimising.
```

Preferred later design:

```txt
At request-write time:
  add country-market or country-market-good to a sparse pending work list

At monthly US-10 time:
  iterate only pending work items
  process requests
  clear the sparse pending work list
```

This later design should avoid both:

```txt
- scanning all goods just to discover that demand likely exists;
- entering per-good wrappers for country-market pairs with no demand.
```

## Q8.5 implementation

The existing dirty market-country cache writer/consumer surface is promoted from probe-only evidence to a guarded runtime helper.

Existing producer:

```txt
cbp_mark_market_country_cache_dirty
```

Existing consumer:

```txt
cbp_repair_dirty_market_country_caches
```

New guarded consumer:

```txt
cbp_repair_dirty_market_country_caches_if_needed
```

The dirty list remains:

```txt
cbp_market_country_cache_dirty_markets
```

Boundary:

```txt
cbp_countries_present_in_market remains a rebuilt current-market work cache.
cbp_market_country_cache_dirty_markets remains scheduling state only.
No durable per-market country-list cache is introduced.
TECH-01 row 126 therefore remains NOT_CONFIRMED unless a later PR proves durable keyed storage.
```

## Files changed

Runtime / generator / validation:

```txt
tools/generate_pr71_active_good_dispatch_helpers.sh
tools/validate_generators.sh
in_game/common/scripted_effects/cbp_market_country_cache_effects.txt
```

Q8-owned standards updated after implementation:

```txt
docs/audits/q8/Q1_architecture_fichiers.md
docs/audits/q8/Q2_systeme_cache.md
docs/audits/q8/Q3_redondances_code.md
docs/audits/q8/Q4_boucles_performance.md
docs/audits/q8/archives/Q5_flux_logique_global.md
```

## Guardrails

```txt
- No stock mutation semantics changed.
- No US-00 / US-10 ordering change.
- No live Q8.2 aggregate pre-gate.
- No Q8.4 body-helper split.
- No live verifier.
- No Q8.7 global-market dispatcher replacement.
- No market-scope variables.
- No durable per-market country-list storage.
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
event cbp_pr126_debug.1
event cbp_us10_debug.1
event cbp_q8_probe_debug.1
```

Expected interpretation:

```txt
Q8.5: dirty market-country cache repair remains guarded and scheduling-only.
Q8.2: deferred unless a later sparse pending-index PR proves a better design.
```

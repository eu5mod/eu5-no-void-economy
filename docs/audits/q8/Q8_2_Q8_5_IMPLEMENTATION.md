# Q8.2 / Q8.5 — implementation

## Purpose

This stacked PR implements the two Q8 tracks that were cleared by the PR150 probe layer and are safe to implement without changing stock semantics:

```txt
Q8.2 / F2  — generated US-10 aggregate pending-request gate
Q8.5 / F5  — guarded dirty market-country cache repair consumer
```

It deliberately does not implement:

```txt
Q8.4 — body-helper split
Q8.6 — live verifier
Q8.7 — global market-local dispatcher replacement
```

## Q8.2 implementation

The generated PR7.1 US-10 dispatcher now performs a country-market aggregate pending-request gate before entering the per-good US-10 wrappers.

New generated helper:

```txt
modeu5_pr71_prepare_us10_pending_request_gate
```

Temporary result value:

```txt
modeu5_pr71_us10_country_market_has_pending_request
```

Updated generated dispatcher shape:

```txt
modeu5_pr71_process_us10_monthly_market_pending_goods
  -> modeu5_pr71_prepare_us10_pending_request_gate
  -> if modeu5_pr71_us10_country_market_has_pending_request > 0:
       modeu5_pr71_process_us10_monthly_market_good_<good>
```

Authoritative source state remains unchanged:

```txt
modeu5_consumption_<good>_pending_requested_by_market[market]
```

The gate is scheduler state only. It does not replace the per-good pending request maps and does not change the stock resolver.

## Q8.5 implementation

The existing dirty market-country cache writer/consumer surface is promoted from probe-only evidence to a guarded runtime helper.

Existing producer:

```txt
modeu5_mark_market_country_cache_dirty
```

Existing consumer:

```txt
modeu5_repair_dirty_market_country_caches
```

New guarded consumer:

```txt
modeu5_repair_dirty_market_country_caches_if_needed
```

The dirty list remains:

```txt
modeu5_market_country_cache_dirty_markets
```

Boundary:

```txt
modeu5_countries_present_in_market remains a rebuilt current-market work cache.
modeu5_market_country_cache_dirty_markets remains scheduling state only.
No durable per-market country-list cache is introduced.
TECH-01 row 126 therefore remains NOT_CONFIRMED unless a later PR proves durable keyed storage.
```

## Files changed

Runtime / generator:

```txt
tools/generate_pr71_active_good_dispatch_helpers.sh
tools/validate_generators.sh
in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt
```

Q8-owned standards updated after implementation:

```txt
docs/audits/q8/Q1_architecture_fichiers.md
docs/audits/q8/Q2_systeme_cache.md
docs/audits/q8/Q3_redondances_code.md
docs/audits/q8/Q4_boucles_performance.md
docs/audits/q8/Q5_flux_logique_global.md
```

## Guardrails

```txt
- No stock mutation semantics changed.
- No US-00 / US-10 ordering change.
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
./tools/audit_modeu5_persistent_state.sh
git diff --check
```

Runtime smoke suggested after static checks:

```txt
event modeu5_pr126_debug.1
event modeu5_us10_debug.1
event modeu5_q8_probe_debug.1
```

Expected interpretation:

```txt
Q8.2: no-request country-market pairs skip generated per-good US-10 dispatcher.
Q8.5: dirty market-country cache repair remains guarded and scheduling-only.
```

# Q3 — Q8 redundancy and generated-code boundaries

## Purpose

Q8 should reduce repeated runtime work without creating parallel helper families that become harder to audit than the original implementation.

This document is the Q8-owned redundancy standard for helper extraction, generated literal goods, and duplicate guard layers.

## Current redundancy risks

| Surface | Risk | Q8 rule |
|---|---|---|
| Generated per-good helpers | Literal symbols are required by EU5, but generated all-good wrappers can accumulate guard layers. | Keep the literal generated surface, but move policy into generator/template and validators. |
| PR7.1 guarded dispatch | Outer active-good / pending-request wrapper may call helpers that still contain internal guards. | Do not split body helpers until all callers are inventoried. Do not add Q8.2 aggregate pre-scan to default runtime without a sparse-index design. |
| Capacity helpers | Public helpers may be called from several surfaces. | Prefer changing the public helper contract once rather than editing each large dispatcher caller. |
| Market-sliced verifier helpers | Verifier helpers can drift into hidden repair or stock mutation. | Keep Q8.6 verifier helpers debug/audit gated, candidate-sliced, and non-stock-mutating. |
| Debug/profile counters | Metrics can look like business state when scattered. | Centralize gates and keep metrics explicitly diagnostic. |
| Q8 docs vs PR126 docs | Duplicated methodology can drift. | Q8 owns new Q1–Q5 documents; PR126 documents remain inherited context. |

## Q8 helper-change standard

```txt
1. Public helpers remain safe and guarded.
2. Internal body helpers may be introduced only after caller inventory proves every caller has the required guard.
3. Generated helper changes must update generator/template and validation, not only generated output.
4. A refactor may reduce duplicate checks only if it does not create an unsafe call surface.
5. Documentation duplication is avoided by keeping Q8 standards in docs/audits/q8/Qx_*.md.
```

## Q8.0 baseline decision

Q8.0 adds no helper or generator changes.

It classifies Q8.4 / F4 as `PROBE_FIRST`: split guarded helpers from body helpers only after caller inventory.

## Q8.4 probe update — helper inventory bridge

PR #150 adds a test-package Q8.4 marker probe:

```txt
modeu5_q8_probe_helper_inventory
```

This runtime marker is paired with the static audit script, which checks that the generated PR7.1 wrappers still call the existing heavy helpers:

```txt
modeu5_process_us00_monthly_market_good_wheat = yes
modeu5_process_us10_monthly_market_good_wheat = yes
```

Q8.4 remains blocked from implementation until a full caller inventory classifies all calls as safe guarded wrappers, explicit tests, or unsafe/unknown.

## Q8.2 / Q8.5 implementation update

Q8.2 is deferred.

The rejected generated-wrapper idea was:

```txt
modeu5_pr71_process_us10_monthly_market_pending_goods
  -> modeu5_pr71_prepare_us10_pending_request_gate
  -> if country-market has any pending request:
       modeu5_pr71_process_us10_monthly_market_good_<good>
```

This is not live because it adds an all-goods pre-scan. If most country-market pairs have at least one pending request, the pre-scan duplicates rather than removes work.

The existing per-good wrapper helpers and heavy helpers are preserved:

```txt
modeu5_pr71_process_us10_monthly_market_good_<good>
modeu5_process_us10_monthly_market_good_<good>
```

Q8.5 adds a guarded dirty repair consumer but no parallel cache family:

```txt
modeu5_repair_dirty_market_country_caches_if_needed
```

This is intentionally not a body-helper split, not a durable per-market list, and not a replacement for `modeu5_rebuild_countries_present_in_market`.

## Q8.6 implementation update

Q8.6 adds a separate verifier helper family rather than changing the stock operators or generated goods helpers:

```txt
modeu5_clear_market_sliced_verifier_state
modeu5_add_market_to_market_sliced_verifier_candidates
modeu5_prepare_market_sliced_verifier_candidates
modeu5_verify_market_sliced_verifier_candidate
modeu5_run_market_sliced_verifier_candidates
```

The verifier reuses the existing market-country work-cache rebuild helper only for candidate markets:

```txt
modeu5_rebuild_countries_present_in_market
```

Boundary:

```txt
- no stock mutation;
- no stock repair;
- no generated goods helper split;
- no live dispatcher replacement;
- no durable per-market country-list cache.
```

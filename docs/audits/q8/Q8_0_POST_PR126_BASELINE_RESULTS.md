# Q8.0 — Post-PR126 baseline audit results

## Purpose

This document is the first stacked Q8 audit result after #126 merged into `main`.

It freezes the current runtime baseline before Q8 implementation PRs start. The goal is to prevent Q8 work from re-optimising stale PR126 assumptions.

This PR is documentation-only. It does not change runtime behaviour.

## Baseline inspected

```txt
base: main after PR126 merge
baseline commit observed in #147: 865d7109d7310bdab2ef4318698244efba86540f
```

Primary files inspected:

```txt
in_game/common/on_action/modeu5_stock_on_actions.txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
in_game/common/scripted_effects/modeu5_promoted_market_cycle_effects.txt
in_game/common/scripted_effects/modeu5_capacity_effects.txt
in_game/common/scripted_effects/modeu5_stock_demand_resolver_effects.txt
in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt
tools/generate_pr71_active_good_dispatch_helpers.sh
tools/templates/modeu5_pr71_active_good_dispatch_good.template.txt
```

Q5 flow documents are part of this baseline, not optional Q8 reading:

```txt
docs/audits/pr126/Q5_flux_logique_global.md
docs/audits/pr126/Q5.1_current_global_flow.md
```

If a Q5.2 checkpoint is added later, it should be treated as a Q5 flow subsection or immediate Q5.1 follow-up before Q8 optimisation documents. It should not be placed inside the Q8 future-optimisation section.

## Executive baseline

Current `main` has the PR126 live promoted-market dispatcher wired, but the monthly entry point is still the country monthly pulse.

Current shape:

```txt
monthly_country_pulse
  -> modeu5_monthly_stock_cycle_pulse
     -> modeu5_run_monthly_stock_cycle
        -> modeu5_prepare_performance_mode_human_relevant_markets
        -> modeu5_run_monthly_capacity_refresh_for_current_country
        -> modeu5_prepare_monthly_market_seen_registry
        -> modeu5_prepare_human_relevant_full_ledger_markets
        -> modeu5_run_monthly_promoted_market_local_cycle
        -> modeu5_run_monthly_country_trade_owner_cycle
        -> optional monthly stock reconciliation in Audit mode
```

Important interpretation:

```txt
The live market-local branch is improved versus pre-PR126 because it is routed through every_market_center_in_country, not every country present in every market.

However, it is still entered from country pulse and still relies on a convention: the country that owns the market center acts as a deterministic owner proxy for market-local work.
```

## Confirmed ownership boundaries

| Surface | Current owner | Target Q8 interpretation | Status |
|---|---|---|---|
| Monthly entry | `monthly_country_pulse` | still country-driven | accepted baseline |
| Country capacity refresh | country | true country-owned work | keep / optimise |
| Promoted-market local cycle | country pulse via market-center owned markets | logically market-local | Q8.7 probe candidate |
| Market-country participant rebuild | current market | work cache rebuild, not source of truth | Q8.5 candidate |
| US-00 same-market production/admission | present country inside promoted market | market-local pass, country-record mutation | keep ordering |
| US-10 same-market consumption | second present-country pass inside promoted market | must run after all US-00 present-country work | keep two-pass invariant |
| Inter-market trade | country trade-owner pass | country-scope `every_trade` remains required | keep |
| Validation/reconciliation | optional audit/reconciliation surfaces | should not hide duplicated orchestration | keep / scope |

## Confirmed Q8 findings after static inspection

### Q8.1 / F3 — PR7.1 profiling counters

Classification: `IMPLEMENT_NOW`

Finding:

```txt
The PR7.1 generated dispatcher still writes considered/processed counters unconditionally from generated per-good wrappers.
```

Relevant surfaces:

```txt
tools/generate_pr71_active_good_dispatch_helpers.sh
tools/templates/modeu5_pr71_active_good_dispatch_good.template.txt
in_game/common/scripted_effects/modeu5_promoted_market_cycle_effects.txt
```

Evidence from static shape:

```txt
modeu5_run_promoted_market_live_local_branch_market_all_goods
  -> modeu5_pr71_prepare_active_good_metrics
  -> every present country:
       modeu5_note_promoted_market_live_us00_country_pass
       modeu5_pr71_process_us00_monthly_market_active_goods
  -> every present country:
       modeu5_note_promoted_market_live_us10_country_pass
       modeu5_pr71_process_us10_monthly_market_pending_goods
```

The generated template increments:

```txt
modeu5_pr71_us00_goods_considered
modeu5_pr71_us00_goods_processed
modeu5_pr71_us00_goods_produced_gate_hits
modeu5_pr71_us00_goods_previous_state_hits
modeu5_pr71_us10_goods_considered
modeu5_pr71_us10_pending_request_hits
modeu5_pr71_us10_requests_processed
```

Target first implementation:

```txt
Gate PR7.1 debug/profile metric writes behind an explicit debug/profile trigger while preserving validation visibility when profiling is enabled.
```

Do not remove:

```txt
- gameplay ledger counters;
- actual US-00/US-10 business maps;
- validation counters required to prove economic equivalence in debug/profile mode.
```

Expected next PR:

```txt
feature/q8-profile-counter-gates
```

### Q8.2 / F2 — US-10 aggregate pending-request gating

Classification: `PROBE_FIRST`

Finding:

```txt
The live promoted-market branch still enters a generated all-good US-10 pending dispatcher for every country present in the current promoted market.

The per-good wrapper then checks the pending request map and calls the heavy resolver only if a pending request exists for that country + market + good.
```

Static shape:

```txt
for each country present in promoted market:
  modeu5_pr71_process_us10_monthly_market_pending_goods
    -> for each generated good:
         read modeu5_consumption_<good>_pending_requested_by_market[market]
         if quantity > 0:
           modeu5_process_us10_monthly_market_good_<good>
```

Interpretation:

```txt
PR7.1 already prevents the heavy resolver from running for no-request goods.
It does not prove that no-request country-market pairs avoid generated per-good guard checks entirely.
```

Target next action:

```txt
Add a debug-only Q8.2 probe or audit comment that counts country-market pairs entering US-10 generated dispatch versus pairs with at least one pending request.
```

Do not add an aggregate gate until the probe classifies the current state as:

```txt
A. Already implemented — no new aggregate gate needed.
B. Partially implemented — add cheap has-any-pending-request gate.
C. Not implemented — add aggregate gate before generated per-good dispatch.
```

Expected next branch:

```txt
audit/q8-us10-gating
```

### Q8.3 / F1 — Country capacity-pool stamping

Classification: `IMPLEMENT_NOW`

Finding:

```txt
The capacity subsystem already distinguishes:
- country location-capacity pool rebuild;
- country storage-capacity pool calculation;
- market-specific trade-capacity application.
```

Current monthly country refresh:

```txt
modeu5_run_monthly_capacity_refresh_for_current_country
  -> modeu5_recalculate_saved_country_storage_capacities
     -> modeu5_calculate_country_storage_capacity_pool
     -> every_market_present_in_country:
          modeu5_recalculate_country_market_capacity_from_prepared_pool_shared
```

Current promoted-market local branch:

```txt
for each country present in promoted market:
  modeu5_prepare_promoted_country_market_capacity
    -> modeu5_calculate_country_storage_capacity_pool
    -> modeu5_recalculate_country_market_capacity_from_prepared_pool_shared
```

Interpretation:

```txt
The expensive owned-location rank pool is not necessarily rebuilt here, but the country-wide storage pool calculation and every_market_present_in_country count can still repeat once per present country per promoted market.
```

Target first implementation:

```txt
Add a monthly country capacity-pool stamp so the country storage-capacity pool calculation is prepared once per country per month, then reused for each country-market capacity record.
```

Guardrails:

```txt
- Do not reuse a pool across countries.
- Do not skip market-specific merchant/trade-capacity contribution.
- Keep country-market capacity refresh before US-00 active-good dispatch.
- Classify any new stamp/cache in PERSISTENT_STATE_AUDIT if persistent.
```

Expected next branch:

```txt
feature/q8-capacity-pool-stamp
```

### Q8.4 / F4 — Guarded helper / body helper split

Classification: `PROBE_FIRST`

Finding:

```txt
The PR7.1 wrapper proves an outer active-good or pending-request gate before calling the existing generated heavy helper.

The existing helper may still contain its original internal guard logic.
```

Risk:

```txt
Splitting body helpers too early could create unsafe call surfaces if any caller reaches the body without the required business gate.
```

Target next action:

```txt
Inventory callers of:
- modeu5_process_us00_monthly_market_good_<good>
- modeu5_process_us10_monthly_market_good_<good>

Only generate body helpers after every caller is classified as guarded or legacy-safe.
```

Expected next branch:

```txt
audit/q8-helper-body-split
```

### Q8.5 / F5 + F9a — Dirty-set architecture for derived caches

Classification: `PROBE_FIRST`

Finding:

```txt
The market-country cache layer already has:
- modeu5_countries_present_in_market
- modeu5_market_country_cache_dirty_markets
- modeu5_mark_market_country_cache_dirty
- modeu5_repair_dirty_market_country_caches
```

The current live promoted-market path still rebuilds `countries_present_in_market` directly for the current promoted market:

```txt
modeu5_prepare_promoted_market_country_cache
  -> modeu5_rebuild_countries_present_in_market
```

Interpretation:

```txt
Q8 should not invent a new market-country cache model.
It should first prove dirty-set producers and consumers around the existing dirty-market repair surface.
```

Target first probe:

```txt
Add debug-only dirty-set lifecycle probes for confirmed ownership/capacity hooks.
Verify affected markets/countries are marked dirty and only those derived caches are repaired.
```

Guardrails:

```txt
- `countries_present_in_market` remains a rebuilt work cache, not durable truth.
- Dirty lists are scheduling state only.
- Do not require rich per-location persistent records.
- Do not use runtime-built map names.
```

Expected next branch:

```txt
probe/q8-dirty-derived-caches
```

### Q8.6 / F9c — Market-sliced verifier

Classification: `PROBE_FIRST`

Finding:

```txt
F9c remains promising, but should not be implemented as live runtime yet.
```

Reason:

```txt
The current repository already has candidate market lists and dirty-market lists, so a verifier should start market-first and candidate-first, not as a world-location rolling verifier.
```

Target first probe:

```txt
Debug-only market slicing probe:
- count world markets;
- count candidate/relevant/promoted markets;
- verify deterministic fixed slices;
- prove dirty markets skip every_location_in_market entirely.
```

Guardrails:

```txt
- No stock mutation.
- No live gameplay dependency.
- Prove coverage stability after save/reload and one monthly tick before promotion.
```

Expected next branch:

```txt
probe/q8-f9c-market-slicing
```

### Q8.7 / F7 — Native global market-local pass

Classification: `PROBE_FIRST`

Finding:

```txt
The current market-local dispatcher is logically market-owned but physically entered through country monthly pulse and every_market_center_in_country.
```

Current safe workaround:

```txt
monthly_country_pulse(country)
  -> every_market_center_in_country
       -> process this market once from its market-center owner
```

Target long-term shape:

```txt
monthly orchestration
  -> country preparation pass
  -> global market-local pass using every_market_in_world if safe
  -> country trade-owner pass
  -> validation / reconciliation pass
```

Do not implement live switch yet.

Required first proof:

```txt
A debug-only probe must confirm `every_market_in_world` can run from a safe once-per-month global/none surface and preserve ordering before any runtime switch.
```

Expected next branch:

```txt
probe/q8-global-market-pass
```

## Consolidated implementation order

Recommended order after this baseline audit:

```txt
1. Q8.1 / F3 — gate PR7.1 profile counters.
2. Q8.2 / F2 — audit/probe US-10 aggregate pending-request gating.
3. Q8.3 / F1 — capacity pool stamp.
4. Q8.5 / F9a — dirty-set producer/consumer probe.
5. Q8.6 / F9c — market-sliced verifier probe.
6. Q8.4 / F4 — helper body split only after caller inventory.
7. Q8.7 / F7 — global market-local pass probe only after TECH-01/global monthly entry proof.
```

## Non-goals confirmed for Q8.0

```txt
- No runtime code change.
- No generated-file change.
- No stock mutation.
- No new persistent state.
- No broad monthly world-location scan.
- No switch from market-center owner workaround to every_market_in_world.
```

## Validation

Documentation-only result. Suggested static checks before merging the stacked PR:

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_modeu5_persistent_state.sh
git diff --check
```

Runtime validation is not required for this documentation-only baseline audit.

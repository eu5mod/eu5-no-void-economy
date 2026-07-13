# Q8.1 + Q8.3 — Profile-counter gates and capacity-pool stamp

## Purpose

This stacked PR implements the two Q8.0 follow-ups classified as `IMPLEMENT_NOW`:

```txt
Q8.1 / F3 — gate temporary PR7.1 profiling counters
Q8.3 / F1 — stamp reusable country capacity-pool facts once per country/month
```

The two changes are bundled because both reduce normal monthly hot-path writes/recalculation without changing the economic order:

```txt
US-00 remains before US-10.
Market-specific merchant/trade capacity is still refreshed per country-market.
Stock mutation remains delegated to central stock operators.
```

## Q8.1 — PR7.1 metric gates

### Problem

PR7.1 active-good / pending-request dispatch introduced useful validation counters:

```txt
cbp_pr71_us00_goods_considered
cbp_pr71_us00_goods_processed
cbp_pr71_us00_goods_produced_gate_hits
cbp_pr71_us00_goods_previous_state_hits
cbp_pr71_us10_goods_considered
cbp_pr71_us10_pending_request_hits
cbp_pr71_us10_requests_processed
```

Those counters are validation/profile state. They are not business state and should not be written unconditionally in normal gameplay.

### Implementation

Adds:

```txt
cbp_pr71_metrics_enabled_trigger
```

The trigger is true only when debug capture or audit mode is enabled:

```txt
cbp_debug_capture_enabled_trigger
OR
cbp_audit_enabled_trigger
```

The PR7.1 generator now gates the reset, preparation, and note helpers behind this trigger.

### Preserved behaviour

The generated business guards still run:

```txt
US-00:
  produced_in_market:<good>
  OR previous US-00 state active

US-10:
  cbp_consumption_<good>_pending_requested_by_market[market] > 0
```

Only metric writes are gated. The heavy helper calls remain controlled by the existing business gates.

## Q8.3 — Country capacity-pool monthly stamp

### Problem

The promoted-market local branch refreshes country-market capacity for every present country before US-00. The existing helper recalculated the country-wide storage capacity pool when the same country could appear in multiple promoted markets in the same monthly cycle.

The market-specific part must remain per country-market:

```txt
scope:cbp_market.merchant_capacity(scope:cbp_country)
```

But the country-wide pool facts can be reused during the same month unless location/rank/capital lifecycle hooks invalidate them.

### Implementation

The public helper now has a stamped wrapper:

```txt
cbp_calculate_country_storage_capacity_pool
```

It delegates to a raw calculator only when needed:

```txt
cbp_calculate_country_storage_capacity_pool_raw
```

Cached scalar facts:

```txt
cbp_capacity_pool_monthly_stamp
cbp_capacity_pool_cached_location_rank_capacity
cbp_capacity_pool_cached_location_count
cbp_capacity_pool_cached_market_count
cbp_capacity_pool_cached_base
cbp_capacity_pool_cached_total
cbp_capacity_pool_cached_location_rank_per_market
```

Owner:

```txt
country scope
```

Lifecycle:

```txt
- rebuilt on first capacity-pool preparation for the country in a given month;
- reused for later country-market capacity refreshes in the same month;
- cleared when the country location-capacity pool is rebuilt.
```

Invalidation surface:

```txt
cbp_rebuild_country_location_capacity_pool
  -> cbp_clear_country_storage_capacity_pool_cache
```

This covers the existing capacity lifecycle path:

```txt
on_location_changed_rank
on_capital_moved
explicit country storage capacity rebuilds
```

### Preserved behaviour

The market-specific capacity record still runs per country-market:

```txt
cbp_apply_country_storage_capacity_pool_to_current_market
  -> reads current market merchant capacity
  -> writes country-market capacity maps
```

The existing promoted-market helper keeps calling the public capacity-pool helper, so the live branch inherits the stamp without duplicating or renaming the promoted-market scripted effect.

## Files changed

```txt
in_game/common/scripted_triggers/cbp_configuration_triggers.txt
in_game/common/scripted_effects/cbp_capacity_effects.txt
tools/generate_pr71_active_good_dispatch_helpers.sh
tools/validate_generators.sh
docs/audits/q8/Q8_1_Q8_3_IMPLEMENTATION.md
```

## Validation expectations

Static validation:

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
```

Optional profile/audit validation:

```txt
Run a monthly profile/debug scenario with debug or audit enabled.
Expected: PR7.1 counters still appear when metrics are enabled.
Normal mode expectation: business guards run, but PR7.1 per-good metric writes are skipped.
```

## Known limitations

```txt
- This PR does not implement Q8.2 aggregate US-10 country-market gating.
- This PR does not implement Q8.5 dirty derived-cache repair.
- This PR does not switch the market-local dispatcher to every_market_in_world.
- Runtime validation still needs to confirm exact EU5 behaviour for the new country-scope scalar cache under save/reload.
```

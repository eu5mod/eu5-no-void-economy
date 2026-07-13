# Q8 / F9c — Deterministic market-sliced verifier probe

## Purpose

This note refines F9 after reviewing the available iterator shapes and the current ModeU5 performance/cache scripts.

The important distinction is:

```txt
Questionable:
  rolling verification over every_location_in_the_world / 30

Potentially profitable, including in Performance Mode:
  market-sliced verification
  -> skip irrelevant markets
  -> skip already dirty markets
  -> inspect locations only for markets that still need verification
```

This is still a future optimisation / probe. It should not change PR146 runtime behaviour.

## Native iterator basis

The relevant engine shapes are:

```txt
every_market_in_world:
  none -> market

ordered_market_in_world:
  none -> market
  supports order_by, position, min, max, check_range_bounds

every_location_in_market:
  market -> location

ordered_in_global_list:
  supports list/variable, order_by, position, min, max, check_range_bounds
```

The important consequence is that a market-first verifier can avoid the blind world-location shape:

```txt
bad shape:
  every_location_in_the_world
    -> location.market
    -> maybe mark market dirty

better shape:
  market slice
    -> if market relevant and not already dirty
       every_location_in_market
         -> verify this market
```

## Current ModeU5 script support

The repository already has several pieces F9c can reuse.

### Performance relevant market list

`cbp_performance_relevant_markets` is a global variable list populated by performance helpers.

Current shape:

```txt
cbp_rebuild_human_relevant_markets:
  clear relevant market list
  every_country:
    limit = { is_ai = no }
    every_market_present_in_country:
      save market
      add market to cbp_performance_relevant_markets if absent
```

Relevant existing helpers:

```txt
cbp_clear_performance_relevant_markets
cbp_mark_performance_relevant_market
cbp_add_country_present_markets_to_performance_relevant_list
cbp_rebuild_human_relevant_markets
```

### Promoted detailed market list

Performance Mode already distinguishes detailed/promoted markets through:

```txt
cbp_detailed_accounting_promoted_markets
cbp_mark_market_detailed_accounting_promoted
cbp_market_detailed_accounting_promoted_trigger
```

This is important because Performance Mode should not verify markets that cannot become detailed or are not human-relevant.

### Dirty market-country cache list

The market-country cache layer already has:

```txt
cbp_market_country_cache_dirty_markets
cbp_mark_market_country_cache_dirty
cbp_mark_current_market_country_cache_dirty
cbp_repair_dirty_market_country_caches
```

The repair path already loops dirty markets:

```txt
every_in_global_list = {
  variable = cbp_market_country_cache_dirty_markets
  save_temporary_scope_as = cbp_market_country_cache_market
  cbp_rebuild_countries_present_in_market = yes
}
```

### Market -> location -> owner rebuild

`cbp_rebuild_countries_present_in_market` already rebuilds the current market work cache with:

```txt
scope:cbp_market_country_cache_market = {
  every_location_in_market = {
    owner ?= {
      save_temporary_scope_as = cbp_market_country_cache_country
      cbp_add_country_to_current_market_country_cache = yes
    }
  }
}
```

That means F9c does not need to invent market-location traversal. It can reuse the existing market-local rebuild/verification pattern.

## Can markets be counted?

There is no confirmed direct `market_count` value in current ModeU5 docs.

However, a probe can count markets manually:

```txt
cbp_f9c_count_world_markets = {
  remove_global_variable = cbp_f9c_world_market_count
  set_global_variable = { name = cbp_f9c_world_market_count value = 0 }

  every_market_in_world = {
    set_global_variable = {
      name = cbp_f9c_world_market_count
      value = {
        value = global_var:cbp_f9c_world_market_count
        add = 1
      }
    }
  }
}
```

The repo already uses this counter style for relevant-market iterations and added-market counts.

Counting alone does not prove deterministic slicing. It only gives a baseline for coverage checks.

## Can markets be split deterministically?

### Possible but not yet proven

`ordered_market_in_world` gives the right syntactic shape:

```txt
ordered_market_in_world = {
  limit = { <triggers> }
  order_by = cbp_f9c_market_order_value
  min = 1
  max = 20
  check_range_bounds = no
  <effects>
}
```

The open question is the `order_by` value.

A valid F9c market order value must be:

```txt
stable across reloads
stable across months
stable after ordinary economic changes
unique or at least deterministic under ties
available in market scope
cheap to compute
```

A direct `market_id`, `market_index`, or equivalent stable numeric value has not yet been confirmed in the ModeU5 matrix.

Therefore, world-market slicing must begin as a probe.

### Fixed generated slices are safer than dynamic slices

Even if a count is available, the safest first implementation is not:

```txt
min = runtime_calculated_start
max = runtime_calculated_end
```

Use generated fixed slice helpers first:

```txt
cbp_f9c_verify_world_market_slice_01
cbp_f9c_verify_world_market_slice_02
...
cbp_f9c_verify_world_market_slice_30
```

Example shape:

```txt
cbp_f9c_verify_world_market_slice_01 = {
  ordered_market_in_world = {
    order_by = cbp_f9c_market_order_value
    min = 1
    max = 20
    check_range_bounds = no
    save_temporary_scope_as = cbp_f9c_market
    cbp_f9c_verify_current_market_if_needed = yes
  }
}
```

The fixed range size can be conservative. The probe then proves coverage by comparing visited markets against the counted world-market count.

## Better Performance Mode variant: slice candidate markets

For Performance Mode, do not start with `ordered_market_in_world`.

Start with existing candidate lists:

```txt
cbp_performance_relevant_markets
cbp_detailed_accounting_promoted_markets
cbp_market_country_cache_dirty_markets
```

Use `ordered_in_global_list` over those lists:

```txt
ordered_in_global_list = {
  variable = cbp_performance_relevant_markets
  order_by = cbp_f9c_market_order_value
  min = 1
  max = 10
  check_range_bounds = no

  save_temporary_scope_as = cbp_f9c_market
  cbp_f9c_verify_current_market_if_needed = yes
}
```

This stacks with Performance Mode because it preserves the main performance principle:

```txt
verify candidate markets, not the world
```

The market verifier should only enter `every_location_in_market` when the current market is still worth checking:

```txt
cbp_f9c_verify_current_market_if_needed = {
  save_temporary_scope_as = cbp_market

  if = {
    limit = {
      NOT = { cbp_f9c_current_market_already_dirty_trigger = yes }
      OR = {
        cbp_market_detailed_accounting_promoted_trigger = yes
        cbp_human_relevant_full_ledger_market_trigger = yes
        cbp_audit_enabled_trigger = yes
      }
    }

    every_location_in_market = {
      cbp_f9c_verify_location_membership = yes
    }
  }
}
```

This is the key difference from a global location verifier.

## Early-exit clarification

A true inner-loop `break` is still not confirmed.

The profitable early-exit shape is therefore market-level, not location-level:

```txt
before entering every_location_in_market:
  if market already dirty:
    skip the whole market-location scan
```

Do not rely on this shape:

```txt
inside every_location_in_market:
  once first drift is found, stop iterating locations
```

The inner-loop body can still guard heavy writes when a market becomes dirty, but the iterator may continue evaluating remaining locations.

Therefore, F9c should optimise by avoiding entire market-location scans for dirty or irrelevant markets.

## Probe sequence

### F9c.1 — World market count probe

```txt
every_market_in_world:
  increment cbp_f9c_world_market_count
```

Expected output:

```txt
ModeU5 F9C COUNT world_markets=<n>
```

### F9c.2 — Ordered world-market slice coverage probe

Generate 30 fixed helpers:

```txt
cbp_f9c_verify_world_market_slice_01
...
cbp_f9c_verify_world_market_slice_30
```

Each helper:

```txt
ordered_market_in_world:
  order_by = cbp_f9c_market_order_value
  min/max = fixed range
  check_range_bounds = no
  mark visited market in debug list
```

Expected proof:

```txt
sum(slice_market_count_01..30) = world_market_count
duplicate_market_visits = 0
missing_market_visits = 0
```

Repeat after:

```txt
save/reload
one monthly tick
market ownership changes if a test can cause them
```

### F9c.3 — Candidate-list slice coverage probe

Rebuild candidate lists:

```txt
cbp_rebuild_human_relevant_markets
```

Then slice:

```txt
ordered_in_global_list over cbp_performance_relevant_markets
```

Expected proof:

```txt
candidate_markets_total > 0
sum(candidate_slice_count_01..30) = candidate_markets_total
duplicate_candidate_visits = 0
irrelevant_world_markets_visited = 0
```

This is the most important Performance Mode probe.

### F9c.4 — Dirty skip probe

Seed dirty markets:

```txt
cbp_mark_market_country_cache_dirty
```

Then run candidate slice verifier.

Expected proof:

```txt
dirty_markets_seen > 0
dirty_markets_location_scans = 0
non_dirty_candidate_location_scans > 0
```

This proves the useful market-level early exit.

## Acceptance criteria

F9c is acceptable only if all required probes prove:

```txt
1. Markets can be counted.
2. Ordered market slices cover all target markets with no duplicates.
3. Slice coverage is stable after save/reload.
4. Slice coverage is stable after at least one monthly tick.
5. Candidate-list slicing visits only relevant/promoted/candidate markets in Performance Mode.
6. Dirty markets skip `every_location_in_market` entirely.
7. Location-level verification remains lightweight: compare / mark dirty / update tested cache state only.
8. No stock mutation occurs in any verifier.
```

## Decision

F9c should be tracked separately from the original world-location verifier.

Recommended classification:

```txt
F9a — dirty-set architecture
  profitable in all modes

F9b — world-location 1/30 verifier
  questionable in Performance Mode

F9c — market-sliced verifier
  promising in Performance Mode if deterministic slicing and dirty-market skipping are proven

F9d — future on_market_change_owner integration
  long-term best outcome; should call the same dirty-market API
```

The best next action is a debug-only F9c probe PR, not a live gameplay change.

The probe should first validate deterministic market slicing and candidate-list slicing. Only after that should it become a live verifier or a foundation for a future `on_market_change_owner` implementation.

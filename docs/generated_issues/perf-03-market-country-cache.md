# PERF-03 - Build Inverse Market-to-Country Cache

Labels: technical-foundation, performance

Related issue: https://github.com/eu5mod/eu5-no-void-economy/issues/60

## User Story

As a ModeU5 maintainer, I want market-driven stock flows to iterate only the
countries present in the target market so that validation, rebuild, and opening
allocation do not scan every country.

## Functional objective

Implement the third performance optimization layer:

```txt
market -> countries present in market -> active/given good
```

The confirmed implementation builds a deduplicated work cache from:

```txt
market -> every_location_in_market -> owner
```

This replaces `market -> every_country` scans in the generated stock source
scanner and CORE-02 opening allocation path.

Runtime testing showed that a market-location scan may include locations whose
`owner` resolves to an invalid country scope. The cache therefore uses guarded
`owner ?= { ... }` traversal and skips locations without a valid owner before
deduplicating country scopes.

## Required scopes / values / effects

| Need | Scope | Method | Status | TECH-01 |
|---|---|---|---|---|
| Market-to-location traversal | market -> location | `every_location_in_market` | CONFIRMED | 123 |
| Location owner country | location -> country | guarded `owner ?= { ... }` scope link | CONFIRMED | 124 |
| Deduplicated current-market country list | global -> country list | `add_to_global_variable_list`, `is_target_in_global_variable_list`, `every_in_global_list`, `clear_global_variable_list` | CONFIRMED | 111, 125 |
| Persistent per-market variable-list owner | market/global keyed list | one persistent country-list per market | NOT_CONFIRMED | 126 |

## Files expected to change

```txt
in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt
in_game/common/scripted_effects/modeu5_core03_succession_effects.txt
in_game/common/scripted_effects/modeu5_performance_effects.txt
tools/templates/modeu5_stock_good_adapter.template.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_perf03_test_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_perf03_debug_events.txt
main_menu/localization/english/modeu5_stock_l_english.yml
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/TEST_PLAN.md
docs/tests/PERF_03_MARKET_COUNTRY_CACHE_RUNBOOK.md
```

## Dependencies

- Stacked after PERF-02 native country-to-market traversal.
- Uses TECH-01 111 global variable-list semantics.
- Uses CORE-01 generated per-good adapters.
- Uses CORE-02 opening-stock initialization and CORE-03 ownership hooks.

## Implementation rules

- Do not mutate stock directly.
- Do not treat the work cache as a stock source.
- Rebuild the current-market country list from location ownership before using
  it in market-driven stock scans.
- Guard owner traversal and skip market locations whose owner is not a valid
  country scope.
- Maintain dirty market markers when location ownership changes.
- Keep full rebuild/repair support by rebuilding the work cache from market
  locations.
- Do not claim a persistent per-market variable-list exists until TECH-01 126
  is confirmed.

## Acceptance criteria

- `modeu5_rebuild_countries_present_in_market` builds a deduplicated country
  list for the saved target market using `every_location_in_market`.
- CORE-01.5/CORE-01.6 source scans use `every_in_global_list =
  modeu5_countries_present_in_market` instead of `every_country`.
- CORE-02 opening allocation eligibility and allocation use the cached country
  list instead of `every_country` / `ordered_country`.
- CORE-03 location ownership changes mark the affected market-country cache
  dirty.
- `modeu5_repair_dirty_market_country_caches` can rebuild all dirty markets and
  clear the dirty list.
- A focused PERF-03 debug event emits dump lines and an explicit
  PASS/BLOCKED/FAIL result.
- A non-territorial market-presence probe compares
  `every_market_present_in_country` against owned-location market coverage and
  reports whether any country-market presence with positive ModeU5 capacity or
  stock would be missed by the location-owner cache.

## Manual test scenario

Run:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Then in a disposable campaign as a country with a capital market, run:

```txt
event modeu5_perf03_debug.1
```

Choose:

```txt
Run market-country cache probe
```

Then run the same event again and choose:

```txt
Run non-territorial market presence probe
```

Review the logs for:

```txt
ModeU5 PERF-03 DUMP market_country_cache ...
ModeU5 PERF-03 RESULT market_country_cache PASS
ModeU5 PERF-03 DUMP nonterritorial_presence ...
ModeU5 PERF-03 RESULT nonterritorial_presence PASS|RISK|BLOCKED ...
```

## Known limitations

The implemented cache is a global work cache for the current market, rebuilt
from `market -> location -> guarded owner` before use. Locations with invalid
owners are ignored because they cannot contribute a valid country stock owner.
It is not a persistent one-variable-list-per-market structure because no
confirmed per-market variable owner or dynamic list-name mechanism exists.
Market-change-specific on_actions are not confirmed; explicit rebuild/repair
remains the supported response until that exposure is confirmed.

The non-territorial market-presence probe is diagnostic. `PASS` means the
tested country did not expose stock-capable non-territorial market presence.
`BLOCKED` means no non-territorial candidate was found. `RISK` means the probe
found a current-country market presence with positive ModeU5 storage capacity
or existing stock that the location-owner cache does not include; in that case
PERF-03 should be extended to merge another confirmed presence source before the
cache is treated as complete for all stock-capable countries.

# PERF-04 - Monthly US-00 Loop Fusion

Labels: technical-foundation, performance

Related issue: https://github.com/eu5mod/eu5-no-void-economy/issues/60

## User Story

As a ModeU5 maintainer, I want the monthly US-00 runtime to traverse a
country's markets once and process all goods inside that market scope so that
the monthly void-economy cycle avoids repeating the same market loop for every
generated good adapter.

## Functional objective

Implement the first safe loop-fusion layer:

```txt
country -> every_market_present_in_country -> all generated goods
```

instead of:

```txt
all generated goods -> country -> every_market_present_in_country
```

This PR deliberately targets only one cadence and one scope:

```txt
monthly US-00 runtime
current country
current country-market relationship
generated per-good US-00 processing helpers
```

It does not merge initialization, dirty validation, full audit, market events,
country ownership events, or good-specific calls into one dispatcher.

## Functional decision

PR #71 / the non-territorial market-presence probe is parked for now. For MVP
performance work, non-owned/non-territorial market presence is accepted as
negligible economic weight and not a blocker for optimizing ordinary
country-owned market loops.

The known risk remains documented:

```txt
if a country can hold meaningful stock or storage capacity in a market where it
owns no location, a location-owner-derived market-country cache may miss it.
```

This PR does not rely on that contested cache for the US-00 monthly loop. It
uses the already confirmed country-driven native iterator
`every_market_present_in_country`.

## Required scopes / values / effects

| Need | Scope | Method | Status | TECH-01 |
|---|---|---|---|---|
| Country-to-market traversal | country -> market | `every_market_present_in_country` | CONFIRMED | 117 |
| Per-good US-00 market processing | country x market x good | generated `modeu5_process_us00_monthly_market_good_<good>` helpers | CONFIRMED | 104, 122 |
| Produced-in-market skip gate | market x good | `produced_in_market:<good>` | CONFIRMED | 122 |
| Non-territorial market-presence edge case | country x market | diagnostic-only deferred probe | TO_TEST | 128 |

## Files expected to change

```txt
tools/generate_stock_good_helpers.sh
in_game/common/scripted_effects/modeu5_stock_goods_generated.txt
docs/generated_issues/perf-04-monthly-us00-loop-fusion.md
docs/generated_issues/perf-03-market-country-cache.md
docs/tests/TEST_PLAN.md
docs/tests/US_00_VOID_ECONOMY_PIPELINE_RUNBOOK.md
```

## Dependencies

- Depends on PERF-02 confirmation of `every_market_present_in_country`.
- Depends on US-00 monthly market-good helpers.
- Depends on PERF-01 zero-work gates to keep each good cheap when no production
  or prior record exists.

## Implementation rules

- Do not change US-00 arithmetic.
- Do not change stock mutation effects.
- Do not remove single-good monthly helpers; they remain useful for tests and
  future good-specific events.
- Fuse only the monthly all-goods dispatcher because it has one cadence, one
  country scope, and one market traversal.
- Keep validation, initialization, audit, and event-driven loops separate.
- Treat PR #71 non-territorial analysis as deferred; do not hide the risk.

## Acceptance criteria

- `modeu5_run_us00_monthly_pipeline_all_goods` loops
  `every_market_present_in_country` once for the current country.
- The generated `modeu5_process_us00_monthly_market_all_goods` helper runs all
  per-good US-00 market processors inside the saved `modeu5_market` scope.
- Existing `modeu5_run_us00_monthly_pipeline_good_<good>` wrappers remain
  available.
- US-00 controlled and monthly runtime tests keep their existing expected dump
  semantics.
- Generated adapters are regenerated and package validation passes.
- Issue #60 is updated with the loop-fusion rule:

```txt
fuse loops only when scope, cadence, ordering, and cache source are identical
```

## Manual test scenario

Run:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Then in a disposable campaign:

```txt
wait until CORE-02 initialization has completed
event modeu5_us00_debug.1
choose "Run US-00 controlled pipeline test"
wait 2 days
event modeu5_us00_debug.1
choose "Run US-00 monthly runtime smoke test"
```

Review:

```txt
ModeU5 US-00 DUMP controlled_e2e ...
ModeU5 US-00 RESULT controlled_e2e PASS
ModeU5 US-00 DUMP monthly_runtime ...
ModeU5 US-00 RESULT monthly_runtime PASS
```

## Known limitations

This PR does not add active-good lists, active-market lists, or a durable
per-market country cache. It reduces repeated market traversal in one confirmed
monthly path. Wider market-first runtime refactors remain separate performance
work.

Non-owned/non-territorial market presence remains a documented risk and may
need a future cache supplement if logs later show meaningful stock/capacity in
those relationships.

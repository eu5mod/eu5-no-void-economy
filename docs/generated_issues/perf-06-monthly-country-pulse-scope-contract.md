# PERF-06 - Monthly Country Pulse Scope Contract And Seen-Market Registry

Labels: technical-foundation, performance, module:core

Related issue: https://github.com/eu5mod/eu5-no-void-economy/issues/60

## User Story

As a ModeU5 maintainer, I want monthly country-pulse handlers to reuse the
current country scope and record markets already seen in the current cycle so
that ModeU5 can separate country-owned work from future deduplicated
market-owned work.

## Functional objective

Correct the monthly runtime scope contract:

```txt
monthly_country_pulse = one invocation per country
```

Therefore the monthly ModeU5 runtime already starts in country scope:

```txt
current pulse country -> markets present in country -> goods
```

It must not be documented or implemented as:

```txt
market -> country -> goods
```

and it must not accidentally become:

```txt
country pulse -> market/good work -> every_country controller selection
```

Add a cycle-scoped registry:

```txt
modeu5_monthly_markets_seen_this_cycle
```

The registry is populated while the country-owned monthly pass runs:

```txt
current pulse country
  -> every_market_present_in_country
    -> mark market seen for this month
    -> run all generated goods for that country-market tuple
```

The registry may be used for future market-owned monthly tasks that should run
once per market. It must not skip country-owned stock, capacity, production, or
ledger work: two countries in the same market still have two distinct
country-market-good records.

## Required scopes / values / effects

| Need | Scope | Method | Status | TECH-01 |
|---|---|---|---|---|
| Monthly country pulse scope | none -> country | `monthly_country_pulse` | CONFIRMED | 011 |
| Country-to-market traversal | country -> market | `every_market_present_in_country` | CONFIRMED | 117 |
| One-per-month reconciliation guard | global variable system | `modeu5_last_monthly_reconciliation_stamp` | CONFIRMED | 112 |
| Reconciliation controller scope | country | preselected current pulse country; fallback `every_country` only outside country scope | CONFIRMED | 001, 011 |
| Monthly seen-market registry | country -> market; global -> market | `modeu5_monthly_markets_seen_this_cycle` with `add_to_global_variable_list`, `is_target_in_global_variable_list`, `clear_global_variable_list` | CONFIRMED | 130 |

## Files expected to change

```txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
tools/generate_stock_good_helpers.sh
docs/technical/TECH-01_engine_exposure_matrix.md
docs/generated_issues/us-11-reconciliation-et-coherence-de-la-double-comptabilite.md
docs/generated_issues/perf-05-reduce-global-market-scans.md
docs/generated_issues/perf-06-monthly-country-pulse-scope-contract.md
docs/tests/PERF_05_REDUCE_GLOBAL_MARKET_SCANS_RUNBOOK.md
```

## Dependencies

- Depends on TECH-01 011 confirming that `monthly_country_pulse` changes scope
  to each country.
- Depends on PERF-04 for the fused US-00 monthly
  `country -> every_market_present_in_country -> goods` dispatcher.
- Depends on PERF-05 for active/dirty reconciliation paths and deterministic
  US-11 tests.
- Uses TECH-01 130 for the monthly seen-market registry.

## Implementation rules

- Do not change stock arithmetic.
- Do not mutate stock outside CORE-01 operators.
- Do not remove the global controller fallback required by initialization,
  audit, and debug entry points that may not already be in country scope.
- When reconciliation is called from the monthly country pulse, save the current
  scope as `modeu5_reconciliation_controller` before invoking validation.
- `modeu5_prepare_reconciliation_controller` must preserve a preselected
  controller and only use `every_country` when no controller exists.
- Documentation must describe `monthly_country_pulse` as the outer country loop.
- The seen-market registry is a scheduling/diagnostic index, not a stock source.
- Do not use the seen-market registry to skip country-owned market/good work.

## Acceptance criteria

- Monthly stock reconciliation preselects the current pulse country before dirty
  validation.
- `modeu5_prepare_reconciliation_controller` no longer scans `every_country`
  when a controller was already provided.
- Fallback controller discovery still works for initialization/manual audit
  contexts where no country scope was preselected.
- TECH-01 and US-11 documentation explicitly state that country pulses already
  iterate countries.
- PERF-05 documentation no longer implies that monthly runtime starts from a
  global market loop.
- The generated monthly all-goods dispatcher marks each reached market through
  `modeu5_mark_monthly_market_seen` before processing goods.
- `modeu5_monthly_markets_seen_this_cycle` resets once per calendar month.
- Duplicate market encounters increment diagnostics but do not suppress
  country-owned processing.

## Manual test scenario

Run:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Then in a disposable campaign as any country:

```txt
wait until CORE-02 initialization has completed
wait one monthly tick
event modeu5_debug.1
choose "Test US-11 dirty-record reconciliation"
```

Expected:

```txt
ModeU5 US-11 RESULT reconciliation PASS
```

The US-11 dumps should show nonzero dirty and active reconciliation values for
the deterministic corruption/repair phases.

For a monthly runtime smoke test, inspect these diagnostic variables when debug
capture is available:

```txt
modeu5_monthly_markets_seen_new_count
modeu5_monthly_markets_seen_duplicate_count
```

## Known limitations

This PR fixes controller selection, documentation, and the first seen-market
registry. It does not complete the future structural runtime target of fully
market-first processing:

```txt
active market -> cached countries_present_in_market -> active goods
```

That remains a separate optimization layer because `monthly_country_pulse`
itself is country-scoped by engine design.

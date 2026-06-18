# PERF-02 Native Relationship Traversal Runbook

## Scope

This runbook validates the first native relationship traversal refactor from
issue #60:

```txt
country -> every_market_present_in_country -> goods
human country -> every_market_present_in_country -> relevant market list
```

It does not validate the future inverse `market -> countries_present_in_market`
cache.

## Build And Install

Run from the repository root:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Scenario A - Source Validation

Expected:

```txt
Generated adapters contain modeu5_recalculate_saved_country_market_storage_capacities.
The shared country storage-capacity wrapper uses every_market_present_in_country
as the outer loop and goods as the inner generated calls.
validate_module_packages.sh passes.
```

## Scenario B - Native Iterator Probe

Setup:

```txt
Start a disposable campaign as a country with at least one market.
Run:

event modeu5_perf02_debug.1
```

Expected:

```txt
The result is PASS.
Native market iterations is greater than zero.
Relevant markets added is greater than zero.
Owned-location markets missing from native list is zero.
No ModeU5 PERF-02 error appears in error.log.
```

Visible dump fields:

```txt
Country scopes scanned
Native market iterations
Relevant markets added
Owned-location markets
Owned-location markets missing from native list
```

## Scenario C - Relevant Market List Sanity

Setup:

```txt
Run the same probe from a human-controlled country.
```

Expected:

```txt
modeu5_performance_relevant_markets is populated through native market traversal
for the current country.
The list is deduplicated.
The list is not used as a stock source.
```

## Logs To Inspect

```txt
error.log
game.log
system.log
debug.log when deterministic dumps are emitted there
```

## Known Limitations

This probe validates the important lower-bound edge case: markets of owned
locations must not be omitted by `every_market_present_in_country`.

It does not yet validate all possible “country present in market” meanings,
such as market access without owned locations, market reassignment, foreign
building ownership, market splits, or save migration. Later performance PRs
must test those cases before replacing market-driven scans with sparse cached
relationships.

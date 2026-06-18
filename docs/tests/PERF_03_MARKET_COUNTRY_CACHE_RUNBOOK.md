# PERF-03 Market-Country Cache Runbook

## Purpose

Validate that ModeU5 can derive a market-driven country list without scanning
all countries:

```txt
market -> every_location_in_market -> owner -> deduplicated country list
```

This runbook validates the work-cache implementation used by generated
validation/rebuild and CORE-02 opening allocation paths.

## Local install

From the repository root:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## In-game procedure

Start a disposable campaign with the Core and Core Tests packages enabled.

Open the console as a country with a capital market and run:

```txt
event modeu5_perf03_debug.1
```

Choose:

```txt
Run market-country cache probe
```

## Expected result

The result event should show:

```txt
PASS - Market-country cache includes the current country
```

The logs should contain:

```txt
ModeU5 PERF-03 DUMP market_country_cache locations_scanned=...
ModeU5 PERF-03 RESULT market_country_cache PASS
```

`locations_scanned` and `countries_present` must both be greater than zero.
`current_country_present` must be `1`.

## Log review

Review:

```txt
error.log
game.log
system.log
debug.log when enabled
```

The PASS decision must be based on the log dump/result lines, not only on the
localized result event.

## Known limitations

This validates the current-market work cache. It does not prove a persistent
one-list-per-market storage model because that exposure remains
`NOT_CONFIRMED` in TECH-01. It also does not validate a dedicated market-change
on_action; market reassignment remains covered by explicit rebuild/repair until
an engine hook is confirmed.

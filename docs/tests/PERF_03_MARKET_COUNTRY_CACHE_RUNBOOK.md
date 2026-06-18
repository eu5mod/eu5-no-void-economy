# PERF-03 Market-Country Cache Runbook

## Purpose

Validate that ModeU5 can derive a market-driven country list without scanning
all countries:

```txt
market -> every_location_in_market -> owner -> deduplicated country list
```

This runbook validates the work-cache implementation used by generated
validation/rebuild and CORE-02 opening allocation paths.
Market locations without a valid country owner are skipped through guarded
owner traversal.

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

Run the same event again and choose:

```txt
Run non-territorial market presence probe
```

## Expected result

The result event should show:

```txt
PASS - Market-country cache includes the current country
```

The logs should contain:

```txt
ModeU5 PERF-03 DUMP market_country_cache locations_scanned=...
ModeU5 PERF-03 DUMP market_country_cache ... locations_with_owner=...
ModeU5 PERF-03 RESULT market_country_cache PASS
ModeU5 PERF-03 DUMP nonterritorial_presence native_markets=... nonterritorial_with_capacity=... nonterritorial_with_stock=... total_capacity=... total_stock=...
ModeU5 PERF-03 RESULT nonterritorial_presence PASS|RISK|BLOCKED ...
```

`locations_scanned`, `locations_with_owner`, and `countries_present` must all be
greater than zero. `current_country_present` must be `1`.

`locations_scanned` may be greater than `locations_with_owner`; this is valid
when the market contains locations whose owner resolves to no valid country.

For the non-territorial presence probe:

- `PASS` means no stock-capable non-territorial market presence was found for
  the tested country.
- `BLOCKED` means the country has no non-territorial market candidate, so the
  risk could not be exercised in that scenario.
- `RISK` means a market from `every_market_present_in_country` has no owned
  location for the current country, has positive ModeU5 storage capacity or
  existing ModeU5 wheat stock, and the location-owner cache does not include
  the current country. Treat that as a design follow-up signal, not as a stock
  mutation failure.

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

The non-territorial presence probe does not repair the cache. If it reports
`RISK`, follow-up work must confirm and merge an additional country-presence
source before market-driven stock flows rely on PERF-03 as a complete list of
stock-capable countries.

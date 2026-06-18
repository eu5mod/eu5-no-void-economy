# US-00 Void Economy Pipeline Runbook

## Scope

This runbook validates the first implementable US-00 layer:

```txt
US-00.1 ledger helper
US-00.2 overproduction ratio and buffer
US-00.3 stored next-cycle production penalty
US-00.4 void wealth and taxable-income proxy
PROBE-021 location output exposure
```

The controlled pipeline test does not yet wire live monthly production into
gameplay. TECH-01 021 must pass before monthly production ingestion can depend
on vanilla `goods_output`.

## Build And Install

Run from the repository root:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Scenario A - PERF-02 Prerequisite

Setup:

```txt
Start a disposable campaign as a country with at least one market.
Run:

event modeu5_perf02_debug.1
```

Expected:

```txt
ModeU5 PERF-02 RESULT native_iterator PASS
missing_owned_location_markets = 0
```

This confirms the country-driven native market traversal used by the current
branch remains valid before running US-00 probes.

## Scenario B - PROBE-021 Location Output Exposure

Setup:

```txt
Run:

event modeu5_us00_debug.1

Choose "Run PROBE-021 location output probe".
```

Expected:

```txt
debug.log contains:
ModeU5 PROBE-021 DUMP location_output country=FRA good=wheat ...
ModeU5 PROBE-021 RESULT location_output PASS
```

`PENDING no_positive_wheat_output` means the candidate syntax loaded and ran,
but the selected country did not expose positive wheat output through the probe.
Inspect `error.log`; if there is no script-system error, retest with a more
suitable producing country before wiring live gameplay.

`FAIL missing_FRA` means the campaign or bookmark does not expose `c:FRA`.

Visible dump fields:

```txt
owned locations scanned
positive wheat-output locations
wheat goods_output total
raw-material output total
```

## Scenario C - Controlled US-00 Pipeline

Setup:

```txt
Run:

event modeu5_us00_debug.1

Choose "Run US-00 controlled pipeline test".
```

The test uses FRA's capital market and wheat. It clears the controlled wheat
fixture, sets wheat capacity to 40, attempts to add 100 wheat through
`modeu5_add_stock` with enforced capacity, records the returned add/reject
outputs, then calculates the US-00 ratios, void wealth, taxable proxy, and
stored next-cycle production penalty.

Expected:

```txt
produced = 100
added = 40
rejected = 60
overproduction ratio = 0.60
effective ratio = 0.59
void wealth = 120
taxable proxy = 120
production penalty = -0.59
market void wealth = 120
total void wealth = 120
stock after = 40
capacity = 40
```

Expected log lines:

```txt
ModeU5 US-00 DUMP controlled_e2e country=FRA good=wheat ...
ModeU5 US-00 RESULT controlled_e2e PASS
```

The test cleans up the controlled stock and US-00 record after writing the dump.
Use the dump lines, not the post-cleanup maps, as the validation artifact.

## Logs To Inspect

```txt
error.log
game.log
system.log
debug.log
```

Known tolerated assertion:

```txt
Tried to localize with localization disabled
```

Tolerate it only when the expected `ModeU5 US-00 DUMP` / `ModeU5 PROBE-021 DUMP`
and matching `RESULT` lines are present, and there is no ModeU5 script-system
error.

## Known Limitations

Live monthly production ingestion remains blocked by TECH-01 021 until the
location-output probe confirms the exact syntax and ownership semantics. The
stored US-00.3 penalty is a theoretical next-cycle value in this PR; applying it
to producing locations is deferred until the producing-location exposure is
confirmed and tested.

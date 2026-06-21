# US-10.0 Stock Demand Resolver Console Test Runbook

## Purpose

This test proves that `modeu5_resolve_stock_demand` builds eligible
candidates, excludes invalid stocks before scoring, orders valid candidates
deterministically, exposes diagnostics, and never mutates stock.

## Before starting EU5

Close EU5, then run:

```bash
./tools/generate_stock_good_helpers.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Confirm that every installed `MODEU5_SOURCE.txt` points to this repository,
branch, and commit.

In the launcher:

```txt
Enable: No Void Economy / modeu5_core
Enable for this validation run only: No Void Economy Tests / modeu5_core_tests
```

Start a clean 1337 campaign where FRA and ENG exist and share at least one
market through the FRA capital market fixture used by the probe.

## Console test

Enter:

```txt
event modeu5_us10_debug.1
```

Select:

```txt
Run US-10.0 resolver ordering test
```

The result event must display:

```txt
PASS - Resolver ordering and non-mutation checks succeeded
```

## Expected debug output

Inspect `game.log` for:

```txt
ModeU5 US-10.0 DUMP eligible=... excluded=... total_available=... first_score=...
ModeU5 US-10.0 RESULT resolver PASS
```

Expected properties:

```txt
eligible candidates >= 2
total available stock >= 90 after seeding FRA +40 and ENG +50 wheat
FRA ordered ahead of ENG because own_country_bonus is highest
FRA and ENG stocks remain unchanged by the resolver call itself
```

## Known limitations

Runtime validation still needs to confirm `opinion:` and
`merchant_power_in_market:` value syntax inside score calculation. If either
value form fails in-game, update TECH-01 and adjust the score helpers before
US-10.1/US-10.2 consume the resolver output.

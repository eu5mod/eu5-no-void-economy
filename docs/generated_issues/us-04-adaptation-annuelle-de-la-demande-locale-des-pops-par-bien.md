# US-04 — Annual local Pop demand adjustment

Labels: `blocked:engine-exposure`, `module:economy`

## User story

As a player, I want actual Pop demand in each location to adapt slowly after a full year of availability or shortage.

## Target loop

```txt
vanilla Pop requested demand
  -> monthly satisfied / shortage outcomes
  -> yearly location × good coefficient adjustment
  -> monthly ModeU5 reconciliation while vanilla demand is not dynamically mutable
```

## Runtime state

Persistent owner:

```txt
location
```

Persistent key/value:

```txt
modeu5_pop_demand_multiplier[goods:<good>] = coefficient
modeu5_us04_reconciliation_coefficient[goods:<good>] = active ModeU5 coefficient
modeu5_us04_reconciliation_requested_quantity[goods:<good>] = last monthly input
modeu5_us04_reconciliation_extra_quantity[goods:<good>] = requested × max(0, coefficient - 1)
modeu5_us04_reconciliation_removed_quantity[goods:<good>] = stock actually removed
modeu5_us04_reconciliation_unsatisfied_quantity[goods:<good>] = extra demand not removed
modeu5_us04_reconciliation_charge_proxy[goods:<good>] = removed × market price
```

`modeu5_pop_demand_multiplier` is retained as archived PR69 probe state.
Runtime gameplay uses `modeu5_us04_reconciliation_coefficient`.

## Safety invariant

```txt
1.20 = explicit one-time initialized saved state
1.00 = disabled, missing, uninitialized, or invalid fallback
```

A missing record must never silently recreate the `1.20` baseline outside the
versioned initialization path.

## One-time initialization

After the existing one-day campaign-start delay, ModeU5 records the schema
version and then initializes owned locations lazily from country scope. Runtime
probes showed that a root-scope `every_location` initializer is not safe enough
to be the production path.

```txt
if global modeu5_us04_multiplier_initialization_version is missing or < 1:
    mark initialization version = 1

on country monthly/yearly preparation:
    if country modeu5_us04_country_multiplier_initialization_version is missing or < 1:
        every_owned_location
          -> every supported good helper
             -> missing key: write 1.20
             -> existing key: preserve value
        country initialization version = 1
```

The version gate is saved globally and per initialized country. Reloading a
campaign does not apply `1.20` again to already-initialized country-owned
locations, while newly encountered owned locations can still be initialized by
the country-scoped path.

## Yearly adjustment

Only an existing record may be changed:

```txt
12 satisfied / 0 shortage -> current × 1.01
0 satisfied / 12 shortage -> current × 0.99
mixed year                -> no write
zero-observation year     -> no write
missing multiplier key    -> no write
```

Annual counters reset after the decision reads them.

## Vanilla integration status

ModeU5 must not copy or regenerate Paradox's `pop_demand` formulas because
those formulas may change between minor and major EU5 versions.

PR #69 probes determined that EU5 1.2+ does not expose a reliable script path
to update engine `pop_demand × good` dynamically during a campaign.

Historical injection and replacement probes remain archived under:

```txt
docs/audits/pr69/
```

The old experimental coefficient remains initialized and updated, but US-04
must not claim that the engine consumes it.

## Temporary reconciliation strategy

Until a dynamic local Pop-demand endpoint exists, US-04 reconciles the ModeU5
extra demand after US-10.3 has recorded Pop requested quantities.

```txt
requested_quantity = modeu5_pop_demand_requested_quantity[goods:<good>]
extra_quantity = requested_quantity × max(0, modeu5_us04_reconciliation_coefficient - 1)
```

The extra quantity is consumed through:

```txt
modeu5_remove_stock(reason = consumption)
```

This single centralized call updates both country × market × good stock and
the market × good aggregate/cache.

The charge side is currently a proxy only:

```txt
charge_proxy = actual_removed_quantity × market_price(goods:<good>)
```

No confirmed estate-specific script effect exists yet, so the proxy is recorded
for diagnostics and future US-04-UI work rather than charged to a live estate.

## Compatibility cleanup

`generate_all.sh` deletes obsolete local artifacts from the abandoned exact-path
vanilla generator:

```txt
packages/modeu5_economy_rebalance/in_game/common/goods_demand/pop_demands.txt
packages/modeu5_economy_rebalance/in_game/common/script_values/
modeu5_us04_pop_demand_values_generated.txt
```

This prevents a stale exact-path override or duplicate production value from
entering a local install.

## Runtime validation

Use a clean new campaign and let at least one full in-game day pass.

Run:

```txt
event modeu5_us04_debug.1
```

### Adaptation and reconciliation fixture

Expected:

```txt
base_multiplier=1.2000
wheat_multiplier=1.2120
wheat_reconciliation_coefficient=1.2120
beer_reconciliation_coefficient=1.1880
cloth_reconciliation_coefficient=1.2000
tools_reconciliation_coefficient=1.2000
wheat_reconciliation_requested=100.00
wheat_reconciliation_extra=21.20
wheat_reconciliation_removed=21.20
wheat_stock_after_reconciliation=178.80
PASS
```

### Initialization lifecycle

Expected:

```txt
version=1
wheat=1.2000
beer=1.2000
second initialization call is idempotent
deleted wheat key is not recreated
missing fallback=1.0000
PASS
```

## Archived PR69 probes

The following probe families are retained as historical evidence only:

```txt
event modeu5_us04_debug.1
event modeu5_us04_q9_debug.1
```

They must not be used as acceptance criteria for production integration.

## Static validation

```txt
tools/validate_us04_pop_demand_architecture.py
```

The validator rejects:

```txt
- exact-path vanilla pop_demands.txt override;
- vanilla formula generator;
- copied wheat value formula;
- treating PR69 injection/replacement probes as production integration;
- 1.20 read fallback;
- missing-record yearly recreation;
- missing initialization gate.
```

## Accepted annual fixture

Previously validated:

```txt
1.2000 -> 1.2120 after full satisfaction
1.2000 -> 1.1880 after full shortage
mixed and zero-observation unchanged
annual counters reset
```

## Accepted temporary reconciliation fixture

Validated by the deterministic probe:

```txt
requested=100
coefficient=1.212
extra=21.20
stock 200 -> 178.80
```

## Acceptance criteria

- [x] Versioned one-time `1.20` initializer implemented.
- [x] Missing-state live fallback is `1`.
- [x] Yearly runtime changes existing records only.
- [x] Exact-path vanilla regeneration removed.
- [x] PR69 injection/replacement probes archived as non-production evidence.
- [x] Active reconciliation coefficient implemented.
- [x] Monthly ModeU5 stock reconciliation implemented through centralized stock removal.
- [x] Stale override cleanup implemented.
- [x] Static architecture validator implemented.
- [ ] New-campaign initialization probe passes.
- [ ] Live US-10.3 location outcome handoff is confirmed.
- [ ] Estate-specific charge endpoint is confirmed.
- [ ] Exact live Pop/Estate requested demand per estate is confirmed.

## Current status

```txt
Annual adaptation fixture:             PASS
Temporary stock reconciliation:        IMPLEMENTED / RUNTIME PENDING
Vanilla pop_demand mutation:           REJECTED FOR PRODUCTION
Estate-specific charge:                NOT_CONFIRMED / proxy only
TECH-01 #039:                          NOT_CONFIRMED
```

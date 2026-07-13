# US-04 — Annual local Pop demand adjustment

Labels: `module:economy`, `engine-exposure:proxy`

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
modeu5_us04_reconciliation_country_stock_delta[goods:<good>] = country-market stock decrease
modeu5_us04_reconciliation_market_stock_delta[goods:<good>] = market aggregate stock decrease
modeu5_us04_reconciliation_estate_charge[goods:<good>] = positive estate charge amount
modeu5_pop_demand_requested_quantity_<estate>[goods:<good>] = estate-specific monthly requested quantity
modeu5_us04_reconciliation_estate_requested_total[goods:<good>] = estate-specific requested quantity total
modeu5_us04_reconciliation_estate_charge_<estate>[goods:<good>] = positive charge amount per estate
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
docs/audits/pr69/archives/
packages/modeu5_core_tests_q9/
```

Current PR #69 source of truth:

```txt
docs/audits/pr69/Q5_flux_logique_global.v3.md
```

The old experimental coefficient remains initialized and updated, but US-04
must not claim that the engine consumes it.

## Proxy reconciliation strategy

Until a dynamic local vanilla Pop-demand endpoint exists, US-04 reconciles extra
ModeU5 demand through an explicit ModeU5-owned location Estate proxy. A plain
`location × good` aggregate is still not sufficient because it cannot identify
which estate should pay for the extra consumption, and a fixed fallback Estate is
not a safe production substitute for real local composition.

The target production shape is not a post-US-10 reconciliation competing with
US-10. It is a pre-US-10 additional-demand preparation pass:

```txt
monthly country pulse
  -> current country
  -> every_market_present_in_country as target market
  -> generated per-good US-04 demand-preparation adapter
  -> for each good demanded by Pops in the target market
  -> every_owned_location limited to location.market = target market
```

If the promoted-market dispatcher owns the local monthly branch later, the
equivalent target shape is:

```txt
promoted market shell
  -> target promoted market
  -> rebuild countries_present_in_market
  -> each present country
  -> generated per-good US-04 demand-preparation adapter
  -> for each good demanded by Pops in the target market
  -> that country's owned locations in the target market
```

The documented cheap gate is market-scoped:

```txt
target market = {
  demands_goods_by_pops = goods:<good>
}
```

It is the first fast skip before owned-location and local-estate scans. It
answers whether the market has Pop demand for the good; it does not provide
quantity or estate split.

This fallback rule is global. If the detailed US-04 path cannot enter, the game
keeps vanilla/no ModeU5 additional demand regardless of Normal, Debug, Audit, or
Performance accounting mode. Performance Mode only changes accounting sparsity.

For each `country × market × location × estate × good`, US-04 calculates:

```txt
future direct path, if TECH-01 149 is confirmed:
estate_requested_quantity =
  direct location Estate requested quantity for goods:<good>

current TECH-01 150 proxy path:
estate_requested_quantity =
  modeu5_us04_reconciliation_coefficient(location, good)
  × proxy_estate_size_at_location

estate_extra_quantity =
  proxy_estate_size_at_location
  × max(0, modeu5_us04_reconciliation_coefficient - 1)

total_extra_quantity =
  sum(estate_extra_quantity for all estates)
```

Then US-10, or a US-10-compatible central demand resolver, should consume the
request through:

```txt
modeu5_remove_stock(reason = consumption)
```

That centralized call updates both country × market × good stock and the market
× good aggregate/cache. The monthly reconciliation record stores requested,
extra, removed, unsatisfied, stock deltas, estate total, and per-estate charge
diagnostics.

The charge side uses the confirmed country-scope vanilla effect:

```txt
add_gold_to_estate = { estate_type = estate_type:<estate> value = -estate_charge }
```

When the proxy records estate-specific extra quantities, US-04 splits the charge
by each estate's share of the additional demand that was actually satisfied:

```txt
actual_removed_quantity =
  satisfied quantity returned by the central stock removal path

estate_actual_quantity =
  actual_removed_quantity
  × estate_extra_quantity
  / total_extra_quantity

estate_charge =
  estate_actual_quantity × market_price(goods:<good>)
```

If US-04 also removes vanilla market supply through `add_goods_supply`, it should
remove the same `actual_removed_quantity`, not the theoretical requested
`total_extra_quantity`, unless a future design explicitly decides that unsatisfied
additional demand should also reduce vanilla supply.

The legacy bridge maps remain diagnostic/test-only:

```txt
modeu5_pop_demand_requested_quantity_peasants_estate
modeu5_pop_demand_requested_quantity_burghers_estate
modeu5_pop_demand_requested_quantity_nobles_estate
modeu5_pop_demand_requested_quantity_clergy_estate
```

These maps are not the production business surface. They are a deterministic
bridge for current tests and documentation of the required per-estate accounting
shape.

The active production proxy maps are:

```txt
modeu5_us04_proxy_estate_size_peasants_estate
modeu5_us04_proxy_estate_size_burghers_estate
modeu5_us04_proxy_estate_size_nobles_estate
modeu5_us04_proxy_estate_size_clergy_estate
```

When no proxy or estate-specific source exists for a location/good, US-04 does
not remove stock and does not charge any estate for that location/good.

PR #69 proved Pop-to-location ModeU5 endpoint access and market-level observed
demand paths. It did not promote a direct vanilla `pop -> pop_demand × good`
read/write expression in TECH-01. PR #167 deliberately avoids that dependency
by using the ModeU5-owned local proxy.

The target runtime shape is:

```txt
for each relevant country × market:
  for each good:
    if target market does not demand goods:<good> by Pops:
      skip this market × good before scanning locations

    for each owned location in market:
      preferred:
        read location x estate x good requested quantity

      proxy candidate:
        modeu5_us04_reconciliation_coefficient(location, good)
        x proxy_estate_size_at_location

      after the location-estate calculation:
        create one additional US-10 demand request from the estate extra quantities
        consume satisfied quantity through modeu5_remove_stock
        adjust vanilla supply and charge estates only for satisfied quantity
```

Do not use raw `pop_size` as a demand proxy and do not fallback to
`peasants_estate`. `proxy_estate_size_at_location` is only acceptable as the
size term of the confirmed `modeu5_us04_reconciliation_coefficient × size`
formula.

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
wheat_reconciliation_requested=121.20
wheat_reconciliation_extra=21.20
wheat_reconciliation_removed=21.20
wheat_reconciliation_unsatisfied=0.00
wheat_stock_after_reconciliation=178.80
wheat_reconciliation_estate_requested_total=121.20
wheat_estate_charge_peasants=>0
wheat_estate_charge_burghers=>0
wheat_estate_charge_nobles=0.00
wheat_estate_charge_clergy=0.00
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

## Accepted proxy reconciliation fixture

Validated by the deterministic probe:

```txt
requested=121.20
coefficient=1.212
extra=21.20
removed=21.20
unsatisfied=0.00
stock 200 -> 178.80
estate charge > 0
```

## Acceptance criteria

- [x] Versioned one-time `1.20` initializer implemented.
- [x] Missing-state live fallback is `1`.
- [x] Yearly runtime changes existing records only.
- [x] Exact-path vanilla regeneration removed.
- [x] PR69 injection/replacement probes archived as non-production evidence.
- [x] Active reconciliation coefficient implemented.
- [x] Monthly ModeU5 reconciliation uses the #167 local-consumption proxy.
- [x] Proxy reconciliation proves country stock, market aggregate, and estate gold mutation occur through confirmed central surfaces.
- [x] Country-scope estate gold charge endpoint is wired for known estates.
- [x] Legacy diagnostic estate split maps remain deterministic/test-only.
- [x] Stale override cleanup implemented.
- [x] Static architecture validator implemented.
- [ ] New-campaign initialization probe passes.
- [ ] Live US-10.3 location outcome handoff is confirmed.
- [x] The #167 local-consumption proxy is confirmed as the active ModeU5-owned runtime calculation.
- [ ] Exact live vanilla Pop/Estate requested demand per estate is confirmed as a future replacement for the proxy.

## Current status

```txt
Annual adaptation fixture:             PASS
Proxy stock reconciliation:            IMPLEMENTED via TECH-01 150
Vanilla pop_demand mutation:           REJECTED FOR PRODUCTION
Estate gold charge effect:             CONFIRMED / wired for proxy reconciliation
Exact vanilla estate demand read:       NOT_CONFIRMED / optional future replacement
TECH-01 #039:                          NOT_CONFIRMED
```

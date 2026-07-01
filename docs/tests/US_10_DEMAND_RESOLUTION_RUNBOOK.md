# US-10 Demand Resolution Runbook

This runbook validates the combined US-10.1, US-10.2, and US-10.3 explicit-request demand-resolution layer.

## Scope

This runbook validates the explicit-request implementation of:

- US-10.1 consumption stock resolution within one market;
- US-10.2 inter-market stock transfer;
- US-10.3 requested / satisfied / unsatisfied outcome tracking.
- US-10.0 bucketed candidate ordering for explicit requests.

This PR does not infer Pop, Estate, or vanilla trade requested quantities from
unconfirmed engine values. Callers pass one requested quantity to the resolver,
and the resolver records whether the request was satisfied or unsatisfied.
The monthly runtime pass can also consume explicit queued
country-market-good requests. A positive `traded_in_market:<good>` value is
logged as a blocked trade signal only; it is not converted into a stock transfer
until an exact vanilla trade quantity exposure is confirmed.

The deterministic in-game scenario and the manual scenarios below use different
fixture stocks, so their expected quantities differ intentionally.

## Install

```bash
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Focused In-Game Test

Start a disposable campaign where France and England exist and have distinct
capital markets. Then run:

```txt
event modeu5_us10_debug.1
```

Choose:

```txt
Run US-10 demand-resolution test
```

Expected result:

```txt
PASS - US-10 demand resolution
```

Expected dump:

```txt
Consumption requested = 160
Consumption satisfied = 140
Consumption unsatisfied = 20
FRA stock after consumption = 0
Ordering foreign candidate count > 0
Ordering own stock after = 0

Trade requested = 100
Trade transferred = 70
Trade unsatisfied = 30
Buyer stock after = 70
Seller stock after = 20
Buyer capacity before transfer = 70
```

The consumption dump is aggregated across two deterministic sub-scenarios:

1. a base request of 100 with FRA stock 80, producing 80 satisfied and 20
   unsatisfied;
2. an ordering request of 60 with FRA stock 40 and at least one other country in
   the same market seeded with wheat. The expected own-stock-after value is 0,
   proving the bucketed resolver consumes own stock before foreign stock.

## Focused Monthly Runtime Integration Test

Start a disposable campaign after ModeU5 initialization has completed. Then run:

```txt
event modeu5_us10_debug.1
```

Choose:

```txt
Run US-10 monthly runtime integration test
```

Expected result:

```txt
PASS - US-10 demand resolution
```

Expected dump:

```txt
ModeU5 TEST ENTERED scenario=us10_monthly_runtime_integration
ModeU5 US-10 DUMP monthly_runtime requested=30 satisfied=30 unsatisfied=0 stock_after=20 processed=1 trade_signals_blocked=...
ModeU5 TEST PASS scenario=us10_monthly_runtime_integration
```

What this proves:

- the monthly input queue `modeu5_consumption_<good>_pending_requested_by_market`
  is read and removed;
- consumption is resolved from ModeU5 country x market x good stock through
  `modeu5_resolve_stock_consumption`;
- the stock mutation still goes through `modeu5_remove_stock`;
- US-10.3 country-market outcome counters are written;
- vanilla market trade signals are observed only as blocked diagnostics unless
  an explicit transfer quantity is available.

## Manual scenario 1 — same-market consumption with bucket order

### Setup

```txt
Market M has consumer country A stock = 40 wheat.
Market M has foreign country B stock = 80 wheat.
A consumer requests 60 wheat in Market M.
```

### Command or event to run

Call:

```txt
modeu5_resolve_stock_consumption = {
  consumer_country = scope:country_a
  market = scope:market_m
  good = wheat
  requested_quantity = 100
}
```

### Expected result

```txt
satisfied_quantity = 60
unsatisfied_quantity = 0
country A stock after = 0
country B is used only after A's own stock is exhausted
modeu5_remove_stock is the only stock mutation effect used
same-market trade income generated = no
transport cost generated = no
trade capacity used = no
```

### Debug output to inspect

```txt
modeu5_debug_last_us10_requested_quantity
modeu5_debug_last_us10_satisfied_quantity
modeu5_debug_last_us10_unsatisfied_quantity
modeu5_debug_last_us10_candidate_count
modeu5_debug_last_us10_excluded_candidate_count
modeu5_debug_last_us10_total_available_candidate_stock
modeu5_debug_last_us10_best_candidate_bucket
modeu5_debug_last_us10_is_intra_market_trade
modeu5_debug_last_us10_trade_income_generated
modeu5_debug_last_us10_transport_cost_generated
modeu5_debug_last_us10_trade_capacity_used
modeu5_debug_last_us10_mutation_effect_called
```

## Manual scenario 2 — Pop outcome tracking

### Setup

```txt
One location L requests 100 wheat through the explicit fallback caller.
The same-market resolver satisfies 75 wheat.
```

### Command or event to run

Call:

```txt
modeu5_resolve_pop_stock_consumption = {
  location = scope:location_l
  consumer_country = scope:country_a
  market = scope:market_m
  good = wheat
  requested_quantity = 100
}
```

### Expected result

```txt
modeu5_pop_demand_requested_quantity[wheat] increases by 100
modeu5_pop_demand_satisfied_quantity[wheat] increases by 75
modeu5_pop_demand_unsatisfied_quantity[wheat] increases by 25
modeu5_pop_demand_unsatisfied_months[wheat] increases by 1
modeu5_pop_demand_satisfied_months[wheat] does not increase for that shortage month
```

## Manual scenario 3 — inter-market transfer

### Setup

```txt
Source market M1 has seller A stock = 60 wheat.
Source market M1 has seller B stock = 30 wheat.
Buyer C in target market M2 has available capacity = 70.
Buyer C requests 100 wheat from M1 to M2.
```

### Command or event to run

Call:

```txt
modeu5_resolve_inter_market_stock_transfer = {
  buyer_country = scope:country_c
  source_market = scope:market_m1
  target_market = scope:market_m2
  good = wheat
  requested_quantity = 100
}
```

### Expected result

```txt
transferred_quantity = 70
unsatisfied_quantity = 30
source market stock decreases by 70
target market stock increases by 70
modeu5_transfer_stock is the only stock mutation effect used
target capacity is enforced
```

### Debug output to inspect

```txt
modeu5_debug_last_us10_source_market
modeu5_debug_last_us10_target_market
modeu5_debug_last_us10_requested_quantity
modeu5_debug_last_us10_transferred_quantity
modeu5_debug_last_us10_unsatisfied_trade_quantity
modeu5_debug_last_us10_candidate_count
modeu5_debug_last_us10_excluded_candidate_count
modeu5_debug_last_us10_total_available_candidate_stock
modeu5_debug_last_us10_mutation_effect_called
```

## Broad Revalidation

The broad chain now includes the US-10 scenario:

```txt
event modeu5_revalidate_debug.1
```

Choose:

```txt
Revalidate main operations
```

After closing EU5:

```bash
./tools/summarize_modeu5_test_logs.sh
```

Expected summary includes:

```txt
ModeU5 TEST ENTERED scenario=us10_demand_resolution
ModeU5 TEST PASS scenario=us10_demand_resolution
Missing expected scenarios: 0
Failed:  0
Blocked: 0
```

## Logs Are Source Of Truth

Review `debug.log`, `error.log`, `game.log`, and `system.log`. The compact
summary is only the first-pass index. A PR validation comment must include the
exact scenario lines and classify any remaining non-blocking noise.

## Known limitations

- US-10.1 and US-10.2 use explicit requested quantities because TECH-01 rows
  056, 086, and 087 are accepted fallbacks rather than confirmed runtime vanilla
  demand or trade quantity reads.
- Runtime vanilla Pop demand quantity is not read yet.
- Exact vanilla trade requested/actual quantity is not read yet.
- Pop/location outcome tracking is validated through the explicit fallback caller
  until live Pop demand exposure is confirmed.
- Candidate mutation is bucket-ordered. Full score-based tie-breaking and
  per-candidate diagnostic dumps remain follow-up work.

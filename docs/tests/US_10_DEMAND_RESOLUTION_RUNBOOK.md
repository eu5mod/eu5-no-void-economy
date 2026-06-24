# US-10 Demand Resolution Runbook

This runbook validates the combined US-10.1, US-10.2, and US-10.3 layer.

## Scope

This PR adds explicit-request demand resolution. It does not infer Pop, Estate,
or vanilla trade requested quantities from unconfirmed engine values. Callers pass
one requested quantity to the resolver, and the resolver records whether the
request was satisfied or unsatisfied.

## Manual scenario 1 — same-market consumption

### Setup

```txt
Market M has country A stock = 40 wheat.
Market M has country B stock = 35 wheat.
A consumer requests 100 wheat in Market M.
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
satisfied_quantity = 75
unsatisfied_quantity = 25
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

## Logs to inspect

```txt
error.log
game.log
system.log
debug.log when deterministic debug events emit dumps
```

## Known limitation

US-10.1 and US-10.2 use explicit requested quantities because TECH-01 rows 056,
086, and 087 are accepted fallbacks rather than confirmed runtime vanilla demand
or trade quantity reads.

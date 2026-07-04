# PR126 PR6.1 — Trade-owner probe runtime fixes

## Purpose

PR6.1 fixes runtime errors observed after PR6 was merged into `developement-balance`.

## Observed issues

The PR6 probe produced:

```txt
Div/0 near common/scripted_effects/modeu5_country_trade_owner_effects.txt
Undefined event target 'modeu5_pr126_trade_owner_target_market'
Undefined event target 'modeu5_target_market'
Invalid right side during comparison 'scope'
Failed to fetch variable for 'modeu5_country_trade_owner_pass_runs'
```

## Root causes

1. The generic trade-owner pass attempted to compute moved goods with:

```txt
trade_volume / traded_goods:transport_cost
```

Runtime testing showed this is not safe from generic trade scope: the scoped goods transport-cost read can evaluate to zero and produce Div/0 spam.

2. The PR6 test market selector could leave the target-market event target unset when the current country did not expose two distinct markets through `every_market_present_in_country`.

3. The blocked-test path did not initialize trade-owner metrics before later comparisons, so guarded assertions could still dereference unset global variables.

## PR6.1 behavior

PR6.1 keeps the native `every_trade` pass diagnostic-only for quantity conversion:

```txt
every_trade
  -> owner
  -> from_market
  -> to_market
  -> traded_goods
  -> trade_volume recorded as diagnostic context
  -> quantity conversion counted as blocked
```

The safe quantity-conversion path remains the generated literal-good helper family:

```txt
modeu5_compute_goods_quantity_from_trade_capacity_good_<good>
```

A future native trade stock-mutating dispatcher must bridge `traded_goods` to a literal generated good adapter before calling the stock-affecting inter-market transfer handlers.

## Test hardening

The PR6.1 test selector now defaults target market to source market on the first candidate and only replaces it when a second market is found. If no second distinct market exists, the test blocks cleanly without dereferencing an unset target.

The test now resets trade-owner metrics before selection so PASS/FAIL/BLOCKED paths can always read initialized globals.

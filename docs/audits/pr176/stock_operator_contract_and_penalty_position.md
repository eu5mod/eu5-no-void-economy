# Stock Operator Contract And Production Penalty Position

## Scope

This assessment covers two risk points raised during the PR-176 stacked review:

- position and quality of `cbp_<good>_production_penalty_modifier`
- explicit vanilla-market side-effect contracts for `cbp_add_stock` and
  `cbp_remove_stock`

## Production Penalty Position

`cbp_<good>_production_penalty_modifier` is a previous-cycle production penalty.
It is generated once per stock good and applied through
`cbp_apply_us00_previous_penalty_good_<good>`.

The current monthly placement is intentional for the implementation that exists
today:

```txt
1. refresh capacity prerequisites
2. apply previous-month production penalties
3. read current vanilla production
4. add stockable production
5. resolve consumption and transfers
6. calculate this-month overproduction
7. store next-month production penalty
```

The modifier does not consume current-month US-04 reconciliation directly. US-04
changes current-month consumption / goods-supply deltas and therefore feeds the
next overproduction calculation. That next overproduction result is stored as
the following month's penalty.

This avoids same-month feedback loops:

```txt
current penalty -> current production -> current stock admission
current consumption / reconciliation -> current overproduction
current overproduction -> next penalty
```

So the static assessment is:

- the modifier is not too early relative to its own source data, because its
  source data is the previous monthly cycle;
- it would be too early only if it tried to use current-month reconciled
  consumption before US-04/US-10 had run;
- current implementation preserves the runtime contract and should not be moved
  after US-04 without redesigning US-00 into same-month recalculation.

## Target Runtime Refinement

A better economic target is to treat the current month's production as staged
until same-month demand has had a chance to consume or transfer it:

```txt
1. refresh capacity prerequisites
2. apply previous-month production penalties
3. read current vanilla production
4. stage/add current production
5. resolve consumption and transfers
6. reject/trim end-of-month excess production
7. calculate this-month overproduction from the rejected excess
8. store next-month production penalty
```

This model is better because it penalizes unsold surplus after monthly demand,
not production that was merely produced before the consumption branch ran.

The step 6 operation should not be implemented as normal consumption/loss
through `cbp_remove_stock`. It needs a dedicated excess-production rejection
surface that:

- preserves country-stock as the source of truth;
- updates the market aggregate through the central operator path;
- records rejected production in US-00 overproduction ledgers;
- does not masquerade as Pop/Estate consumption, decay, or US-20 loss.

That runtime-order redesign is deliberately not included in this stacked PR.
This PR only makes the current stock mutation contract explicit and documents
the safer target shape for a later US-00 runtime-order change.

## Add/Remove Stock Contract

`country_market_good_stock` remains the source of truth and
`market_good_stock` remains the aggregate/cache. Callers must not mutate either
field directly.

The central operators now require an explicit vanilla-market side-effect
decision:

```txt
cbp_add_stock = {
    country = scope:...
    market = scope:...
    good = wheat
    quantity = scope:...
    capacity_policy = enforce
    only_add_at_country_level = yes
}

cbp_remove_stock = {
    country = scope:...
    market = scope:...
    good = wheat
    quantity = scope:...
    reason = consumption
    only_remove_at_country_level = yes
}
```

The flag name means:

```txt
yes = operate only on ModeU5 country x market accounting
      while still keeping the ModeU5 market aggregate/cache synchronized

no  = operate on ModeU5 country x market accounting
      and apply the matching vanilla market add_goods_supply delta
```

It does not mean that the ModeU5 aggregate is skipped. Skipping that aggregate
would violate the ModeU5 invariant:

```txt
market_good_stock = sum(country_market_good_stock)
```

The `no` path is intentionally centralized:

```txt
cbp_add_stock    + only_add_at_country_level = no
  -> add ModeU5 stock
  -> add positive vanilla goods supply equal to actual_added_quantity

cbp_remove_stock + only_remove_at_country_level = no
  -> remove ModeU5 stock
  -> add negative vanilla goods supply equal to actual_removed_quantity
```

US-04 signed consumption/restitution now uses `no`, so the same central stock
operator applies both the ModeU5 country-market delta and the matching vanilla
market-supply delta. Future callsites can switch to `no` only when they want
that vanilla market delta owned by the central stock operator.

Direct `add_goods_supply` calls are restricted to:

```txt
in_game/common/scripted_effects/cbp_stock_effects.txt
packages/cbp_core_tests
```

Runtime features that need vanilla market-supply reconciliation must use either
`cbp_add_stock` / `cbp_remove_stock` with the `no` flag, or a central helper in
`cbp_stock_effects.txt` when there is no country-stock receiver, such as US-20
market-level destination loss on an unpromoted destination market.

## Failure Mode And Static Guard

If the flag is missing or not one of `yes` / `no`, CI fails before the game is
launched. The runtime wrapper also fails closed for invalid selector states
before dispatching to a generated literal-good adapter:

- `cbp_add_stock` returns `cbp_actual_added_quantity = 0`
- `cbp_remove_stock` returns `cbp_actual_removed_quantity = 0`
- the rejected / unsatisfied quantity is preserved
- an `error_log` line is emitted
- the record is marked validation-required

The missing-parameter case is guarded statically through
`tools/validate_cbp_stock_operator_contracts.py`. This is deliberate: EU5
scripted-effect parameter substitution can fail before a scripted default branch
can run, so CI must catch absent fields before the game loads the script.

## Validation Contract

The new static contract validator scans runtime scripts, generated files, test
harnesses, and templates for:

```txt
cbp_add_stock    -> only_add_at_country_level = yes | no
cbp_remove_stock -> only_remove_at_country_level = yes | no
add_goods_supply -> only in cbp_stock_effects.txt or packages/cbp_core_tests
```

Meaning:

```txt
only_add_at_country_level
  Yes = operate at country x market level only
  No  = operate at country x market + vanilla market level

only_remove_at_country_level
  Yes = operate at country x market level only
  No  = operate at country x market + vanilla market level
```

It is also called by `tools/validate_ci_static_contracts.py`, so CI fails if a
future stock mutation callsite omits the explicit contract or bypasses the
central vanilla market-supply operator.

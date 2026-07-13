# US-04 alternative architecture — observed current demand

## Why this exists

The injection syntax matrix tests whether ModeU5 can alter Paradox's `pop_demand` database object without copying vanilla formulas.

That is only one integration family.

There is a second, more version-resilient architecture:

```txt
observe current engine demand
  -> store a ModeU5 demand target
  -> apply annual 0.99 / 1.00 / 1.01 update in ModeU5 stock consumption
```

This avoids changing `pop_demand` at all.

## Difference from the injection architecture

### Injection architecture

```txt
vanilla pop_demand formula
  × persistent location × good coefficient
  -> engine demand
```

The coefficient is a living multiplier:

```txt
1.20
1.212
1.22412
...
```

This requires a hook into the `pop_demand` definition.

### Observed-current architecture

```txt
engine current demand
  -> ModeU5 observed demand target
  -> annual transition factor
  -> ModeU5 stock consumption target
```

The annual multiplier is only the yearly transition:

```txt
shortage year    0.99
neutral year     1.00
satisfied year   1.01
```

The state is not a permanent `pop_demand` multiplier. The state is the current ModeU5 demand target itself.

## Concrete model

For each supported scope:

```txt
market × good
```

or, if a robust country split is available:

```txt
country × market × good
```

store:

```txt
cbp_current_pop_consumption_target[good]
```

Initialization:

```txt
observed_engine_demand = goods_demand_in_market(goods:<good>)
cbp_current_pop_consumption_target[good] = observed_engine_demand × 1.20
```

Yearly update:

```txt
if 12 satisfied / 0 shortage:
    target = target × 1.01

if 0 satisfied / 12 shortage:
    target = target × 0.99

otherwise:
    target unchanged
```

Monthly consumption:

```txt
ModeU5 stock system consumes from country/market stock according to target
```

Vanilla demand remains untouched.

## What this solves

```txt
- no vanilla pop_demand file regeneration;
- no dependency on Paradox formula shape;
- no static database injection dependency;
- no need to reference a hypothetical location.pop_demand.wheat value;
- annual multiplier is exactly 0.99 / 1.00 / 1.01, not a living coefficient.
```

## What this loses or must solve

### Scope

`goods_demand_in_market(goods:<good>)` is market-level demand. It is not location-level Pop demand.

Therefore the clean observed architecture is naturally:

```txt
market × good
```

or:

```txt
country × market × good
```

It is not naturally:

```txt
location × good
```

unless ModeU5 introduces a distribution rule.

### Distribution

If ModeU5 needs country or location consumption, it must distribute observed market demand.

Possible distribution keys:

```txt
- country share of market population;
- country share of owned locations in the market;
- country share of ModeU5 stock demand created by previous cycle;
- human-relevant/accounting-promoted countries only, with market-level fallback.
```

### Vanilla drift

If the target is updated only from its previous target:

```txt
target_next = target_current × annual_factor
```

then it can drift away from vanilla demographic/economic changes.

A safer variant can rebase periodically:

```txt
target_next = observed_engine_demand × learned_preference_factor
```

but that reintroduces a learned factor. This is a design choice.

## Recommended interpretation of "current"

If the intended business rule is:

```txt
current consumption target changes by ±1% per year
```

then the persisted object should be an absolute demand target, not a multiplier.

The annual factor is:

```txt
0.99 / 1.00 / 1.01
```

The stored target is:

```txt
current desired consumption quantity
```

not:

```txt
current pop_demand multiplier
```

## Feasibility evidence already present

The existing disposable probe already reads observed market demand via:

```txt
goods_demand_in_market(goods:<good>)
```

The previous runtime produced, for example:

```txt
wheat current market demand = 54.2594
beer current market demand  = 9.2151
```

So current market demand extraction is feasible.

What remains open is not extraction. The open design question is whether US-04 should:

```txt
A. affect vanilla pop_demand upstream;
```

or:

```txt
B. consume an observed/current ModeU5 demand target downstream.
```

## Proposed next probe

Add a non-injection probe that logs:

```txt
observed_current_demand[good]
initial_target = observed_current_demand × 1.20
satisfied_next = initial_target × 1.01
shortage_next  = initial_target × 0.99
```

Then route one controlled demand resolution through ModeU5 stock removal using `initial_target` instead of vanilla demand mutation.

Acceptance:

```txt
- observed current demand is positive;
- target initialization is observed × 1.20;
- annual transition is exactly 0.99 / 1.00 / 1.01;
- ModeU5 stock consumption uses the target;
- vanilla demand remains unchanged.
```

## Status

```txt
Observed current market demand extraction: FEASIBLE
Downstream ModeU5 target architecture:     NOT IMPLEMENTED
Location × good precision:                 NOT AVAILABLE from observed market demand alone
Injection architecture:                    STILL UNDER TEST
```

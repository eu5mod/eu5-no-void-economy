# US-04 Q11 Pop-demand read probe design — 2026-07-12

## Purpose

Clarify whether any script value/accessor can read an already-computed vanilla Pop demand value for a specific good.

Target question:

```txt
Can the mod read vanilla Pop × good demand directly?
```

Examples of desired-but-unconfirmed accessors:

```txt
pop_demand(goods:wheat)
scope:some_pop.pop_demand(goods:wheat)
demand:pop_demand(goods:wheat)
pop_demand:wheat
```

## Rationale

The wiki documents `pop_demand` as a hardcoded good-demand object in `common/goods_demand` and describes Pop demands as the special good-demand case where script values were accepted.

However, the linked Paradox forum discussion says the wiki is stale for 1.2 behavior and that script-value support in Pop-demand multipliers changed. Therefore Q11 does not assume that scripting `pop_demand` works; it only checks whether read access exists.

## Package

Q11 is isolated in its own optional package:

```txt
packages/modeu5_core_tests_q11
```

This avoids enabling Q9's destructive `REPLACE:pop_demand` candidate while checking read access.

## Console command

```txt
event modeu5_us04_q11_debug.1
```

## Probe families

Q11 includes these read candidates:

```txt
pop_demand(goods:books)
pop_demand(goods:wheat)
demand:pop_demand(goods:books)
demand:pop_demand(goods:wheat)
pop_demand:books
pop_demand:wheat
scope:modeu5_us04_q11_saved_every_pop.pop_demand(goods:books)
scope:modeu5_us04_q11_saved_every_pop.pop_demand(goods:wheat)
```

It evaluates those candidates from several scopes where possible:

```txt
country scope
capital location scope
capital market scope
candidate every_pop scope under capital
candidate random_pop scope under capital
saved-pop dot-chain scope
```

Known-good control:

```txt
goods_demand_in_market(goods:books)
goods_demand_in_market(goods:wheat)
```

The control remains market × good only; it is not Pop × good.

## Interpretation

### Positive evidence

A useful positive result would look like:

```txt
ModeU5 US-04 POP DEMAND READ PROBE q11 candidate=... value=<positive numeric value>
```

The value must be attached to a Pop-scope candidate or an accessor clearly documented/validated as Pop × good.

### Negative evidence

Useful negative evidence includes:

```txt
- parser errors for a candidate syntax
- unknown effect/scope errors for every_pop/random_pop
- zero/null/static values for all Pop-demand candidates while the market control is positive
```

### Ambiguous evidence

A positive value from a country/location/market scope is not enough by itself unless it can be proven to represent Pop × good demand rather than aggregate market demand or a constant.

## Expected next step after runtime logs

After running Q11, add a runtime evidence file:

```txt
docs/audits/pr69/us04_q11_pop_demand_read_probe_runtime_YYYY-MM-DD.md
```

Then update PR #69 status with one of:

```txt
Pop × good vanilla demand read: CONFIRMED
Pop × good vanilla demand read: REJECTED for tested syntax
Pop × good vanilla demand read: AMBIGUOUS
```

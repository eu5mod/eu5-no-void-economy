# US-04 Q11 Pop-demand read probe design — 2026-07-12

## Purpose

Q11 tests whether any candidate syntax can read an already-computed vanilla Pop × good demand value.

This probe is read-only. It does not inject into or replace `pop_demand`.

## Context

External references used when designing the probe:

```txt
https://forum.paradoxplaza.com/forum/threads/modding-request-to-restore-script_value-support-for-pop_demands-multipliers-changed-in-1-2.1921104/#post-31410489
https://eu5.paradoxwikis.com/Goods_modding#Pop_demands
```

The wiki may be stale for EU5 1.2, especially around script-value support inside `pop_demand`. Q11 therefore does not assume Pop-demand scripting works. It tests read access only.

## Package

```txt
packages/cbp_core_tests
```

Console event:

```txt
event cbp_us04_q11_debug.1
```

## Candidate syntaxes

```txt
pop_demand(goods:books)
pop_demand(goods:wheat)

demand:pop_demand(goods:books)
demand:pop_demand(goods:wheat)

pop_demand:books
pop_demand:wheat

scope:saved_pop.pop_demand(goods:books)
scope:saved_pop.pop_demand(goods:wheat)
```

## Scope contexts

```txt
country scope
capital location scope
capital market scope
candidate every_pop scope under capital
candidate random_pop scope under capital
saved-pop dot-chain scope
```

## Control

The probe also logs the known-good market-level demand values:

```txt
goods_demand_in_market(goods:books)
goods_demand_in_market(goods:wheat)
```

These are controls only and do not satisfy Pop × good read access.

## Interpretation rules

```txt
Parser/value error => negative evidence for that syntax.
Positive non-zero value from a real Pop scope => candidate positive evidence.
Market control positive but Pop candidates rejected => no tested Pop-demand read accessor.
```

## Runtime result

Recorded separately in:

```txt
docs/audits/pr69/us04_q11_pop_demand_read_runtime_2026-07-12.md
```

Outcome:

```txt
No tested Q11 syntax can read an already-computed vanilla Pop × good demand value.
```

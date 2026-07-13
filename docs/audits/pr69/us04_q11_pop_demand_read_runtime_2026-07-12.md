# US-04 Q11 Pop-demand read runtime — 2026-07-12

## Purpose

Q11 was added to answer one narrow question:

```txt
Can any tested script-value syntax read an already-computed vanilla Pop × good demand value?
```

This probe is read-only. It does not inject into or replace `pop_demand`.

## Runtime summary

The scenario executed:

```txt
ModeU5 TEST ENTERED scenario=us04_q11_pop_demand_read_probe
ModeU5 TEST PASS scenario=us04_q11_pop_demand_read_probe
```

The `PASS` marker means the probe chain executed. It does **not** mean that any Pop-demand accessor succeeded.

The normal US-04 adaptation scenario remained blocked:

```txt
ModeU5 US-04 RESULT pop_demand_adaptation BLOCKED reason=direct_pop_demand_read_not_confirmed
ModeU5 TEST BLOCKED scenario=us04_pop_demand_adaptation reason=direct_pop_demand_read_not_confirmed
```

## Tested read syntaxes rejected

The engine rejected the direct function-style accessors:

```txt
Failed to find a valid event target link 'pop_demand(goods:books)'
Cannot read [pop_demand(goods:books)] as a script value
Badly read script value pop_demand(goods:books)

Failed to find a valid event target link 'pop_demand(goods:wheat)'
Cannot read [pop_demand(goods:wheat)] as a script value
Badly read script value pop_demand(goods:wheat)
```

The demand-object form was rejected:

```txt
More than one colon in event target link 'demand:pop_demand(goods:books)'
Cannot read [demand:pop_demand(goods:books)] as a script value
Badly read script value demand:pop_demand(goods:books)

More than one colon in event target link 'demand:pop_demand(goods:wheat)'
Cannot read [demand:pop_demand(goods:wheat)] as a script value
Badly read script value demand:pop_demand(goods:wheat)
```

The colon shorthand was rejected:

```txt
Failed to find a valid event target link 'pop_demand:books'
Cannot read [pop_demand:books] as a script value
Badly read script value pop_demand:books

Failed to find a valid event target link 'pop_demand:wheat'
Cannot read [pop_demand:wheat] as a script value
Badly read script value pop_demand:wheat
```

The saved-Pop dot-chain form was rejected:

```txt
Failed to find a valid event target link 'pop_demand(goods:books)'
Cannot read [scope:cbp_us04_q11_saved_every_pop.pop_demand(goods:books)] as a script value
Badly read script value scope:cbp_us04_q11_saved_every_pop.pop_demand(goods:books)

Failed to find a valid event target link 'pop_demand(goods:wheat)'
Cannot read [scope:cbp_us04_q11_saved_every_pop.pop_demand(goods:wheat)] as a script value
Badly read script value scope:cbp_us04_q11_saved_every_pop.pop_demand(goods:wheat)
```

## Positive side finding: Pop scope acquisition works

The runtime errors show that the test did enter real Pop scopes, for example:

```txt
Scope: Pop ... Castilian Catholic Nobles in Valladolid ...
Scope: Pop ... Castilian Catholic Clerics in Valladolid ...
Scope: Pop ... Castilian Catholic Burghers in Valladolid ...
Scope: Pop ... Castilian Catholic Peasants in Valladolid ...
```

This means Pop-scope acquisition via the tested iterator path is not the blocker.

However, Pop scopes and Market scopes do not support `set_variable`, causing noisy but secondary errors:

```txt
set_variable effect [ This scope doesn't support variables. Scope: Market Burgos Market ]
set_variable effect [ This scope doesn't support variables. Scope: Pop ... ]
```

These errors are probe hygiene issues. They do not create a positive Pop-demand read accessor.

## Conclusion

```txt
No tested Q11 syntax can read an already-computed vanilla Pop × good demand value.
```

Supported conclusions:

```txt
- `pop_demand(goods:books)` is not a valid readable script value.
- `pop_demand(goods:wheat)` is not a valid readable script value.
- `demand:pop_demand(goods:<good>)` is not valid syntax.
- `pop_demand:<good>` is not a valid readable script value.
- `scope:saved_pop.pop_demand(goods:<good>)` is not a valid readable script value.
- The engine can enter Pop scopes, but no tested Pop-demand value accessor is exposed there.
```

US-04 status after Q11:

```txt
Direct vanilla Pop × good demand read: REJECTED for tested syntaxes / NOT_CONFIRMED overall
Pop × good read/write integration:     NOT_CONFIRMED
```

Next useful step:

```txt
Either find another documented/undocumented accessor name, or request engine exposure for a Pop × good demand/consumption read surface.
```

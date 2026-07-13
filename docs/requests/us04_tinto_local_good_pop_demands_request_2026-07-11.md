# US-04 Tinto request — local per-good Pop-demand modifiers

Hello Tinto team,

As of the current 1.3 open beta direction, we now have a broad `local_pop_demands` modifier on location scope. This is useful, but it is too broad for dynamic per-good demand systems.

There also appears to be a global per-good Pop-demand modifier family, such as:

```txt
global_<good>_pop_demands
```

Could we get the same per-good modifier family on location scope?

## Requested modifier family

**Available scope:** `location`

**Requested syntax:**

```txt
local_<good>_pop_demands = <value>
```

Examples:

```txt
local_wheat_pop_demands = 0.10
local_books_pop_demands = -0.05
local_furniture_pop_demands = 0.20
```

or, for dynamic use through a unit modifier:

```txt
cbp_books_pop_demand_modifier = {
    local_books_pop_demands = 1
}
```

then at runtime:

```txt
add_location_modifier = {
    modifier = cbp_books_pop_demand_modifier
    size = scope:my_dynamic_books_demand_delta
}
```

The important requirement is that the modifier can be scaled dynamically with `add_location_modifier size = <script value>` and then affect Pop demand for that specific good in that location.

## Why `local_pop_demands` is not enough

A broad modifier such as:

```txt
local_pop_demands = 0.10
```

changes demand for all goods in the location. That is useful for general welfare/consumption effects, but it cannot model substitution, habit formation, shortages, or good-specific consumption adaptation.

For example, if a location has repeated shortages of books but sufficient grain, the mod should be able to reduce only books demand while leaving wheat demand unchanged.

## Use cases

### 1. Dynamic consumption adaptation

A mod can track satisfaction/shortage per good and location, then adjust future demand:

```txt
if books fully satisfied for a year:
    local_books_pop_demands +1%

if books repeatedly unsatisfied for a year:
    local_books_pop_demands -1%

if wheat is stable:
    wheat demand unchanged
```

This requires a per-good local modifier. A broad all-goods modifier cannot express this.

### 2. Country setup / historical starting conditions

On game start, a country or region may have cultural, climatic, or economic consumption differences:

```txt
Mediterranean locations:
    local_olives_pop_demands = +X

Steppe locations:
    local_horses_pop_demands = +Y

Urban printing centers:
    local_books_pop_demands = +Z
```

This would allow historical/regional demand profiles without replacing the whole `pop_demand` object.

### 3. Events and decisions

Events, disasters, reforms, cabinet actions, or infrastructure can affect demand for specific goods:

```txt
Famine relief:
    local_wheat_pop_demands = +X or -X depending on implementation

Literacy reform:
    local_books_pop_demands = +X

Military frontier:
    local_horses_pop_demands = +X
    local_firearms_pop_demands = +Y

Luxury-tax reform:
    local_jewelry_pop_demands = -X
    local_fine_cloth_pop_demands = -Y
```

### 4. Mod compatibility and avoiding fragile replacements

Before 1.2, some mods used dynamic script values inside `REPLACE:pop_demand`. That path no longer appears to provide dynamic runtime demand control.

A location-scoped per-good modifier family would avoid fragile full replacement of the vanilla `pop_demand` object and would be much safer for compatibility between overhaul mods.

## Why this is preferable to restoring full script-value `pop_demand`

Restoring dynamic script values inside `pop_demand` would help, but it encourages full-object replacement and can create conflicts between mods.

A modifier family like:

```txt
local_<good>_pop_demands
```

would be safer because several mods could stack modifiers on the same location and good without replacing the same database object.

## Requested goods coverage

Ideally, this should be generated for all vanilla goods using the same naming convention as existing good-specific modifiers.

Examples:

```txt
local_wheat_pop_demands
local_books_pop_demands
local_furniture_pop_demands
local_wine_pop_demands
local_horses_pop_demands
```

## Minimal acceptance criteria

A modifier should be considered sufficient if this works:

```txt
cbp_books_pop_demand_modifier = {
    local_books_pop_demands = 1
}
```

and this runtime effect changes only books demand in the target location:

```txt
add_location_modifier = {
    modifier = cbp_books_pop_demand_modifier
    size = 0.10
}
```

Expected result:

```txt
books Pop demand in that location changes by +10%
wheat / fish / furniture / other goods remain unchanged
```

A stronger version would also expose a way to read the effective vanilla Pop demand per good before the modifier is applied, but the per-good local modifier alone would already unlock many good-specific demand adaptation systems.

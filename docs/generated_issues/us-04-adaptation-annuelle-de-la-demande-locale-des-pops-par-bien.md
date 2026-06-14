# US-04 — Annual local Pop demand adjustment

Labels: `blocked:engine-exposure`

## User Story

```txt
US-04 — Annual local Pop demand adjustment
```

As a player, I want Pop good demand in each location to adapt slowly after a full year of availability or shortage.

## Functional objective

Track Pop good demand satisfaction at `location × good`.

Adapt actual Pop good demand by changing the good coefficient used by the vanilla `pop_demand` demand definition.

The primary implementation must use the vanilla `pop_demand` goods-demand definition. The per-good coefficient is implemented as a script value evaluated from Pop scope.

Each location has a local Pop-demand adaptation multiplier for each good. All Pops in the same location use the same multiplier for the same good.

Source notes:

- `pop_demand` is the vanilla Pop-demand coefficient surface.
- The vanilla `pop_demands.txt` file states that the hardcoded `pop_demand` checks script values from Pop scope.
- EU5 variable maps support scoped persistent associative storage.
- Location variable-map access from a Pop-scope script value remains prototype-gated.

Target runtime representation, subject to prototype:

```txt
location-scoped variable map:
  name  = modeu5_pop_demand_multiplier
  key   = <goods scope>
  value = numeric multiplier
```

Each `location × good` multiplier entry must be initialized to `1` before use. If missing map entries do not safely resolve to `1`, the script value must provide an explicit fallback.

Representation:

```txt
adapted_pop_demand_coefficient[good] =
    base_pop_demand_coefficient[good]
    × location.variable_map(modeu5_pop_demand_multiplier|good)
```

After 12 satisfied months, multiply the local Pop-demand multiplier by `1.01`.

After 12 unsatisfied months, multiply the local Pop-demand multiplier by `0.99`.

Mixed years and zero-demand years leave the multiplier unchanged. The annual adjustment is multiplicative and compounds over time.

## Runtime position

```txt
Monthly step:
  1. Vanilla evaluates actual Pop good demand through the `pop_demand` demand definition.
  2. The relevant good coefficient is evaluated as a script value from Pop scope.
  3. From Pop scope, the script value resolves the Pop's location.
  4. The coefficient reads the ModeU5 multiplier stored at location × good in a location-scoped variable map.
  5. Adapted Pop good demand is passed to US-10.1 stock resolution.
  6. US-10.3 records requested quantity, removed quantity, and satisfaction ratio.
  7. US-04 updates monthly satisfaction counters for location × good.

Feeds:
  next year's actual Pop demand coefficient through `pop_demand`
```

Example coefficient shape:

```txt
pop_demand = {
    wine = modeu5_pop_demand_coefficient_wine
}
```

Prototype target for coefficient lookup:

```txt
modeu5_pop_demand_coefficient_wine = {
    value = 1

    multiply = {
        desc = "POP_DEMAND_LOCAL_PREFERENCE"
        value = {
            location = {
                value = "variable_map(modeu5_pop_demand_multiplier|goods:wine)"
            }
        }
    }
}
```

If the nested `location = { value = "variable_map(...)" }` form does not parse from Pop-scope script values, the prototype must test equivalent scope-link or saved-scope forms.

Yearly adjustment effect model:

```txt
# Conceptual:
# location.pop_demand_multiplier[wine] *= 1.01
```

Variable maps do not overwrite existing keys when `add_to_variable_map` is called. To update a multiplier, the implementation must remove the old key and re-add the updated numeric value.

Prototype target for yearly multiplier update:

```txt
set_local_variable = {
    name = modeu5_temp_multiplier
    value = "variable_map(modeu5_pop_demand_multiplier|goods:wine)"
}

change_local_variable = {
    name = modeu5_temp_multiplier
    multiply = 1.01
}
```

The exact `goods:wine` event-target syntax must be confirmed by prototype.

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Unmet Pop-relevant need signal | country × market × good | `US-10.3` actual Pop-demand satisfaction outcome, adapted for the US-04 runtime target `location × good`; optional market shortage trigger is diagnostic only | NOT_CONFIRMED | 037 |
| Population/type inputs | location | `num_pop_type`, `percentage_pop_type_in_location`; used only if US-04 needs local debug/reconstruction of Pop demand | CONFIRMED | 038 |
| Modify vanilla demand locally | location × good × Pop context | per-good `pop_demand` script value evaluated from Pop scope, reading a location-scoped variable-map entry such as `"variable_map(modeu5_pop_demand_multiplier|<goods key>)"` | CONFIRMED | 039 |
| Yearly counters | location × good | location-scoped ModeU5 variable maps keyed by goods scope, e.g. `modeu5_pop_demand_satisfied_months` and `modeu5_pop_demand_unsatisfied_months` | CONFIRMED | 040 |
| Yearly pulse | country | `yearly_country_pulse` drives iteration over owned locations and goods to apply yearly adjustment to location-scoped variable-map entries | CONFIRMED | 012 |

### 037 unmet-need prototype

Source of information:

```txt
https://eu5.paradoxwikis.com/Goods_modding#Pop_demands
https://eu5.paradoxwikis.com/Variable#Variable_maps
in_game/common/goods_demand/pop_demands.txt
```

Prototype candidate:

```text
goods_has_unmet_pop_relevant_demand_in_market = {
    # Scope: goods
    # Argument: market = <market scope>

    is_demanded_in_market_by_pops = $market$

    $market$ = {
        goods_demand_in_market = {
            goods = prev

            value > {
                value = goods_supply_in_market(prev)
                add = stockpile_in_market(prev)
            }
        }
    }
}
```

This prototype is only a coarse unmet-need signal. It must not be used as the US-10.1 `requested_quantity`.

For US-04 annual adjustment, the authoritative signal must come from US-10.3:

```txt
location × good requested quantity
location × good removed quantity
location × good satisfaction ratio
```

Market-level shortage alone is not sufficient to adjust a location-local multiplier.

## Files expected to change

```txt
in_game/common/goods_demand/
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/events/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on:
  US-10.1
  US-10.3
  yearly pulse
  TECH-01
  prototype confirming `pop_demand` script values execute from Pop scope
  prototype confirming Pop scope can resolve the Pop's location
  prototype confirming Pop-scope script values can read location-scoped variable maps
  prototype confirming goods scopes can be used as variable-map keys
  prototype confirming numeric variable-map entries can be read, multiplied, removed, and re-added
  prototype confirming dynamic goods iteration can preserve or re-enter the owning location scope

Blocks:
  US-04-UI

Related US:
  US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Apply only to Pop good demand.
- Never apply to building, production, construction, or army demand.
- Use the vanilla `pop_demand` demand definition as the primary coefficient surface.
- Implement each affected good's `pop_demand` coefficient as a script value.
- Evaluate the coefficient from Pop scope.
- Resolve the Pop's location from Pop scope.
- Read the local `location × good` multiplier from a ModeU5 persistent location-scoped variable map.
- The primary multiplier map name is `modeu5_pop_demand_multiplier`.
- The multiplier map key is the goods scope.
- The multiplier map value is a numeric multiplier.
- Initialize every `location × good` multiplier map entry to `1` before it can be read by `pop_demand`.
- If initialization cannot be guaranteed, the coefficient script value must use a safe fallback that returns `1` when the local multiplier map entry is missing or invalid.
- Treat logical `location.pop_demand_multiplier[good]` as design notation.
- Runtime storage should use location-scoped variable maps unless prototype evidence proves they cannot be read safely from `pop_demand` script values.
- Do not rely on undocumented non-map forms such as:
  - `location.var:modeu5_pop_demand_multiplier:wine`
  - `location.var:modeu5_pop_demand_multiplier.var:wine`
  - `modeu5_pop_demand_multiplier(wine)`
  - `modeu5_pop_demand_multiplier(good = wine)`
- Use the documented quoted variable-map lookup form:
  - `"variable_map(modeu5_pop_demand_multiplier|<goods key>)"`
- Do not assume scripted-effect arguments resolve inside quoted variable-map expressions.
- If a dynamic key must be passed into a quoted variable-map expression, save it to a local variable first and use the local variable as the key argument.
- Variable-map names are identifiers and cannot be parameterized through `$args$` or variables.
- Apply the adapted coefficient before calling `modeu5_resolve_stock_demand`.
- Treat zero requested quantity as neither satisfied nor unsatisfied.
- Reset annual counters only after yearly adjustment.
- Annual demand adaptation is multiplicative:
  - fully satisfied year: `location.pop_demand_multiplier[good] ×= 1.01`
  - fully unsatisfied year: `location.pop_demand_multiplier[good] ×= 0.99`
- Implement multiplier updates by reading the existing map value, multiplying it, removing the old key, and re-adding the updated value.
- Do not implement annual adaptation as an additive percentage-point change such as `+ 0.01` or `- 0.01`.
- A simulated-demand fallback is allowed only if direct `pop_demand` coefficient integration is proven unavailable.
- Estate-level, market-level, country-level, or temporary-demand fallbacks are not equivalent and require separate design approval.

## Variable-map storage pattern

US-04 and US-10.3 share the following logical location × good demand record:

```txt
location.pop_demand_record[good] = {
    multiplier
    requested_quantity
    satisfied_quantity
    unsatisfied_quantity
    satisfied_months
    unsatisfied_months
}
```

The confirmed physical representation is a synchronized family of location-scoped variable maps because one native map entry holds one value:

```txt
modeu5_pop_demand_multiplier
modeu5_pop_demand_satisfied_months
modeu5_pop_demand_unsatisfied_months
```

Map structure:

```txt
map name: modeu5_pop_demand_multiplier
key:      goods scope
value:    numeric multiplier
default:  1
```

Counter map structure:

```txt
map name: modeu5_pop_demand_satisfied_months
key:      goods scope
value:    numeric count
default:  0

map name: modeu5_pop_demand_unsatisfied_months
key:      goods scope
value:    numeric count
default:  0
```

Example physical storage for wine on a location:

```txt
add_to_variable_map = {
    name = modeu5_pop_demand_multiplier
    key = goods:wine
    value = 1
}
```

Example physical lookup for wine on that same location:

```txt
"variable_map(modeu5_pop_demand_multiplier|goods:wine)"
```

The exact goods event-target syntax, such as `goods:wine`, must be confirmed by prototype.

## Dynamic goods iteration pattern

A dynamic goods-iterator implementation is preferred if engine support is confirmed.

Prototype target:

```txt
every_owned_location = {
    save_scope_as = modeu5_current_location

    every_goods = {
        set_local_variable = {
            name = modeu5_current_good
            value = this
        }

        scope:modeu5_current_location = {
            modeu5_annual_adjust_location_pop_demand_current_good = yes
        }
    }
}
```

Inside `modeu5_annual_adjust_location_pop_demand_current_good`, the implementation should use `local_var:modeu5_current_good` as the variable-map key.

Prototype target for a satisfied-year update:

```txt
set_local_variable = {
    name = modeu5_temp_satisfied_months
    value = "variable_map(modeu5_pop_demand_satisfied_months|local_var:modeu5_current_good)"
}

if = {
    limit = {
        local_var:modeu5_temp_satisfied_months = 12
    }

    set_local_variable = {
        name = modeu5_temp_multiplier
        value = "variable_map(modeu5_pop_demand_multiplier|local_var:modeu5_current_good)"
    }

    change_local_variable = {
        name = modeu5_temp_multiplier
        multiply = 1.01
    }

    remove_from_variable_map = {
        name = modeu5_pop_demand_multiplier
        key = local_var:modeu5_current_good
    }

    add_to_variable_map = {
        name = modeu5_pop_demand_multiplier
        key = local_var:modeu5_current_good
        value = local_var:modeu5_temp_multiplier
    }
}
```

Prototype target for an unsatisfied-year update:

```txt
set_local_variable = {
    name = modeu5_temp_unsatisfied_months
    value = "variable_map(modeu5_pop_demand_unsatisfied_months|local_var:modeu5_current_good)"
}

if = {
    limit = {
        local_var:modeu5_temp_unsatisfied_months = 12
    }

    set_local_variable = {
        name = modeu5_temp_multiplier
        value = "variable_map(modeu5_pop_demand_multiplier|local_var:modeu5_current_good)"
    }

    change_local_variable = {
        name = modeu5_temp_multiplier
        multiply = 0.99
    }

    remove_from_variable_map = {
        name = modeu5_pop_demand_multiplier
        key = local_var:modeu5_current_good
    }

    add_to_variable_map = {
        name = modeu5_pop_demand_multiplier
        key = local_var:modeu5_current_good
        value = local_var:modeu5_temp_multiplier
    }
}
```

After yearly adjustment, counters must be reset by removing and re-adding the current good key with value `0`:

```txt
remove_from_variable_map = {
    name = modeu5_pop_demand_satisfied_months
    key = local_var:modeu5_current_good
}

add_to_variable_map = {
    name = modeu5_pop_demand_satisfied_months
    key = local_var:modeu5_current_good
    value = 0
}

remove_from_variable_map = {
    name = modeu5_pop_demand_unsatisfied_months
    key = local_var:modeu5_current_good
}

add_to_variable_map = {
    name = modeu5_pop_demand_unsatisfied_months
    key = local_var:modeu5_current_good
    value = 0
}
```

Do not depend on a runtime `$current_good$` token inside `every_goods`.

Invalid or not confirmed:

```txt
every_goods = {
    change_variable = {
        name = modeu5_pop_demand_multiplier_$current_good$
        multiply = 1.01
    }
}
```

Preferred dynamic pattern:

```txt
every_goods = {
    set_local_variable = {
        name = modeu5_current_good
        value = this
    }

    scope:modeu5_current_location = {
        value = "variable_map(modeu5_pop_demand_multiplier|local_var:modeu5_current_good)"
    }
}
```

This pattern is still prototype-gated until confirmed in-game.

## Fallback storage pattern

If location-scoped variable maps cannot be read from `pop_demand` script values, US-04 may fall back to macro-generated per-good location variables.

Fallback logical model:

```txt
location.pop_demand_multiplier[good]
```

Fallback runtime variables:

```txt
modeu5_pop_demand_multiplier_<good>
modeu5_pop_demand_satisfied_months_<good>
modeu5_pop_demand_unsatisfied_months_<good>
```

Example fallback physical variables for wine:

```txt
modeu5_pop_demand_multiplier_wine
modeu5_pop_demand_satisfied_months_wine
modeu5_pop_demand_unsatisfied_months_wine
```

Fallback yearly call pattern:

```txt
every_owned_location = {
    modeu5_annual_adjust_location_pop_demand_good = { good = wine }
    modeu5_annual_adjust_location_pop_demand_good = { good = beer }
    modeu5_annual_adjust_location_pop_demand_good = { good = lumber }
}
```

Fallback must be documented as a fallback, not the primary design.

## US-specific boundary checks

- [ ] Only 12/12 satisfied or 12/12 unsatisfied changes the multiplier.
- [ ] Mixed years do not change the multiplier.
- [ ] Zero-demand years do not change the multiplier.
- [ ] A shortage for one good does not alter another good's multiplier.
- [ ] A shortage in one location does not alter another location's multiplier.
- [ ] All Pops in the same location share the same multiplier for the same good.
- [ ] Two different locations may have different multipliers for the same good.
- [ ] The same location may have different multipliers for different goods.
- [ ] Building, production, construction, and army demand are unaffected.
- [ ] The multiplier update is multiplicative and compounds over time.
- [ ] The logical map model is represented physically by location-scoped variable maps.
- [ ] Per-good variables are used only as a fallback if variable-map access fails in the `pop_demand` script-value context.

## Acceptance criteria

- [ ] Actual Pop good demand is adapted through the vanilla `pop_demand` demand definition.
- [ ] The good's Pop-demand coefficient is implemented as a script value.
- [ ] The good's Pop-demand coefficient is evaluated from Pop scope.
- [ ] The Pop-scope coefficient resolves the Pop's location.
- [ ] The Pop-scope coefficient reads the relevant ModeU5 multiplier for `location × good`.
- [ ] The logical multiplier endpoint is represented as `location.pop_demand_multiplier[good]`.
- [ ] The primary runtime multiplier storage is represented as a location-scoped variable map named `modeu5_pop_demand_multiplier`.
- [ ] The variable-map key is the goods scope.
- [ ] The variable-map value is the numeric multiplier.
- [ ] Demand passed to US-10 equals base Pop good demand times the adapted Pop-demand coefficient.
- [ ] Monthly satisfaction uses actual requested quantity and removed stock / satisfaction result from US-10.3.
- [ ] Twelve satisfied months multiply the local multiplier by `1.01`.
- [ ] Twelve unsatisfied months multiply the local multiplier by `0.99`.
- [ ] Annual adjustments compound over time.
- [ ] The multiplier is never adjusted by simply adding or subtracting `0.01`.
- [ ] Variable-map updates remove the old key and re-add the updated value.
- [ ] Mixed and zero-demand years make no change.
- [ ] Building inputs are unaffected.
- [ ] Debug exposes:
  - Pop scope used for coefficient evaluation
  - resolved location
  - good
  - variable-map key used for the good
  - base Pop-demand coefficient
  - local `location × good` multiplier
  - adapted Pop-demand coefficient
  - requested quantity
  - removed quantity
  - satisfaction ratio
  - monthly satisfaction counter
  - monthly shortage counter
  - yearly adjustment result
  - storage mode, variable-map or fallback per-good variable
  - fallback mode, if active
- [ ] TECH-01 and annual test evidence are updated.

## Manual test scenario

### Setup

```txt
Locations L1 and L2 each contain Pops demanding wine and beer.
Initialize all location × good multiplier entries to 1.
Record 12 satisfied wine months for L1.
Record 12 unsatisfied wine months for L2.
Record a mixed beer year for both locations.
Inspect the multiplier and annual-counter maps before and after yearly_country_pulse.
```

### Expected result

```txt
L1 wine multiplier becomes 1.01.
L2 wine multiplier becomes 0.99.
Both beer multipliers remain 1.
No location or good overwrites another map entry.
Existing multiplier entries are updated through remove/re-add.
Annual counters reset only after the yearly adjustment reads them.
Missing entries use the documented safe default.
Debug identifies owner scope, goods key, old value, new value, and storage mode.
```

## Known limitations

A mutable runtime endpoint such as the following is still not confirmed:

```txt
location.pop_demand_<good>
pop.pop_demand_<good>
country.pop_demand_<good>
set_pop_demand
change_pop_demand
```

US-04 therefore does not depend on such an endpoint.

The preferred endpoint is the `pop_demand` good coefficient evaluated from Pop scope.

Direct gameplay implementation is blocked until prototypes confirm whether a Pop-scope `pop_demand` script value can:

```txt
1. resolve the Pop's location
2. read a persistent location-scoped variable map
3. use a goods scope as a variable-map key
4. return an adapted coefficient
```

The logical target storage is:

```txt
location.pop_demand_multiplier[good]
```

The primary runtime-compatible representation is:

```txt
location-scoped variable map:
  name  = modeu5_pop_demand_multiplier
  key   = <goods scope>
  value = numeric multiplier
```

The fallback runtime-compatible representation is:

```txt
location.var:modeu5_pop_demand_multiplier_<good>
```

Fallback per-good variables are not required for acceptance if location-scoped variable maps work from the `pop_demand` script-value context.

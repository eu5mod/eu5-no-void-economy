# US-04 — Annual pop demand adjustment

Labels: `blocked:engine-exposure`

## User Story

```txt
US-04 — Annual pop demand adjustment
```

As a player, I want Pop good demand to adapt slowly to a full year of availability or shortage within a country's participation in a market.

## Functional objective

Track Pop good demand satisfaction at `country × market × good`.

Adapt actual Pop good demand by changing the Pop-demand coefficient used by the vanilla `pop_demand` demand definition.

The primary implementation must use the vanilla `pop_demand` endpoint, evaluated from Pop scope.

The local adaptation multiplier is stored as a ModeU5 or using the vanilla pop.pop_demand[good]

Conceptually:

```txt
pop.pop_demand[good] =
    pop.pop_demand[good]
    × country.modeu5_country_market[market].pop_demand_multiplier_<good>
```

After 12 satisfied months, multiply the local Pop demand multiplier by `1.01`.

After 12 unsatisfied months, multiply the local Pop demand multiplier by `0.99`.

Mixed years and zero-demand years leave the multiplier unchanged. The annual adjustment is multiplicative and compounds over time.

## Runtime position

```txt
Monthly step:
  1. Vanilla evaluates actual Pop good demand through the `pop_demand` demand definition.
  2. The relevant good coefficient is evaluated from Pop scope.
  3. The coefficient reads the vanilla or the ModeU5 multiplier stored at country × market × good.
  4. Adapted Pop good demand is passed to US-10.1 stock resolution.
  5. US-10.3 records requested quantity, removed quantity, and satisfaction ratio.
  6. US-04 updates monthly satisfaction counters for country × market × good.

Feeds:
  next year's actual Pop demand coefficient through `pop_demand`
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Unmet Pop-relevant need signal | country × market × good | candidate market shortage trigger, or US-10.3 unsatisfied Pop-demand outcome | NOT_CONFIRMED | 037 |
| Population/type inputs | location | `num_pop_type`, `percentage_pop_type_in_location` | CONFIRMED | 038 |
| Modify vanilla demand locally | location × good × Pop context | local dynamic demand modifier/effect | CONFIRMED | 039 |
| Yearly counters | location × good | ModeU5 variables | CONFIRMED | 040 |
| Yearly pulse | country | `yearly_country_pulse` | CONFIRMED | 012 |

### 037 unmet-need prototype

Source of information : 
 - https://eu5.paradoxwikis.com/Goods_modding#Pop_demands 
 - in_game/common/goods_demand/pop_demands.txt

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

This prototype is only an unmet-need signal for US-04. It must not be used as the US-10.1 `requested_quantity`.

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
  prototype confirming Pop scope can resolve the required country and market context
  prototype confirming Pop-scope script values can read the ModeU5 country × market × good multiplier

Blocks:
  US-04-UI

Related US:
  US-10-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Apply only to Pop good demand, never building/production/construction/army demand.
- Use the vanilla `pop_demand` demand definition as the primary endpoint.


- Apply the adapted coefficient before calling `modeu5_resolve_stock_demand`.
- Treat zero requested quantity as neither satisfied nor unsatisfied.
- Reset annual counters only after yearly adjustment.
- Annual demand adaptation is multiplicative:
  - fully satisfied year: `pop.pop_demand[good] = pop.pop_demand[good] × 1.01`
  - fully unsatisfied year: `pop.pop_demand[good] = pop.pop_demand[good] × 0.99`
- Do not implement annual adaptation as an additive percentage-point change such as `pop.pop_demand + 0.01` or `pop.pop_demand[good] - 0.01`.
- A simulated-demand fallback is allowed only if direct `pop_demand` coefficient integration is proven unavailable.
- Estate-level, market-level, or temporary-demand fallbacks are not equivalent and require separate design approval.

## US-specific boundary checks

- [ ] Only 12/12 satisfied or 12/12 unsatisfied changes the multiplier.
- [ ] Mixed years do not change the multiplier.
- [ ] Zero-demand years do not change the multiplier.
- [ ] A shortage for one good does not alter another good's multiplier.
- [ ] A shortage in one country × market pair does not alter another country × market pair.
- [ ] If a country owns several locations in the same market, they share the same `country × market × good` multiplier.
- [ ] If the same country participates in several markets, each market has its own multiplier for the same good.
- [ ] Building, production, construction and army demand are unaffected.
- [ ] The multiplier update is multiplicative and compounds over time.

## Acceptance criteria

- [ ] Actual Pop good demand is adapted through the vanilla `pop_demand` demand definition.
- [ ] The good's Pop-demand coefficient is evaluated from Pop scope.
- [ ] The Pop-scope coefficient reads the relevant ModeU5 multiplier for `country × market × good`.
- [ ] The logical multiplier endpoint is represented as `pop.pop_demand[good]` or the closest confirmed engine-compatible variable-map structure.
- [ ] Demand passed to US-10 equals base Pop good demand times the adapted Pop-demand coefficient.
- [ ] Monthly satisfaction uses actual requested quantity and removed stock / satisfaction result from US-10.3.
- [ ] Twelve satisfied months multiply the local multiplier by `1.01`.
- [ ] Twelve unsatisfied months multiply the local multiplier by `0.99`.
- [ ] Annual adjustments compound over time.
- [ ] The multiplier is never adjusted by simply adding or subtracting `0.01`.
- [ ] Mixed and zero-demand years make no change.
- [ ] Building inputs are unaffected.
- [ ] Debug exposes:
  - Pop scope used for coefficient evaluation
  - resolved country
  - resolved market
  - good
  - base Pop-demand coefficient
  - local multiplier
  - adapted Pop-demand coefficient
  - requested quantity
  - removed quantity
  - satisfaction ratio
  - monthly satisfaction counter
  - monthly shortage counter
  - yearly adjustment result
  - fallback mode, if active
- [ ] TECH-01 and annual test evidence are updated.



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

Direct gameplay implementation is blocked until the prototype confirms whether a Pop-scope `pop_demand` script value can resolve and read the ModeU5 multiplier stored at `country × market × good`.

The logical target storage is:

```txt
country.modeu5_country_market[market].pop_demand_multiplier[good]
```

or the closest confirmed engine-compatible variable-map representation.

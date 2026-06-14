# US-08 — RGO & building price realignement

Labels: `blocked:engine-exposure`, `module:economy`

## User Story

```txt
US-08 — RGO & building price realignement
```

As a player, I want relevant RGOs and buildings to use a fixed base price of 50 ducats without the dynamic pricing introduced in 1.2.

## Functional objective

Identify the confirmed static base-price and dynamic-pricing fields, set relevant RGO/productive/commercial/transformation entries to base 50, and preserve only approved standard modifiers applied afterward.

## Module / availability

```txt
Package: ModeU5 Economy Rebalance
Activation: optional companion package
Behavior when absent:
  install no US-08 static building/RGO price override
  preserve vanilla construction and upgrade pricing
```

## Runtime position

```txt
Static load-time balance override
Depends on: confirmed vanilla RGO/building price fields
Feeds counters to: displayed construction prices
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Building price field and fallback rules | building type static definition | `price`, `p_building_<key>`, `p_expensive_building_<key>` | CONFIRMED | 065 |
| Building price scaling fields | building type static definition | `expensive`, `increase_per_level_cost` | CONFIRMED | 065 |
| Read building base cost | building type | `building_base_cost_in_gold` | CONFIRMED | 065 |
| RGO price field and dynamic rules | RGO/static economy files | construction/upgrade price fields | NOT_CONFIRMED | 082 |
| Relevant building/RGO entry list | local vanilla files | in-scope definition keys and current values | TO_TEST | 084 |

## Files expected to change

```txt
in_game/common/goods/
in_game/common/building_*/
in_game/common/rgo_*/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: local vanilla 1.2+ files, TECH-01
Blocks: US-08-UI
Related US: US-07
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/MODULE_OPTION_MODEL.md`.
- Keep US-08 static overrides physically outside the Core package; do not simulate deactivation with UI or runtime checks.
- Confirm exact static fields and affected entries before overriding.
- Set the verified base to 50 and neutralize only confirmed dynamic rules.
- Preserve approved standard post-base modifiers.
- Avoid unrelated static changes.

## US-specific boundary checks

- [ ] “50 ducats” refers to the confirmed base-price concept, not an invented field.
- [ ] Dynamic 1.2 effects are disabled only where verified.

## Acceptance criteria

- [ ] Every in-scope RGO/building uses base 50.
- [ ] Confirmed dynamic price rules no longer affect those entries.
- [ ] Standard approved modifiers still apply after the base.
- [ ] Final displayed cost matches calculation.
- [ ] Static files load without new blocking errors.

## Manual test scenario

### Setup

```txt
Inspect representative RGO, productive, commercial, and transformation entries
Compare prices across conditions that previously triggered dynamic variation
```

### Expected result

```txt
Each uses base 50
Only approved standard modifiers change final cost
No 1.2 dynamic variation remains for in-scope entries
```

## Known limitations

Building pricing fields and age-based fallback rules are documented. RGO pricing rules remain `NOT_CONFIRMED`; the exact in-scope vanilla building/RGO entry list remains `TO_TEST`. `default_market_price` from TECH-01 064 is a goods market-price field and must not be treated as a construction-price field.

# US-07 — Trade building rebalance

Labels: `module:trade`

## User Story

```txt
US-07 — Trade building rebalance
```

As a player, I want trade buildings rebalanced to fit ModeU5 storage and logistics constraints.

## Functional objective

Review confirmed vanilla trade-building fields, reduce marketplace trading/estate power as specified, and reassess only explicitly approved costs, capacities, or modifiers.

Current static-packaging constraint: the approved `trade_buildings.txt` `local_burghers_estate_power` reduction is composed into the US-09 Rebalance Economy exact-path building override because US-09 also edits the same vanilla file for trade-capacity compensation. This avoids two companion packages shipping competing versions of the same static definitions.

## Module / availability

```txt
Package: Rebalance Estate Power
Activation: optional companion package
Behavior when absent:
  install no standalone US-07 static building override
  preserve vanilla trade-building values only if Rebalance Economy is also absent
  keep Core US-02 storage-capacity behavior independent
```

## Runtime position

```txt
Static load-time balance override
Depends on: confirmed vanilla building definitions and modifier names
Feeds counters to: US-02 capacity and trade balance
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Building modifier block | building type static definition | `modifier`, `raw_modifier`, and documented country modifier blocks | CONFIRMED | 063, 065 |
| Marketplace power modifiers | location/estate | `local_burghers_estate_power`, `local_merchant_power` | CONFIRMED | 063 |
| Exact vanilla trade-building entries and values | local vanilla building files | relevant building keys, current modifiers, costs, and capacities | CONFIRMED | 083 |
| Building price fields | building type static definition | `price`, `expensive`, `increase_per_level_cost`, age price keys | CONFIRMED | 065 |

## Files expected to change

```txt
in_game/common/building_*/
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: local vanilla files, TECH-01
Blocks: US-07-UI
Related US: US-02, US-08
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/MODULE_OPTION_MODEL.md`.
- Keep US-07 static overrides physically outside the Core package; a runtime toggle cannot restore overwritten vanilla definitions.
- When a US-07 static field overlaps a US-09 exact-path generated file, compose the field in the US-09 generator instead of shipping two competing static overrides.
- Verify exact building files and field names before override.
- Keep changes limited to explicitly reviewed trade buildings.
- Do not infer unexposed modifiers.
- Record vanilla and ModeU5 values.
- Do not broaden into full building-profit reconstruction.

## US-specific boundary checks

- [ ] Marketplace power reduction uses the confirmed actual field.
- [ ] Storage contribution changes remain coordinated with US-02.

## Acceptance criteria

- [ ] Every changed building and field is documented.
- [ ] Marketplace power is reduced from its verified vanilla value as approved.
- [ ] The currently approved overlap is `trade_buildings.txt` `local_burghers_estate_power x 0.5`; `local_merchant_power` remains unchanged until a concrete target value is approved.
- [ ] Unrelated buildings remain unchanged.
- [ ] Tooltips/localization match the changed effects.
- [ ] Static files load without new blocking errors.

## Manual test scenario

### Setup

```txt
Compare a controlled location before/after constructing each changed trade building
Inspect power, cost, and storage effects
```

### Expected result

```txt
Only documented fields differ from vanilla
Displayed effects match ModeU5 values
No unrelated building behavior changes
```

## Known limitations

Building modifier and pricing fields, including both marketplace-power modifier names, are documented. The current package composition covers only the approved `local_burghers_estate_power` reduction in the US-09 exact-path trade-building override; `local_merchant_power` is intentionally left unchanged.

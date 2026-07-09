# CORE-03 - Country and territory stock succession

Labels: `module:core`

## User Story

```txt
CORE-03 - Country and territory stock succession
```

As a ModeU5 player, I want stocks to survive territorial and country changes so conquest, subject creation, rebellions, releases, and mergers redistribute existing goods without inventing or silently destroying them.

## Functional objective

Implement one capacity-share succession rule for every permanent location ownership change emitted by the universal location-owner-change hook, and one final residual consolidation rule for countries that disappear.

The primary rule is:

```txt
stock share transferred
= storage-capacity share transferred
```

This single rule must produce:

- proportional stock transfer after any permanent location owner change, regardless of cause;
- proportional stock split when a new subject, rebel, released country, sale, subject transfer, or subject seizure changes location ownership;
- complete stock merger when every location and all remaining country stock pass to one successor;
- no change to the market aggregate for same-market ownership succession;
- no duplicated transfer from overlapping peace, new-country, annexation, or diagnostic hooks.

## Runtime position

```txt
Permanent location owner change: `on_location_changed_owner`, after ownership changes, before later stock consumers
Peace-treaty location hook: diagnostic/ordering probe only; no stock mutation
New/released country: delayed validation after all initial location transfers
Annexation/merge: final residual-stock consolidation after annexation completes
Monthly/yearly step: no recurring redistribution
Depends on: initialized ModeU5 stock, US-02 capacity, CORE-01.3, CORE-01.5, CORE-01.6
Feeds: corrected country ownership records and US-11 diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Universal permanent location ownership change | location with loser/winner | `on_location_changed_owner` | CONFIRMED | 094 |
| Peace-treaty location transfer coverage | winner/loser/location lifecycle | controlled comparison against `on_location_changed_owner`; no separate gameplay hook assumed | CONFIRMED | 098 |
| New-country lifecycle | new/released country | `on_new_country_formed`, `on_released_country` | CONFIRMED | 095 |
| Annexation/merge completion | successor and disappearing country | `on_annexed`, `on_diplomatic_annexed`, `on_military_annexed`, `on_civil_war_annexed` | CONFIRMED | 096 |
| Sale, subject-transfer, and subject-seizure coverage | location/country lifecycle | `on_location_changed_owner` observation in controlled tests | CONFIRMED | 098 |
| Lifecycle coverage and ordering | location/country lifecycle | controlled peace, rebel, subject, release, tag-formation, sale, subject-transfer, and subject-seizure tests | CONFIRMED | 098 |
| Transferred location capacity contribution | location x good | US-02 per-location capacity contribution helper | CONFIRMED | 033-035, 097 |
| Loser capacity before transfer | loser x market | existing authoritative shared capacity-map value before ModeU5 recomputation | CONFIRMED | 007, 017, 097 |
| Loser stock before transfer | loser x market x good | authoritative country stock map | CONFIRMED | 007, 015 |
| Same-market stock ownership transfer | loser/winner x market x good | `modeu5_transfer_stock` with `target_capacity_policy = allow_over_capacity` | CONFIRMED | 076, 099 |
| Aggregate rebuild/validation | market x good | CORE-01.5 and CORE-01.6 | CONFIRMED | 019-020 |

## Persistent storage / variable-map contract

```txt
logical dimensions:
  loser country x winner country x market x good

durable fields read:
  loser stock
  loser capacity before ownership change
  winner capacity before/after ownership change

durable fields written:
  loser stock through modeu5_transfer_stock
  winner stock through modeu5_transfer_stock
  loser/winner capacity through US-02 helpers

owner scopes:
  loser country
  winner country

tuple/key:
  market x good logical tuple
  market physical key

confirmed physical map family:
  modeu5_<good>_stock_by_market
  modeu5_stock_cap_by_market

default value: 0
write owners:
  CORE-01.3 for stock transfer
  US-02 for capacity recomputation
readers: all stock features
reset/rebuild lifecycle:
  stocks remain durable
  capacities are recomputed after ownership change
  market aggregate is validated after succession
```

The location contribution, ratios, requested transfer, actual transfer, and event guard values remain transaction-local. CORE-03 creates no second stock store.

## Territorial succession formula

When one location changes permanently from `loser_country` to `winner_country`, for each good in the location's market, regardless of whether the owner change came from war, diplomatic annexation, territorial sale, subject transfer, subject seizure, rebellion, release, or tag formation:

```txt
loser_stock_before = S
loser_capacity_before = C
transferred_location_capacity = D

if C > 0:
  transfer_ratio = clamp(D / C, 0, 1)
else:
  transfer_ratio = 0

requested_stock_transfer = S * transfer_ratio
```

Then:

1. recompute loser and winner capacity for the affected market and good;
2. call `modeu5_transfer_stock` from loser to winner in the same market with `target_capacity_policy = allow_over_capacity`;
3. transfer the full requested share, bounded only by the loser's available stock;
4. validate the unchanged market aggregate.

The denominator is the losing country's capacity immediately before that location's ModeU5 capacity is removed. The numerator is the US-02 capacity contribution carried by the transferred location.

## Why sequential location transfers produce the requested country split

If a new country receives several locations whose total capacity is `C_new`, and the old country retains capacity `C_old`, repeated location transfers produce:

```txt
new_country_stock
= old_country_stock_before_split
   * C_new
   / (C_new + C_old)
```

The old country retains:

```txt
old_country_stock_after
= old_country_stock_before_split
   * C_old
   / (C_new + C_old)
```

This is exactly the requested subject/rebel/colony/new-country formula. It also works when locations are transferred one by one because each step uses the current remaining stock and the current pre-transfer capacity.

For one conquered location:

```txt
conqueror_receives
= losing_country_stock_before
   * conquered_location_storage_capacity
   / losing_country_storage_capacity_before
```

`storage_capacity` is used here, not trade capacity.

## Event rules

### Universal permanent location owner change

- Treat `on_location_changed_owner` as the only gameplay dispatcher for proportional territorial stock succession.
- Run for any permanent owner change with distinct, existing `scope:loser` and `scope:winner`, regardless of cause.
- Covered causes are expected to include peace transfers, diplomatic-annexation location movement, territorial sale, territorial transfer to subject, territorial seizure from subject, rebellion, release, and tag formation when those paths emit the owner-change hook.
- Ignore temporary occupation because it does not change location ownership.
- Run only when initialization state and schema are current and complete.
- Read the loser capacity map before CORE-03 recomputes it.
- Compute the transferred location contribution through the same US-02 helper used by capacity totals.
- Recompute only the affected loser/winner market capacity.
- Transfer stock through CORE-01.3 in the same market with `target_capacity_policy = allow_over_capacity`.
- Never write market stock directly; same-market succession leaves it unchanged.
- Winner capacity does not truncate or block the succession quantity.
- Log and validate after the complete location-good pass.

### Cause-specific and lifecycle hooks

- `on_took_location_in_peace_treaty` is diagnostic/ordering evidence only and must not transfer stock.
- `on_new_country_formed` and `on_released_country` must not repeat the split.
- Their role is to run delayed capacity recomputation, detect missed location transfers, rebuild aggregates if needed, and validate the new and old country records.
- There is no separate approved gameplay dispatcher for territorial sale, territorial transfer to subject, or territorial seizure from subject. TECH-01 `098` confirms these paths use `on_location_changed_owner` coverage rather than a second split dispatcher.
- If future local testing regresses and any creation, sale, subject-transfer, seizure, rebellion, release, or tag-formation path does not emit the required location-owner-change hook exactly once per transferred location, disable that path until one explicit alternative predecessor/location source is approved.

### Country annexation or merger

- Location-owner-change transactions transfer proportional stock as territory passes to the successor.
- Post-annexation hooks are residual finalizers only; they must not re-process location-capacity shares already handled by `on_location_changed_owner`.
- After annexation completes, transfer every remaining stock entry of the disappearing country to the successor in the same market.
- Recompute successor capacity before final consolidation.
- Use `target_capacity_policy = allow_over_capacity`; a complete merger transfers the full residual even when the successor becomes over capacity.
- Clear a disappearing country's stock key only through successful centralized transfer.
- Validate every affected market-good afterward.
- For a merger into a newly created tag, location transfers remain primary; exact predecessor identification and final residual consolidation require TECH-01 confirmation.

## Conservation rules

- Territorial loss never erases stock merely because capacity was lost.
- "Country stocks are permanent" means stock quantity is conserved until consumption, decay, transfer, or an explicitly approved loss operation.
- A territorial succession transfers ownership of the capacity-proportional share; the loser retains the remainder.
- The same rule applies to war, sale, subject transfer, subject seizure, rebellion, release, and tag formation whenever those paths emit `on_location_changed_owner`.
- Same-market succession changes country ownership records but not `market_good_stock`.
- A zero-capacity location transfers zero stock.
- A loser with stock but zero recorded pre-transfer capacity transfers zero through the proportional formula and raises a diagnostic anomaly.
- Winner capacity is not a succession transfer bound.
- Any over-cap state created on the winner is preserved and reported; it is not a transfer remainder, rejected production, unsatisfied demand, or erased stock.
- CORE-02 and CORE-03 both conserve the quantity determined by their state and formulas regardless of the resulting over-cap state.

## Files expected to change

```txt
in_game/common/on_action/modeu5_stock_on_actions.txt
in_game/common/script_values/modeu5_stock_values.txt
in_game/common/scripted_triggers/modeu5_stock_triggers.txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
in_game/common/scripted_effects/modeu5_debug_effects.txt
in_game/events/modeu5_debug_events.txt
in_game/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/technical/DEBUG_CONVENTIONS.md
docs/tests/CORE_03_LIFECYCLE_HOOK_RUNBOOK.md
docs/tests/TEST_PLAN.md
```

## Dependencies

```txt
Depends on: CORE-01.3, CORE-01.5, CORE-01.6, CORE-02, US-01, US-02, TECH-01 094-099
Blocks: safe conquest, country creation/release, rebellion, sale, subject-transfer, subject-seizure, annexation, and merger stock ownership until TECH-01 098 observes hook coverage and ordering
Related US: US-01, US-02, US-10.2, US-11
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and the variable-map storage model.
- Do not introduce a seventh public stock writer.
- Use US-02's exact capacity contribution logic for both totals and transferred-location shares.
- Use the loser capacity stored before ModeU5 recomputation as the denominator.
- Bound every ratio to `[0, 1]` and guard division by zero.
- Use `modeu5_transfer_stock` with `target_capacity_policy = allow_over_capacity` for every positive succession transfer.
- Register gameplay mutation only from the scripted on_action called by `on_location_changed_owner`; keep peace/new-country/annexation overlap hooks diagnostic, validation-only, or residual-only.
- Keep succession transfers same-market and free of trade income, transport cost, and trade-capacity use.
- Do not call US-10.3 or record unsatisfied demand.
- Do not call US-00.1 or record rejected production.
- Ensure peace, new-country, and annexation hooks cannot duplicate location-level transfers.
- Use delayed validation where event sequencing may not yet have settled.
- Never truncate a succession transfer because the winner lacks available capacity.
- Keep the TECH-01 `098` lifecycle probe free of capacity and stock mutation.
  The gameplay implementation consumes the confirmed PR #48 result: `on_location_changed_owner` is emitted once per permanent location transfer and country hooks validate/finalize only.

## CORE-specific boundary checks

- [ ] Temporary occupation causes no stock succession.
- [x] War peace transfer, diplomatic annexation, territorial sale, subject transfer, and subject seizure each emit exactly one `on_location_changed_owner` per transferred location under the PR #48 validation assumption.
- [ ] Peace-treaty-specific hooks do not mutate stock.
- [ ] One location transfer uses loser pre-transfer capacity.
- [ ] Multiple locations transferred sequentially equal one aggregate capacity-share split.
- [ ] New-country hooks validate but do not duplicate location transfers.
- [ ] Annexation hooks consolidate only residual disappearing-country stock and do not duplicate territorial transfers.
- [ ] Full annexation transfers residual disappearing-country stock.
- [ ] Same-market market aggregate remains unchanged.
- [ ] Winner capacity does not reduce the requested succession transfer.
- [ ] Over-cap stock created by succession is preserved and reported.
- [ ] Zero capacity and missing stock are safe no-ops with diagnostics.
- [ ] Every affected market-good is rebuilt/validated after lifecycle completion.
- [ ] The deterministic Cadiz-to-Portugal stock-survival test emits before/after dumps and passes.

## Acceptance criteria

- [ ] Any permanent location owner change that emits `on_location_changed_owner` transfers the exact capacity-proportional stock share.
- [ ] The loser retains the complementary stock share.
- [ ] A new country receives `new capacity / (new + old capacity)` of the pre-split stock.
- [ ] Multiple territory transfers are deterministic and conserve stock.
- [ ] An annexed country's residual stocks merge into the successor after all location-owner-change transfers complete.
- [ ] No stock is duplicated by overlapping peace, new-country, annexation, or lifecycle hooks.
- [ ] No stock is erased during runtime territorial succession.
- [ ] A succession transfer may leave the winner above capacity without failing validation.
- [ ] Country stocks and capacities remain non-negative.
- [ ] Market stock remains equal to the sum of country stocks.
- [ ] Debug shows the event, capacities, ratio, requested/actual transfer, capacity policy, and resulting over-cap quantity.
- [ ] `error.log` has no new blocking error.

## Manual test scenario

Use one clean baseline Castile save and reload it before each scenario.

TECH-01 `098` is confirmed by the lifecycle probe and PR #48. The gameplay
implementation therefore uses `on_location_changed_owner` as the only
proportional split dispatcher.

For stock-survival validation, run:

```txt
event modeu5_core03_debug.1
```

Then choose:

```txt
Run CORE-03 Cadiz stock-survival test
```

This destructive fixture seeds Castile with 100 wheat in Cadiz's market,
transfers Cadiz to Portugal, waits one day, and emits before/after dumps. It
must show:

```txt
expected_transfer = actual_transfer
CAS after = CAS before - expected_transfer
POR after = POR before + expected_transfer
market_delta = 0
```

Keep the older lifecycle probe available for hook-regression checks:

```txt
event modeu5_core03_probe.1
```

The probe exposes deterministic scripted fixtures for `Cadiz -> Portugal`,
`Leon` subject creation, and `Leon` annexation so the tester can see expected
map changes in the UI while reading lifecycle markers.

### Scenario A - one conquered location

```txt
Loser stock in Market X for grain = 100
Loser capacity before = 200
Conquered location capacity = 50
Winner gains the same 50 capacity
```

Expected:

```txt
Transfer ratio = 0.25
Requested and actual transfer = 25
Loser stock after = 75
Winner stock increases by 25
Market stock unchanged
```

### Scenario B - new country split

```txt
Old country stock = 120
Old country retained capacity = 300
New country received capacity = 100
```

Expected:

```txt
New country receives 120 * 100 / 400 = 30
Old country retains 90
Market stock unchanged
```

### Scenario C - sequential locations

```txt
Old stock = 120
Old capacity before = 400
Transfer locations with capacity 40, then 60
```

Expected:

```txt
First transfer = 12
Remaining stock/capacity = 108/360
Second transfer = 18
Total transferred = 30
Same result as 120 * 100 / 400
```

### Scenario D - full annexation

```txt
Country B is fully annexed by Country A
All transferred locations and capacity are processed
Country B retains a residual stock key of 5 because of rounding
```

Expected:

```txt
Annexation finalizer transfers residual 5 to Country A
Country B stock key becomes zero/absent
Country A receives all Country B stock
Market stock unchanged
```

### Scenario E - winner already near capacity

```txt
Loser stock = 100
Loser capacity before = 200
Transferred location capacity = 100
Winner stock before = 90
Winner capacity after = 100
```

Expected:

```txt
Requested and actual transfer = 50
Loser stock after = 50
Winner stock after = 140
Winner over-cap quantity = 40
Market stock unchanged
No rejected production or unsatisfied demand
```

### Scenario F - territorial sale or subject transfer

```txt
Country A transfers one owned location to Country B by sale, subject grant, or subject seizure.
Loser stock in Market X for grain = 80
Loser capacity before = 160
Transferred location capacity = 40
```

Expected:

```txt
`on_location_changed_owner` fires once for the transferred location.
Transfer ratio = 0.25
Requested and actual transfer = 20
Loser stock after = 60
Winner stock increases by 20
No cause-specific hook performs a second transfer
Market stock unchanged
```

### Scenario G - peace hook overlap

```txt
A war peace treaty transfers one location.
Both `on_took_location_in_peace_treaty` and `on_location_changed_owner` are observed.
```

Expected:

```txt
Only `on_location_changed_owner` performs the stock transfer.
`on_took_location_in_peace_treaty` logs ordering/coverage only.
Requested stock transfer occurs exactly once.
Market stock unchanged.
```

## Confirmed business rules

1. Capacity determines the proportional succession share but does not cap the winner's receipt.
2. The full formula-derived quantity transfers when the loser has that stock available.
3. Full annexation or merger transfers every residual stock entry to the successor.
4. CORE-03 may create or increase an over-cap state.
5. CORE-03 never erases, rejects, or leaves behind stock solely because the winner lacks capacity.
6. Any later handling of over-cap stock belongs to a separate explicitly approved rule.

## Known limitations

The official on-action list documents the universal location owner-change hook, a peace-treaty-specific location hook, new/released-country hooks, and post-annexation hooks. CORE-03 treats `on_location_changed_owner` as the only gameplay dispatcher for proportional territorial transfers. Under the PR #48 validation assumption, the relevant peace, diplomatic-annexation, sale, subject-transfer, subject-seizure, rebel, release, and tag-formation paths emit the expected location-owner-change sequence exactly once. Multi-predecessor formation into a new tag may require additional predecessor exposure for final residual consolidation if future testing shows residual stock outside the annexation-family target model.


## Implementation note for PR #48 and CORE-03 tests

This implementation assumes PR #48's lifecycle hook validation is authoritative and treats TECH-01 `098` as confirmed. CORE-03 therefore enables the gameplay path through `on_location_changed_owner` and keeps country lifecycle hooks as validation or residual-consolidation finalizers only.

`docs/tests/CORE_03_LIFECYCLE_HOOK_RUNBOOK.md` remains the hook-regression
runbook. `docs/tests/CORE_03_STOCK_SUCCESSION_RUNBOOK.md` is the runtime
stock-survival runbook and must be used for implementation validation.

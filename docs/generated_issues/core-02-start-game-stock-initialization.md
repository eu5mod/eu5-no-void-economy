# CORE-02 - Start-game stock initialization

Labels: module:core, technical-foundation

## User Story

```txt
CORE-02 - Start-game stock initialization
```

As a ModeU5 player, I want the stock layer to initialize once from the opening game state so every country receives its capacity-proportional share and the double-accounting invariant is valid before the monthly economy begins.

## Functional objective

Add one delayed, versioned, idempotent `on_game_start` pipeline that:

1. establishes global ModeU5 initialization variables;
2. calculates all country x market x good storage capacities through US-02;
3. reads an opening quantity for each market x good;
4. allocates the full opening quantity to countries proportionally to their capacity through `modeu5_add_stock`;
5. permits the resulting country stocks to exceed capacity;
6. resolves fixed-point residue without truncating the opening quantity;
7. rebuilds and validates every market aggregate;
8. enables monthly ModeU5 gameplay only after successful completion.

## Runtime position

```txt
Start-game step: on_game_start -> delay 1 day -> modeu5_start_game_dispatcher
Monthly step: the monthly dispatcher must skip stock gameplay until initialization_state = complete
Yearly step: none
Depends on: CORE-00, CORE-01.1, CORE-01.5, CORE-01.6, US-01, US-02
Feeds: all stock-owning and stock-consuming features
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Delayed start-game hook | none | extend `on_game_start` with a unique ModeU5 on-action after `delay = { days = 1 }` | CONFIRMED | 089 |
| Persistent initialization/version guard | none | `global_var:modeu5_stock_schema_version`, `modeu5_initialization_state`, global-variable effects/triggers | CONFIRMED | 090 |
| Iterate countries, markets, and goods | none | `every_country`, `every_market_in_world`, `every_goods` | CONFIRMED | 001-002, 006 |
| Country capacity by market and good | country x market x good | US-02 authoritative capacity map | CONFIRMED | 007, 017, 033-035 |
| Opening vanilla market stock | market x good | `"stockpile_in_market(goods:<good>)"` on market scope after the delayed start hook | CONFIRMED | 091 |
| Proportional allocation arithmetic | market x good x country | local variables with multiply/divide/min/max | CONFIRMED | 026 |
| Deterministic residue recipient | temporary list or typed country iterator with positive allocation weight | `ordered_in_list` or typed `ordered_country` with `order_by = country_capacity` | CONFIRMED | 074, 093 |
| Stock addition | country x market x good | `modeu5_add_stock` with `capacity_policy = allow_over_capacity` | CONFIRMED | 015-018, 022-023, 099 |
| Aggregate rebuild and validation | market x good | `modeu5_rebuild_market_stock_from_country_stocks`, `modeu5_validate_stock_consistency` | CONFIRMED | 019-020 |

## Persistent storage / variable-map contract

Global scalar state:

```txt
modeu5_stock_schema_version
modeu5_initialization_state
```

Static/scripted configuration:

```txt
modeu5_current_stock_schema_version
modeu5_initialization_rounding_epsilon
modeu5_debug_level, read-only here and initialized by CORE-00 from the selected game rule
```

Physical numeric initialization states:

```txt
0 = absent / not started
1 = in_progress
2 = complete
-1 = failed
```

Stock and capacity storage:

```txt
logical dimensions: country x market x good
logical record fields: stock, capacity and optional capacity breakdown
owner scope: country
tuple/key: market x good logical tuple; market physical key
confirmed physical map family:
  modeu5_<good>_stock_by_market
  modeu5_<good>_stock_cap_by_market
  optional US-02 capacity-breakdown maps
physical value type: numeric
default value: 0
write owner:
  US-02 capacity helper for capacity fields
  modeu5_add_stock for initial stock
readers: every stock feature
reset/rebuild lifecycle:
  capacity is recalculated before stock seeding
  opening stock is seeded once only
  market aggregate is rebuilt from country stock after seeding
```

Market aggregate:

```txt
owner scope: global variable system
map: modeu5_<good>_market_stock
key: market scope
default: 0
write owner during startup: CORE-01.1 additions and CORE-01.5 rebuild
```

Storage remains sparse:

- Do not materialize zero stock, zero counters, or zero aggregate entries solely for initialization.
- Missing zero-default fields remain absent.
- Nonzero defaults such as a future demand multiplier of `1` use their owning feature's initializer or safe accessor; CORE-02 must not eagerly create every location x good record.
- Opening source quantities, allocation shares, residuals, and diagnostics stay transaction-local.

## Initialization pipeline

### Phase 0 - Hook and guard

```txt
on_game_start
-> delay one day
-> modeu5_start_game_dispatcher
```

- Extend the hardcoded on-action only through an `on_actions` block with a unique ModeU5 name.
- Run the ordered pipeline inside one custom on-action effect. Do not rely on an event and effect fired concurrently for sequencing.
- Select the startup mode first. Set `modeu5_initialization_state = in_progress` before fresh initialization, migration, or recovery writes; do not downgrade an already complete current-schema state merely to validate it.
- Do not start monthly ModeU5 economic mutations until state is `complete`.

### Phase 1 - Select startup mode

```txt
no schema marker and no country stock:
  fresh initialization

current schema marker:
  no reseed; validate existing data only

current schema marker with failed state:
  diagnostics only; never seed or enable monthly stock gameplay automatically

older schema marker:
  require one explicit migration; never reuse fresh stock seeding

newer schema marker:
  abort ModeU5 mutations and log incompatible save

no schema marker but country stock exists:
  abort fresh initialization; preserve all stock and require an explicit migration

initialization_state = in_progress from a prior interrupted run:
  abort fresh initialization; preserve all stock and require an explicit recovery
```

Before fresh allocation, every country x market x good source stock must be absent or exactly zero. Any nonzero or negative country source entry blocks allocation. A stray market aggregate without country stock is an invalid cache: rebuild it to zero from country stock before continuing.

### Phase 2 - Calculate capacities

- Run the US-02 authoritative country-level capacity calculation for every active country before opening-stock allocation.
- Build country x market capacity from market merchant capacity and owned-location rank/capital contributions.
- Write each capacity key through the US-02 centralized capacity helper.
- Treat negative capacity as invalid, replace it with zero, and log the source contributions.
- A country with zero capacity receives no opening stock.
- Capacity calculation itself must not mutate stock.
- Capacity is the proportional allocation weight, not an opening-stock admission limit.
- A valid initialization may leave one or more countries above capacity.

### Phase 3 - Determine opening market-good quantity

Recommended source:

```txt
opening_source_quantity = max(0, vanilla stockpile_in_market for the good)
total_modeu5_capacity = sum(country capacity for market and good)
opening_target_quantity = opening_source_quantity
```

CORE-02 does not truncate the opening source to total capacity. If the opening quantity is greater than total capacity, the same proportional formula allocates the full quantity and creates an explicit over-cap state.

There is no synthetic fill-ratio fallback. If TECH-01 `091` cannot read the current vanilla market stock reliably, fresh initialization remains blocked and no ModeU5 opening stock is created. A successfully read vanilla value of zero is a valid empty opening stockpile.

If `opening_source_quantity > 0` while `total_modeu5_capacity = 0`, no proportional basis exists. Do not erase, invent, or arbitrarily assign the stock. Mark initialization failed for that market-good, log `zero_total_capacity`, and keep monthly ModeU5 stock gameplay disabled until capacity data or an approved migration rule resolves it.

### Phase 4 - Allocate proportionally

For each country with positive capacity in the selected market:

```txt
country_initial_share =
  opening_target_quantity
  * country_market_good_capacity
  / total_modeu5_capacity
```

Then call:

```txt
modeu5_add_stock(
  country
  market
  good
  quantity_to_add = country_initial_share
  capacity_policy = allow_over_capacity
  reason = initialization
)
```

Rules:

- Do not call the US-00.1 production ledger.
- The sum of initial shares must not exceed `opening_target_quantity`.
- Capacity determines each country's share but does not cap that share.
- `actual_added_quantity` must equal `requested_initial_quantity`; initialization produces no rejected quantity.
- Record `over_capacity_quantity = max(0, stock_after - capacity)` for diagnostics only.
- Countries with equal proportional rights may receive slightly different final amounts only because of fixed-point residue.
- Country iteration must read capacity maps, not reconstruct capacity.

### Phase 5 - Resolve fixed-point residue

After the proportional pass:

```txt
remaining_initial_quantity =
  opening_target_quantity - sum(actual_added_quantity)
```

- If the absolute residue is at or below the configured fixed-point epsilon, log it and stop.
- If positive and above epsilon, select the country with the greatest original capacity through the confirmed ordered-iterator contract (`ordered_in_list` or typed `ordered_country`), repeating only if required.
- Never write the residue directly to a stock or market aggregate.
- Never exceed `opening_target_quantity`.
- A negative residue is a blocking initialization error; do not compensate by removing arbitrary country stock.

### Phase 6 - Rebuild, validate, and commit

For every initialized market x good:

1. call `modeu5_rebuild_market_stock_from_country_stocks`;
2. call `modeu5_validate_stock_consistency`;
3. confirm country stocks are non-negative and report any over-cap amount without correcting it;
4. confirm aggregate difference is zero;
5. confirm allocated quantity matches the full opening source within epsilon.

Set `modeu5_stock_schema_version` and `modeu5_initialization_state = complete` only after the global pass succeeds.

If a blocking check fails:

- set state to `failed`;
- leave monthly ModeU5 stock gameplay disabled;
- preserve country source stock for diagnosis;
- do not rerun fresh seeding automatically;
- expose a deterministic debug recovery event, but do not add a destructive reset path without approval.

## Files expected to change

```txt
in_game/common/on_action/modeu5_stock_on_actions.txt
in_game/common/script_values/modeu5_stock_values.txt
in_game/common/scripted_triggers/modeu5_configuration_triggers.txt
in_game/common/scripted_triggers/modeu5_stock_triggers.txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
in_game/common/scripted_effects/modeu5_stock_goods_generated.txt
main_menu/localization/english/modeu5_stock_l_english.yml
tools/generate_stock_good_helpers.sh
tools/templates/modeu5_stock_good_adapter.template.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_stock_test_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_debug_events.txt
packages/modeu5_core_tests/in_game/common/on_action/modeu5_core02_exposure_on_actions.txt
packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_core02_exposure_effects.txt
packages/modeu5_core_tests/in_game/events/modeu5_core02_exposure_events.txt
packages/modeu5_core_tests/main_menu/localization/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/technical/DEBUG_CONVENTIONS.md
docs/tests/CORE_02_OPENING_STOCK_EXPOSURE_RUNBOOK.md
docs/tests/CORE_02_START_GAME_INITIALIZATION_RUNBOOK.md
docs/tests/TEST_PLAN.md
```

## Dependencies

```txt
Depends on: CORE-00, CORE-01.1, CORE-01.5, CORE-01.6, US-01, US-02, TECH-01 089-093, 099
Blocks: enabling the monthly ModeU5 economic cycle
Related US: US-01, US-02, US-03, US-04, US-11
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and `VARIABLE_MAP_STORAGE_MODEL.md`.
- Use `on_game_start` with a one-day delay because its immediate state may not contain initialized nations.
- Treat startup testing as delayed by one in-game day minimum; do not judge initialization state or startup logs on campaign day 0.
- Keep the dispatcher global; do not trigger one full-world initialization from every country.
- Make the pipeline idempotent and schema-versioned.
- Never seed stocks when any existing nonzero or negative country source stock is detected.
- Never use the market aggregate as a source of truth or distribute it back to countries.
- Recalculate all startup capacities before calculating any opening allocation.
- Use the current vanilla market stock as the only opening-stock source.
- Use `modeu5_add_stock` with `capacity_policy = allow_over_capacity` for every positive country allocation.
- Use CORE-01.5 and CORE-01.6 for aggregate repair and validation.
- Treat opening over-cap stock as a valid initialized state, not rejected production, void wealth, or a production penalty.
- Keep zero-default storage sparse.
- Do not silently repair a newer, incompatible schema.
- Add one non-destructive manual initialization/diagnostic event for testing or mid-campaign installation.
- Keep the TECH-01 `091` delayed opening-stock probe separate from the
  initialization dispatcher. Passing that probe is a prerequisite for fresh
  seeding, not permission to implement a fallback.

## CORE-specific boundary checks

- [ ] Fresh initialization runs only after the delayed hook.
- [ ] Loading or re-entering an initialized campaign never refills stock.
- [ ] Existing country stock with a missing marker is preserved, but fresh allocation is blocked until an explicit migration/recovery is implemented.
- [ ] Capacity is complete before any opening stock is added.
- [ ] A zero-capacity country receives zero stock when other countries provide a positive total allocation weight.
- [ ] A positive opening source with zero total capacity fails closed without erasing or arbitrarily assigning stock.
- [ ] Vanilla quantity above total capacity is fully allocated and logged as over-cap stock.
- [ ] Rounding residue uses `modeu5_add_stock`.
- [ ] Startup never initializes monthly ledgers, penalties, or demand outcomes with fabricated activity.
- [ ] A failed initialization prevents monthly stock mutations.
- [ ] New-country formation, ownership changes, market splits/merges, and capacity loss after startup remain runtime lifecycle behavior, not reasons to rerun fresh initialization.

## Acceptance criteria

- [ ] Fresh stock seeding occurs exactly once in a clean new game even if the dispatcher is invoked again.
- [ ] Global initialization state and schema version persist.
- [ ] Every positive capacity is computed before stock seeding.
- [ ] For each market-good, initial country stocks are proportional to capacity within fixed-point epsilon.
- [ ] A country may exceed capacity when the opening source exceeds total capacity.
- [ ] Total initialized stock equals the full opening source within epsilon.
- [ ] Market aggregates equal the sum of country stocks.
- [ ] A second invocation with the current complete schema performs validation only and adds no stock.
- [ ] Existing source stock with no marker is never duplicated.
- [ ] Opening over-cap quantities and any unavailable vanilla source are visible in debug.
- [ ] `error.log` has no new blocking error.
- [x] TECH-01 `091` is confirmed before fresh stock allocation is enabled.

## Manual test scenario

### Scenario A - proportional allocation

```txt
Market X, Good grain
Country A capacity = 100
Country B capacity = 300
Opening source quantity = 200
Total capacity = 400
```

Expected:

```txt
Country A stock = 50
Country B stock = 150
Market stock = 200
Difference = 0
```

### Scenario B - opening quantity above capacity

```txt
Country A capacity = 40
Country B capacity = 60
Opening source quantity = 150
```

Expected:

```txt
Opening target = 150
Country A stock = 60
Country B stock = 90
Country A over-cap quantity = 20
Country B over-cap quantity = 30
Allocated quantity = 150
US-00 rejected production = 0
No void wealth or production penalty
```

### Scenario C - repeated invocation

```txt
Complete Scenario A, then invoke the startup dispatcher again
```

Expected:

```txt
Country stocks remain 50 and 150
No opening stock is added
Validation difference = 0
Initialization mode = existing/current schema
```

### Scenario D - existing unversioned country stock

```txt
Schema marker absent
Country A source stock = 20
Market aggregate missing or wrong
```

Expected:

```txt
Country A remains 20
No fresh proportional allocation occurs
Initialization state = failed
Monthly stock gameplay remains disabled
Explicit migration/recovery is required
```

## Confirmed business rules

1. Read the current vanilla stock for each market and good.
2. Calculate every country storage capacity before allocating stock.
3. Require all ModeU5 country x market x good stocks to be empty before fresh allocation.
4. Allocate the full vanilla market stock proportionally to country storage capacities.
5. Permit initialization to create stocks above capacity; do not erase or reject the excess.
6. Treat capacity as an allocation weight for CORE-02, not an admission cap.
7. Do not invent a fill-ratio fallback when the vanilla stock value cannot be read.
8. Post-start territorial and country lifecycle rules are owned by CORE-03.

## Known limitations

The wiki documents `on_game_start`, its one-day-delay warning, persistent global variables, all required iterators, and `stockpile_in_market` as a market value. Vanilla scripts use `"stockpile_in_market(goods:<good>)"` on market scope. A controlled June 15, 2026 test confirmed that this form returns a persistent numeric value after the delayed start hook without mutating ModeU5 stock or initialization state. The rejected `stockpile_in_market:<good>` form produced an event-target and missing-goods-field error and must not be restored. No synthetic opening-stock fallback is accepted.

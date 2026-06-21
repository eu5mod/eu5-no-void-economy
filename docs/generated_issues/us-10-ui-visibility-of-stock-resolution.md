# US-10-UI — Visibility of Stock, Demand, and Void-Economy Resolution

Labels: none

## User Story

```txt
US-10-UI — Visibility of Stock, Demand, and Void-Economy Resolution
```

As a player or modder, I want to understand where production entered stock, where it was rejected, which stocks fulfilled demand, which candidates were excluded, and why any quantity remained unsatisfied.

## Functional objective

Implement a read-only ModeU5 goods summary panel for the selected market/country context.

The panel must show one row per visible good with these columns:

- Good
- Country Stocks
- Market Stocks
- Overproduction
- Production Efficiency

The panel must distinguish:
- country-owned stock vs market aggregate stock
- stock over capacity vs monthly overproduction/surplus
- production efficiency modifiers vs stock/demand outcomes

Debug logs may support validation, but the player-facing panel is the primary deliverable.

## Runtime position

```txt
Monthly step: read after US-00.1/US-00.2/US-00.3/US-00.4 and US-10.1/US-10.2/US-10.3
Depends on counters from: EPIC US-00 and US-10.0 through US-10.3
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| US-00 production admission record | country × market × good | direct reads of produced/added/rejected maps and runtime debug dump fields | CONFIRMED | 021-025 |
| US-00 void-economy record | country × market × good | ratio, effective ratio, void wealth, price source, and penalty fields | CONFIRMED | 025-030 |
| US-00 production modifier diagnostics | country × location × market × good | affected location count and modifier application mode | CONFIRMED | 010, 027-029 |
| Resolver/outcome records | demand/country/market/location/good | current transaction diagnostics plus direct reads of US-10.3 outcome maps | CONFIRMED | 007, 040, 067-077 |
| Debug event and logs | effect scope | event triggers and `debug_log` | CONFIRMED | 013 |
| Localization/tooltips | UI | `custom_tooltip`, modifier descriptions, localization keys | CONFIRMED | 014 |
| Optional custom panel | UI | ModeU5 window | OUT_OF_SCOPE | N/A |

## Files expected to change

```txt
in_game/events/
in_game/localization/
main_menu/common/static_modifiers/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

Mandatory player-facing goods summary panel

```txt
in_game/gui/
in_game/common/scripted_guis/
in_game/common/script_values/
in_game/common/scripted_effects/
```

## Dependencies

```txt
Depends on: EPIC US-00, US-10.0, US-10.1, US-10.2, US-10.3, TECH-01
Blocks: transparent stock lifecycle visibility
Related US: US-00-UI, US-04-UI, US-05-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and project debug conventions.
- Debug is mandatory; custom GUI is optional.
- Include the folded US-00-UI requirements: produced, added, rejected, ratio, buffer, void wealth, good price/source, previous/new penalty, affected locations, and modifier mode.
- Show demand type, scope, requested/satisfied/unsatisfied, candidates, scores, quantities, and exclusions.
- Explain that same-market consumption is not trade.
- Explain that logistics costs and trade-income adjustments are outside the surviving MVP story set.
- Keep display read-only.
- Do not create a second authoritative resolver/outcome map for UI. Read US-10.3 aggregates and current transaction diagnostics directly.
- Do not create a second authoritative stock, capacity, production, consumption, transfer, or modifier map for UI.
- Read country stock and country capacity from existing ModeU5 country maps.
- Read market stock and market capacity from existing ModeU5 market aggregate/rebuild records.
- Read monthly production/consumption/transfer figures from existing transaction counters or cached monthly diagnostics.
- Display over-cap stock only as a stock/capacity warning.
- Display overproduction only as current monthly surplus.
- Never treat overproduction as rejected production.
- Never treat over-cap stock as unsatisfied demand.
- Tooltips must distinguish stock pressure, production surplus, and output modifiers.
- If modifier exposure is incomplete, hide the output modifier column or mark it as unavailable rather than guessing.
- If a good has no valid capacity, show usage as `n/a` and raise a diagnostic only when stock exists with zero capacity.

## Mandatory modder/debug layer

The mandatory debug layer explains resolver behavior after US-10.1, US-10.2, and US-10.3 have run.

For each resolved demand, show:

```txt
demand type
scope
requested quantity
satisfied quantity
unsatisfied quantity
candidate list
candidate order
candidate scores
quantity taken per candidate
excluded candidates
exclusion reasons
same-market versus inter-market behavior
```

Same-market consumption must be explicitly labeled as non-trade. Inter-market transfers must show source, target, capacity, requested transfer, actual transfer, and unsatisfied remainder.

## Optional player-facing goods summary

In addition to mandatory resolver debug, US-10-UI may expose a compact read-only player panel summarizing the player's own stock state and current monthly production balance by good.

This panel is not an authoritative stock, capacity, production, consumption, demand, or modifier store. It reads existing ModeU5 stock/capacity records, US-10 monthly resolution counters, and exposed engine modifier values.

### Player-facing row model

For each visible good, show exactly these compact player-facing columns:

```txt
Good
Country Stocks
Market Stocks
Overproduction
Production Efficiency
```

Recommended compact row:

```txt
| Good | Country Stocks | Market Stocks | Overproduction | Production Efficiency |
|---|---|---|---|---|
| Grain | 100/100 | 300/500 | +20%⚠ | +35% |
Iron |  40/100 | 900/500 | -10% | +10% |
Tools | 100/100 | 650/500 | +45%⚠ | +25% |
```

### Column definitions

```txt
country_current_stock =
  player's own ModeU5 stock for selected country x market x good

country_stock_capacity =
  player's own ModeU5 stock capacity for selected country x market x good

country_stocks_display =
  country_current_stock / country_stock_capacity

country_storage_usage =
  if country_stock_capacity > 0:
    country_current_stock / country_stock_capacity
  else:
    n/a

market_current_stock =
  total ModeU5 stock in the selected market x good

market_stock_capacity =
  total ModeU5 stock capacity in the selected market x good

market_stocks_display =
  market_current_stock / market_stock_capacity

market_storage_usage =
  if market_stock_capacity > 0:
    market_current_stock / market_stock_capacity
  else:
    n/a
```

The visible `Country Stocks` column must use the compact `country_current_stock/country_stock_capacity` format. The tooltip must show the full country-owned capacity context:

```txt
Country stock: 100
Country stock capacity: 100
Country usage: 100%
Country free capacity: 0
Country over-cap stock: 0
```

The visible `Market Stocks` column must use the compact `market_current_stock/market_stock_capacity` format. The tooltip must show the full market aggregate context:

```txt
Market stock: 300
Market stock capacity: 500
Market usage: 60%
Market free capacity: 200
Market over-cap stock: 0
```

If either country or market stock is above its matching capacity, mark only that stock value with a warning indicator and expose the matching over-cap quantity in the tooltip:

```txt
Country stock: 130
Country stock capacity: 100
Country usage: 130%
Country over-cap stock: 30

Market stock: 700
Market stock capacity: 650
Market usage: 107.7%
Market over-cap stock: 50
```

`Country Stocks` shows the player's own country-owned stock in the selected market. `Market Stocks` shows the selected market aggregate. The two columns must not be conflated.

### Current overproduction / surplus

The player-facing `Overproduction` column summarizes the current monthly production balance after stock resolution.

```txt
monthly_surplus =
  monthly_production - monthly_consumption - monthly_net_transfers_out
```

Display as a signed percentage when a stable denominator exists:

```txt
surplus_rate =
  - (monthly_surplus / monthly_consumption) # Or the production penalty defined in US-00.3
```
This number should be red if under -5% 



If monthly consumption is zero, do not display a misleading percentage. Show the raw quantity instead:

```txt
Surplus: +20/month
Rate: n/a because monthly consumption is zero
```

The UI label must use `Overproduction` for player readability, while tooltip text must define it as a current monthly surplus, not as over-cap stock and not as rejected production.

### Production Efficiency

Production Efficiency / Output Modifier Visibility

For each visible good, the panel may show a read-only Production Efficiency or Output Modifier display value only when the required engine-exposed components are confirmed.

This value is an MVP visibility aid, not a full recomputation of market production efficiency.

Market production efficiency may be affected by multiple components, including but not limited to:

- global production efficiency (global_production_efficiency) 
- global good-specific output modifiers (global_<good>_output_modifier)
- research effects
- societal values
- market/input conditions
- presence or absence of precursor goods
  examples: cotton for linen, wood for paper, paper for books
- other engine-side production modifiers not yet exposed to ModeU5 script

For MVP, the UI must not guess missing components or present a partial value as complete. If only some components are exposed, the column must clearly label the value as partial, for example:

- global production efficiency (global_production_efficiency) 
- global good-specific output modifiers (global_<good>_output_modifier)

** Warning ** : Others elements might improve your efficiency : (Researches, societal values, presence or absence of precursor goods,...)

If no reliable modifier exposure exists, the column should be hidden or display:

Production Efficiency: unavailable
Reason: required modifier components are not exposed

Tooltip text must distinguish confirmed components from unavailable components:

Confirmed components:
- Global production efficiency: +15%
- Good output modifier: +20%

Unavailable / not yet exposed:
- Research contribution
- Societal value contribution
- Precursor/input availability contribution
- Other engine-side production modifiers

Displayed value: partial +35%
Full production efficiency: unavailable

This display is informational only. It does not recompute production, does not replace the engine's own production calculation, and must not be used as an authoritative economic input.

A future dedicated US-10-UI-1 should define full production-efficiency decomposition once the required modifier and precursor/input exposure is confirmed.

### Scope and selector

The panel should support at least one of these modes:

```txt
Country goods summary:
  one row per good across the player's selected country context

Market goods summary:
  one row per good for the selected market

Good detail:
  one selected good across markets, if later approved
```

MVP should prefer the selected-market summary because `Country Stocks` and `Market Stocks` are both market-relative. Good-detail navigation across markets remains optional.

## US-specific boundary checks

- [ ] Consumption display shows no transport/trade economics.
- [ ] Production admission display shows no direct Estate-income punishment.
- [ ] Void-economy display distinguishes tracked value, previous penalty application, and next-month prepared penalty.
- [ ] Inter-market display shows source, target, capacity, and actual transfer.
- [ ] Exclusion reasons are human-readable and stable.
- [ ] Country Stocks are shown as `country_current_stock/country_stock_capacity` without hiding usage, free capacity, or over-cap details in tooltip.
- [ ] Market Stocks are shown as `market_current_stock/market_stock_capacity` without hiding usage, free capacity, or over-cap details in tooltip.
- [ ] Country and market stock values are visually distinct and not conflated.
- [ ] Stock above capacity is marked as over-cap stock, not overproduction.
- [ ] Current surplus is shown as production balance, not storage overflow.
- [ ] Surplus percentage handles zero consumption safely.
- [ ] Production Efficiency tooltip separates global production efficiency and good-specific output.
- [ ] Missing modifier exposure does not block stock visibility.
- [ ] Player-facing panel remains read-only.

## Acceptance criteria

- [ ] Demand type and all quantity outcomes are visible.
- [ ] Produced, added, rejected, ratio, void wealth, and production-penalty diagnostics are visible.
- [ ] Stocks used, order, score, and quantity per candidate are visible.
- [ ] Excluded candidates and reasons are visible.
- [ ] Same-market versus inter-market behavior is explicit.
- [ ] Requested, transferred, and unsatisfied quantities are separately visible for transfers.
- [ ] No logistics or trade-income adjustment is hidden in this display layer.
- [ ] Player can see one compact row per visible good.
- [ ] Each row shows country-owned stock as `country_current_stock/country_stock_capacity`.
- [ ] Each row shows selected-market aggregate stock as `market_current_stock/market_stock_capacity`.
- [ ] Country and market capacity, usage, free capacity, and over-cap quantity are available in tooltips.
- [ ] Each row shows current overproduction/surplus or deficit where counters exist.
- [ ] Each row shows current Production Efficiency where engine exposure exists.
- [ ] Production Efficiency tooltip shows `global_production_efficiency` and the good-specific output modifier separately.
- [ ] The panel does not create or mutate resolver, stock, capacity, production, demand, or modifier state.

## Manual test scenario

### Setup

```txt
Run one US-00 monthly runtime smoke test, one multi-stock consumption, and one capacity-limited inter-market transfer
Include at-war, embargoed, empty, and wrong-market candidates where exposed.
Include one good at normal country capacity, one good below country capacity, and one good above country capacity. Include at least one market aggregate below capacity and one market aggregate above capacity.
Include one good with positive monthly surplus and one good with negative monthly surplus.
Include one good with both `global_production_efficiency` and a good-specific output modifier exposed.
```

### Expected result

```txt
US-00 shows produced/added/rejected, void wealth, price source, previous/new penalty, and modifier mode
Each demand shows ordered usage and exclusions
Transfer shows actual quantity and states that logistics/trade-income adjustments are out of scope.
The player-facing goods summary shows Good, Country Stocks, Market Stocks, Overproduction, and Production Efficiency.
Country and market stocks are each shown as current/capacity values.
Stock above capacity is marked as over-cap stock, not overproduction.
Overproduction/surplus is shown as a monthly production balance, not a storage overflow.
Production Efficiency tooltip separates global production efficiency from good-specific output modifier.
```

## Known limitations

MVP may rely on deterministic debug events. A full custom stock-resolution panel is outside scope unless explicitly requested.

The player-facing goods summary depends on exposed market aggregates, production, consumption, transfer, and modifier counters. If any exposure is missing, the corresponding column must be hidden, marked unavailable, or kept blocked by TECH-01 rather than guessed.

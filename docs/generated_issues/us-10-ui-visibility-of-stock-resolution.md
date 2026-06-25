# US-10-UI — Visibility of Stock Resolution

Labels: none

## User Story

```txt
US-10-UI — Visibility of Stock Resolution
```

As a player or modder, I want to understand which stocks fulfilled a demand, which were excluded, and why any quantity remained unsatisfied.

## Functional objective

Provide mandatory debug for resolver inputs, ordered candidates, scores, exclusions, quantities per candidate, final outcomes, and the consumption/inter-market distinction; optionally expose a compact ModeU5 goods summary showing good, country stock/capacity, market stock/capacity, current overproduction, and production efficiency components.

## Runtime position

```txt
Monthly step: read after US-10.1/US-10.2/US-10.3
Depends on counters from: US-10.0 through US-10.3
Feeds counters to: player/modder diagnostics
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Resolver/outcome records | demand/country/market/location/good | current transaction diagnostics plus direct reads of US-10.3 outcome maps | CONFIRMED | 007, 040, 067-077 |
| Debug event and logs | effect scope | event triggers and `debug_log` | CONFIRMED | 013 |
| Localization/tooltips | UI | `custom_tooltip`, modifier descriptions, localization keys | CONFIRMED | 014 |
| Optional custom panel | UI | ModeU5 window | OUT_OF_SCOPE | N/A |

## Files expected to change

```txt
in_game/events/
in_game/localization/
docs/technical/DEBUG_CONVENTIONS.md
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

Optional custom panel files, only if the ModeU5 panel is implemented:

```txt
in_game/gui/
in_game/common/scripted_guis/
in_game/common/script_values/
in_game/common/scripted_effects/
```

## Dependencies

```txt
Depends on: US-10.0, US-10.1, US-10.2, US-10.3, TECH-01
Blocks: transparent stock resolution
Related US: US-04-UI
```

## Implementation rules

- Follow `AGENTS.md`, `CLAUDE.md`, and project debug conventions.
- Debug is mandatory; custom GUI is optional.
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

This number should be red if under -5%.

If monthly consumption is zero, do not display a misleading percentage. Show the raw quantity instead:

```txt
Surplus: +20/month
Rate: n/a because monthly consumption is zero
```

The UI label must use `Overproduction` for player readability, while tooltip text must define it as a current monthly surplus, not as over-cap stock and not as rejected production.

### Production Efficiency

For each good, show a read-only `Production Efficiency` display value:

```txt
production_efficiency_display =
  global_production_efficiency
+ global_<good>_output_modifier
```

Tooltip must show the components separately:

```txt
Production efficiency: +15%
Good output modifier: +20%
Displayed production efficiency: +35%
```

The exact good-specific modifier key must be resolved per good from engine modifier exposure, because not every goods key is guaranteed to match the display name.

This display value is informational only. It does not recompute production and does not replace the engine's own production calculation.

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
Run one multi-stock consumption and one capacity-limited inter-market transfer.
Include at-war, embargoed, empty, and wrong-market candidates where exposed.
Include one good at normal country capacity, one good below country capacity, and one good above country capacity. Include at least one market aggregate below capacity and one market aggregate above capacity.
Include one good with positive monthly surplus and one good with negative monthly surplus.
Include one good with both `global_production_efficiency` and a good-specific output modifier exposed.
```

### Expected result

```txt
Each demand shows ordered usage and exclusions.
Consumption is labeled non-trade.
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

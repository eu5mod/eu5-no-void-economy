# US-10 UI fixing trail

This document records the working trail for PR #130 / branch `feature/us10-vanilla-market-selector`.

Purpose: avoid circular debugging by keeping every UI hypothesis, test, result, and decision in one place.

## Source references

Primary UI reference:

```txt
https://github.com/MEIOU-and-Taxes/MnT-EU5/tree/develop/in_game/gui
```

Primary file studied:

```txt
MEIOU-and-Taxes/MnT-EU5@develop/in_game/gui/production_lateralview.gui
```

Primary US-10 UI specification:

```txt
docs/generated_issues/us-10-ui-visibility-of-stock-resolution.md
```

The player-facing compact table columns are: `Good`, `Country Stocks`, `Market Stocks`, `Overproduction`, `Production Efficiency`.

## Latest correction: scaffolded goods generation

The first production-filter patch was intentionally limited to a compact hand-written goods set. That was the wrong maintainability trade-off: US-10 should follow the canonical ModeU5 goods registry, not a manually curated subset.

Current direction:

- `tools/modeu5_goods.sh` remains the canonical list of 74 ModeU5 stock goods.
- `tools/generate_us10_ui_helpers.sh` now scaffolds the US-10 GUI table rows and `produced_by_market` read-model helpers from that list.
- `tools/generate_all.sh` calls the US-10 generator through `bash tools/generate_us10_ui_helpers.sh`.
- New resources added to `modeu5_goods` should be picked up by regeneration instead of requiring manual GUI/scripted-effect edits.

## Current working problem

US-10 needs a Production UI entry that displays ModeU5 stock data by:

```txt
country × market × good
```

Target UX:

1. Production shows a ModeU5 Stocks entry.
2. ModeU5 opens inside the existing Production UI, not as a custom lateralview.
3. Table rows should represent goods produced in the selected market, not merely goods that have stored stock.
4. Columns follow the US-10 spec: country stock / country capacity and market stock / market capacity.
5. Data/table should remain reusable if Plan B later generates a full `production_lateralview.gui` override.

## Current conclusion snapshot

| Topic | Current conclusion |
|---|---|
| Custom `OpenLateralView('modeu5_*')` | Rejected. Runtime reports `Invalid ViewName`; custom lateralview IDs appear hardcoded / not mod-registered. |
| Full override of `production_lateralview.gui` | Worked in-game, but held as Plan B because maintaining a 5,500-line vanilla file manually is patch-fragile. Plan B must be generated/scripted. |
| `scripted_widgets` standalone widget | Rejected. The widget can be loaded/validated, but it is not automatically instantiated into the UI tree. |
| `GetVariableSystem` | Valid as UI state (`Toggle`, `Set`, `Clear`, `Exists`), but it does not provide an injection point by itself. |
| `production_main_tabs` injection | Valid for adding a visible top tab. Not a final body injection point. |
| `production_view_subtabs` injection | Validated. It can mount an inline ModeU5 body in the existing Production flow. |
| Current best direction | Plan A remains viable for V0: Production-hosted inline body, compact fixed-width table, explicit Sync/hover-sync, and generated production-based row visibility. |

## M&T / vanilla Production observations

### `production_main_tabs`

M&T keeps `production_main_tabs` as the top-level lateralview selector. The vanilla-style tabs call known lateralview IDs only:

```gui
OpenLateralView('production')
OpenLateralView('goods_production')
OpenLateralView('food_production')
OpenLateralView('town_rights')
```

This supports the current architecture: do not call `OpenLateralView('modeu5_*')`. ModeU5 calls `OpenLateralView('production')` and sets internal UI state.

### `production_view_subtabs`

M&T uses `production_view_subtabs` as an internal display/control strip. It has valid `ProductionView` context and can be overridden without a full `production_lateralview.gui` copy.

As of `a7ed5a0`, a static ModeU5 placeholder rendered inline inside Production. As of `db6936c`, a real table-shaped UI rendered. As of `9271b3b`, table/panel split and selected-market sync were in place.

### Vanilla market selector pattern

Vanilla market selection is tied to a parent filtered list and `ProductionView.GetSelectedMarket`. M&T's Production selector uses `ProductionSelectMarket.Parent.FilterByMarket(Market.Self)` on the selected market card.

V1 selector-hook result:

- `zz_modeu5_us10_production_select_market.gui` attempted to override the selector and add a ModeU5 refresh after `ProductionSelectMarket.Parent.FilterByMarket(Market.Self)`.
- Runtime result: the table still refreshed only through hover or explicit Sync; no selector-file GUI error was logged.
- Conclusion: the separate selector file is not a reliable Plan A hook. It either did not override the active selector instance, or the active click path is not the path copied into the standalone file.
- Decision: remove the selector hook and keep Plan A to table + hover-sync + explicit Sync. True click-time selector sync belongs in Plan B, where the original selector can be patched inside the full generated `production_lateralview.gui`.

### Selected-market label versus table refresh

The `Selected market` label changes automatically because it is a live GUI binding to `ProductionView.GetSelectedMarket` and `Market.GetName`.

The table does not automatically recalculate from that binding because it reads ModeU5 variables materialised on `Player.MakeScope` by scripted effects. Jomini text binding re-evaluates display accessors, but it does not cascade into a scripted effect when the view-model value changes.

### Good icons

M&T uses static trade-good icon textures in the pattern:

```gui
icon = { size = { 20 20 } texture = "gfx/interface/icons/trade_goods/icon_goods_cloth.dds" texture_density = 2 }
```

For the compact ModeU5 V0 table, the first column is an icon column, not a text-good-name column. Use `gfx/interface/icons/trade_goods/icon_goods_<good>.dds` for known goods. Keep a tooltip/name follow-up for later if needed.

## Trail of attempts and results

| Step | Change / hypothesis | Result | Decision |
|---|---|---|---|
| 1 | Custom ModeU5 lateralview via `OpenLateralView('modeu5_*')`. | Fails with `Invalid ViewName`. | Rejected. |
| 2 | Full `production_lateralview.gui` override. | Worked visually. | Held as Plan B due maintenance risk. |
| 3 | `scripted_widgets` standalone widget. | Loaded but did not instantiate globally. | Rejected. |
| 4 | Override `production_main_tabs`. | Top ModeU5 tab appears. | Keep only as selector/state entry. |
| 5 | Floating overlay/window. | Bad positioning, input capture/freeze risk. | Rejected. |
| 6 | Static inline placeholder via `production_view_subtabs`. | Appears in Production. | Validates Plan A injection point. |
| 7 | Coverage probe using `position`. | GUI error: layout children cannot use `position`. | Rejected. |
| 8 | Coverage probe using `margin_top`. | GUI error: `margin_top` not handled on this widget. | Rejected. |
| 9 | Table iteration. | Table appears; selected market name and values update through Sync. | Good enough visually. |
| 10 | Taller panel + best-effort auto-sync. | Works through hover; not true selector-click sync. | Keep for Plan A. |
| 11 | V1 standalone market selector hook. | No visible automatic click-sync effect. | Removed. |
| 12 | Increase panel height to `940` and move hover-sync to whole ModeU5 body. | Works visually; panel covers enough for V0, but not a true replacement of search/selector. | Keep. |
| 13 | All-goods generated table filtered by `modeu5_us10_ui_<good>_produced`. | Runtime showed an empty table because the country-level US-00 produced ledger was not a reliable vanilla-production presence signal. | Rejected. |
| 14 | Stock-bearing visibility: country stock > 0 OR market stock > 0 OR overproduction > 0. | Rows reappeared. Later screenshots showed the visible-good list stayed suspiciously similar across markets. | Reclassed as temporary debug workaround only. |
| 15 | All-goods hardcoded table. | Suspected to make `Loading Game resources` heavier. | Rejected as a manual approach; generator is the maintainable route. |
| 16 | Right-align value columns and remove `the Good`. | UI still displayed `the Good`; log showed file was loaded and `text` localization was being parsed. | Header issue likely caused by localization/key handling; use direct `raw_text = "Good"` and icon first column. |
| 17 | Fixed row height using only `size = { -1 26 }`. | Visual row height did not materially change; rows still distributed across the scroll area. | Use `minimumsize`/`maximumsize` and `set_parent_dimension_to_minimum = height`. |
| 18 | Overproduction values used `text = "[...|2]%"`. | Runtime emitted `Unlocalized text '[...overproduction_percent...]%'` warnings. | Use `raw_text` for dynamic literal formatted values. |
| 19 | Compact icon rows. | In-game screenshots show major improvement, but columns overflowed/escaped the panel. | Fix with fixed-width compact columns. |
| 20 | Production-based row visibility. | User observed same-good rows across Lisboa and Burgos; stock presence is not the right Production-table filter. | Use `modeu5_us10_ui_<good>_produced_by_market > 0`, aggregated across countries present in the selected market. |
| 21 | Hand-written compact goods set for `produced_by_market`. | Not maintainable and not aligned to the 74-good registry. | Replace with `tools/generate_us10_ui_helpers.sh` scaffolded from `tools/modeu5_goods.sh`. |

## Current implementation notes

- `modeu5_us10_stock_table.gui` contains reusable table templates and should be generated by `tools/generate_us10_ui_helpers.sh`.
- The table still follows the US-10 spec columns, but headers are compact labels to fit the Production panel: `Good`, `Country`, `Market`, `Overprod.`, `Eff.`.
- Value columns are fixed width and right-aligned to prevent overflow into the map.
- The first column is an icon column using `gfx/interface/icons/trade_goods/icon_goods_<good>.dds`.
- Rows should be emitted for all 74 ModeU5 goods from `tools/modeu5_goods.sh`.
- Rows are hidden unless `modeu5_us10_ui_<good>_produced_by_market > 0`.
- `modeu5_us10_ui_<good>_produced_by_market` is a selected-market aggregate computed from the ModeU5 US-00 produced ledger across countries present in the market.
- Stock presence alone is not a Production-row visibility gate; stock-bearing visibility was only a temporary debugging workaround.
- Country and market stocks are displayed as `current/capacity`.
- `Production Efficiency` remains `n/a`, per the spec instruction not to guess when modifier exposure is incomplete.
- `modeu5_us10_stock_lateralview.gui` is a reusable panel shell.
- `zz_modeu5_us10_production_subtabs.gui` hides the vanilla display/employment/automation strip when ModeU5 is active.
- `zz_modeu5_us10_production_tabs.gui` opens vanilla Production, sets `modeu5_us10_stock_tab`, and refreshes the read-model.
- Hover auto-sync is still best-effort; explicit `Sync` remains the reliable fallback.

## Important runtime log learnings

Probably noise for US-10 UI:

```txt
Could not clone setting 'anti_aliasing'
Could not clone setting 'portrait_multi_sampling'
Variable '...' is set but is never used
Found sentinel file from a previous boot
pdxinput_context.cpp:2896 Could not push the provided stack context. ID: 0
```

Actionable logs:

```txt
Invalid ViewName: 'modeu5_*'
Duplicated key modeu5_us10_ui_*
Could not find widget 'modeu5_us10_stock'
Property 'ignoreinvisible' not handled
Unsupported property: size with a percentage on widgets that are a child of a vbox/hbox
Unsupported property: position on widgets that are a child of a hbox/vbox
Property 'margin_top' not handled
Unlocalized text '[Player.MakeScope.GetVariable(...overproduction_percent...).GetValue|2]%' -> use raw_text, not text
```

## Current branch state

- Top ModeU5 tab exists and opens Production.
- Inline ModeU5 panel exists inside Production.
- Table/panel are separated for reuse.
- US-10 UI rows and selected-market production helper are now scaffolded from the canonical goods list.
- Top tab / Sync / hover-sync refresh through `modeu5_us10_ui_prepare_current_market_table_for_production_ui`.
- No standalone selector override remains.

## Current validation checklist

```txt
git fetch origin
git reset --hard origin/feature/us10-vanilla-market-selector
git rev-parse --short HEAD
bash tools/generate_us10_ui_helpers.sh
./tools/validate_module_packages.sh
git diff --check
```

In-game checks:

1. ModeU5 panel still opens inside Production.
2. Table rows still show after Sync/hover refresh.
3. First column uses icons, not text names.
4. Header uses compact labels and does not show `the Good`.
5. Numeric columns are right-aligned.
6. Row height is compact.
7. Columns no longer overflow into the map.
8. Goods list changes by selected market because visibility uses `produced_by_market`.
9. No GUI errors for `minimumsize` / `maximumsize` / `set_parent_dimension_to_minimum`.
10. No `Unlocalized text` warning for overproduction values.
11. No missing texture errors for the full ModeU5 goods set.

## Plan B trigger

Move to generated full `production_lateralview.gui` override if Plan A cannot cover/replace vanilla Buildings content cleanly enough for a V0 that can be handed to a UI specialist, or if true selector-click sync is required for V0 acceptance.

Plan B must be generated/scripted, not manually copied, and should patch stable anchors in vanilla/M&T `production_lateralview.gui` so later updates can fail fast if anchors move.

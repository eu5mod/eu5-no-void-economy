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

M&T is the primary reference for `ProductionView`, `OpenLateralView`, `filtered_sorted_list`, and market selector behavior. Vic3/CK3 are secondary references only for broad Jomini GUI state patterns such as `GetVariableSystem`.

Primary US-10 UI specification:

```txt
docs/generated_issues/us-10-ui-visibility-of-stock-resolution.md
```

The player-facing compact table columns are: `Good`, `Country Stocks`, `Market Stocks`, `Overproduction`, `Production Efficiency`.

## Testing cadence decision

Manual EU5 testing costs about 5 minutes per run. We group safe analysis/code changes into coherent batches and request one test only when the batch should answer a specific question. Emergency single-commit tests are reserved for freeze/crash/input-lock fixes.

## Current working problem

US-10 needs a Production UI entry that displays ModeU5 stock data by:

```txt
country × market × good
```

Target UX:

1. Production shows a ModeU5 Stocks entry.
2. ModeU5 opens inside the existing Production UI, not as a custom lateralview.
3. Table shows one line per visible stock-bearing good in the selected market/country read-model.
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
| Current best direction | Plan A is good enough for a V0 hand-off if height and table rendering are acceptable; full automatic selector-click sync was not achieved in Plan A. |

## Plan A acceptance criteria

Plan A is acceptable only if the inline body looks like a credible active Production body, not like a small probe card.

Acceptance criteria from the user:

1. The inline panel must descend to the bottom of the visible screen/body so the Buildings list is covered or pushed out of the visible area.
2. The panel should cover as much as possible of the Buildings-only controls. Search may remain a later UI-specialist topic if hiding it cleanly requires a deeper override.
3. The probe text must be removed and replaced with a real table structure.
4. If vertical coverage remains unacceptable, move to Plan B generated override.

## M&T / vanilla Production observations

### `production_main_tabs`

M&T keeps `production_main_tabs` as the top-level lateralview selector. The vanilla-style tabs call known lateralview IDs only:

```gui
OpenLateralView('production')
OpenLateralView('goods_production')
OpenLateralView('food_production')
OpenLateralView('town_rights')
```

This supports Chris's recommendation: do not call `OpenLateralView('modeu5_*')`. ModeU5 can call `OpenLateralView('production')` and set internal UI state.

### `production_lateralview` body structure

M&T defines the actual `production_lateralview` root and places the top tabs in `panel_content` with:

```gui
header_main_tabs = {
    blockoverride "content" {
        using = production_main_tabs
    }
}
```

Then the body is a main `vbox` containing several `filtered_sorted_list` blocks. The body is largely driven by `ProductionView.Vars('display')`.

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

For the compact ModeU5 V0 table, the first column should be an icon column, not a text-good-name column. Use `gfx/interface/icons/trade_goods/icon_goods_<good>.dds` for known goods. Keep a tooltip/name follow-up for later if needed.

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
| 13 | Rebuild table to spec columns and generated static row list for all ModeU5 stock goods, visible only when produced > 0. | Runtime showed an empty table because `*_produced` is a ModeU5 ledger value and not a vanilla-production presence signal. | Rejected. |
| 14 | Change row visibility to stock-bearing/overproduction signals: country stock > 0 OR market stock > 0 OR overproduction > 0. | Rows reappeared. | Keep for V0. |
| 15 | All-goods hardcoded table. | Suspected to make `Loading Game resources` heavier. | Rejected for V0; prefer compact row set. |
| 16 | Right-align value columns and remove `the Good`. | UI still displayed `the Good`; log showed file was loaded and `text` localization was being parsed. | Header issue likely caused by localization/key handling; use direct `raw_text = "Good"` and icon first column. |
| 17 | Fixed row height using only `size = { -1 26 }`. | Visual row height did not materially change; rows still distributed across the scroll area. | Use `minimumsize`/`maximumsize` and `set_parent_dimension_to_minimum = height`. |
| 18 | Overproduction values used `text = "[...|2]%"`. | Runtime emitted `Unlocalized text '[...overproduction_percent...]%'` warnings. | Use `raw_text` for dynamic literal formatted values. |
| 19 | Compact icon rows. | Pending test at commit `6f2c144`. | Current batch. |

## Latest implementation notes

- `modeu5_us10_stock_table.gui` contains reusable table templates.
- The table follows the compact US-10 player-facing spec: `Good`, `Country Stocks`, `Market Stocks`, `Overproduction`, `Production Efficiency`.
- V0 now intentionally keeps a compact stock-bearing row set rather than all-goods hardcoding, because all-goods GUI expansion is heavier during `Loading Game resources` and fragile while Plan A is still stabilising.
- Rows are hidden unless the selected market/country read-model has country stock, market stock, or overproduction for that good.
- Do not use `modeu5_us10_ui_<good>_produced` as the GUI row visibility gate; the current US-00 produced ledger does not read vanilla production directly.
- Country and market stocks are displayed as `current/capacity`.
- `Production Efficiency` remains `n/a`, per the spec instruction not to guess when modifier exposure is incomplete.
- `modeu5_us10_stock_lateralview.gui` is a reusable panel shell.
- `zz_modeu5_us10_production_subtabs.gui` hides the vanilla display/employment/automation strip when ModeU5 is active.
- `zz_modeu5_us10_production_tabs.gui` refreshes the ModeU5 table when opened from the top tab.
- The ineffective standalone selector hook file was removed.
- Panel height is now `940`.
- Hover auto-sync is now on the whole ModeU5 panel and the selected-market strip.
- The explicit `Sync` button remains as fallback.
- First column is now intended to be icons using `gfx/interface/icons/trade_goods/icon_goods_<good>.dds`.
- Value columns are intended to be right-aligned.
- Dynamic values that include literal suffixes such as `%` must use `raw_text`, not `text`, to avoid localization warnings.

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

Things to watch after compact icon-row update:

```txt
gui/modeu5_us10_stock_table.gui
minimumsize / maximumsize on hbox rows
set_parent_dimension_to_minimum = height
icon_goods_<good>.dds texture availability
raw_text for all dynamic value cells with literal suffixes
```

## Current branch state

- Top ModeU5 tab exists and opens Production.
- Inline ModeU5 panel exists inside Production.
- Table/panel are separated for reuse.
- Top tab refreshes existing ModeU5 read-model.
- Inline Sync action uses the actual `ProductionView.GetSelectedMarket` context.
- Best-effort hover auto-sync exists on the whole panel.
- No standalone selector override remains.
- Current table is compact, stock-bearing, spec-column based, and should render a good icon first column.
- Current head after logging this file is expected to be newer than `6f2c144`; check PR head before testing.

## Plan B trigger

Move to generated full `production_lateralview.gui` override if Plan A cannot cover/replace vanilla Buildings content cleanly enough for a V0 that can be handed to a UI specialist, or if true selector-click sync is required for V0 acceptance.

Plan B must be generated/scripted, not manually copied, and should patch stable anchors in vanilla/M&T `production_lateralview.gui` so later updates can fail fast if anchors move.

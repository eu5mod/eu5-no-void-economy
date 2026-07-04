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
3. Table shows one line per good produced in the selected market.
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
| Current best direction | Plan A is good enough for a V0 hand-off if height is acceptable; full automatic selector-click sync was not achieved in Plan A. |

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
| 12 | Increase panel height to `940` and move hover-sync to whole ModeU5 body. | Pending test. | Current batch. |

## Latest implementation notes

- `modeu5_us10_stock_table.gui` contains reusable table templates.
- `modeu5_us10_stock_lateralview.gui` is a reusable panel shell.
- `zz_modeu5_us10_production_subtabs.gui` hides the vanilla display/employment/automation strip when ModeU5 is active.
- `zz_modeu5_us10_production_tabs.gui` refreshes the ModeU5 table when opened from the top tab.
- The ineffective standalone selector hook file was removed.
- Panel height is now `940`.
- Hover auto-sync is now on the whole ModeU5 panel and the selected-market strip.
- The explicit `Sync` button remains as fallback.

## Important runtime log learnings

Probably noise for US-10 UI:

```txt
Could not clone setting 'anti_aliasing'
Could not clone setting 'portrait_multi_sampling'
Variable '...' is set but is never used
Found sentinel file from a previous boot
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
```

Things to watch after height/whole-panel hover-sync:

```txt
gui/modeu5_us10_stock_lateralview.gui
Property 'size'
ProductionView.GetSelectedMarket.MakeScope
```

## Current branch state

- Top ModeU5 tab exists and opens Production.
- Inline ModeU5 panel exists inside Production.
- Table/panel are separated for reuse.
- Top tab refreshes existing ModeU5 read-model.
- Inline Sync action uses the actual `ProductionView.GetSelectedMarket` context.
- Best-effort hover auto-sync exists on the whole panel.
- No standalone selector override remains.

## Plan B trigger

Move to generated full `production_lateralview.gui` override if Plan A cannot cover/replace vanilla Buildings content cleanly enough for a V0 that can be handed to a UI specialist, or if true selector-click sync is required for V0 acceptance.

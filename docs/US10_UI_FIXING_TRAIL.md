# US-10 UI fixing trail

This document records the working trail for PR #130 / branch `feature/us10-vanilla-market-selector`.

Purpose: avoid circular debugging by keeping every UI hypothesis, test, result, and decision in one place.

## Source references

Primary UI reference for this trail:

```txt
https://github.com/MEIOU-and-Taxes/MnT-EU5/tree/develop/in_game/gui
```

Primary file currently studied:

```txt
MEIOU-and-Taxes/MnT-EU5@develop/in_game/gui/production_lateralview.gui
```

Rationale:

- M&T is an active EU5 GUI mod source, closer than Vic3/CK3 examples.
- Vic3/CK3 remain useful only for broad Jomini GUI state patterns, especially `GetVariableSystem`, not for EU5 `ProductionView` / `OpenLateralView` behavior.

## Testing cadence decision

Manual EU5 testing costs about 5 minutes per run. We will therefore stop asking for one test per micro-commit unless the commit is a risky crash/freeze fix.

Working cadence:

1. Accumulate a small coherent batch of analysis + code changes.
2. Update this trail before asking for a test.
3. Ask for one test only when the batch should answer a specific question.
4. The requested test must include the expected visible result and the expected relevant log changes.
5. Keep emergency single-commit tests only for freeze/crash/input-lock fixes.

## Current working problem

US-10 needs a Production UI entry that displays ModeU5 country-stock data by:

```txt
country × market × good
```

Target UX:

1. Production shows a ModeU5 Stocks entry.
2. ModeU5 opens inside the existing Production UI, not as a custom lateralview.
3. Market selector uses a vanilla-like market card/list pattern.
4. Table shows one line per good produced in the selected market.
5. Icon/aesthetic polish only after the interaction model is stable.

## Current conclusion snapshot

| Topic | Current conclusion |
|---|---|
| Custom `OpenLateralView('modeu5_*')` | Rejected. Runtime reports `Invalid ViewName`; custom lateralview IDs appear hardcoded / not mod-registered. |
| Full override of `production_lateralview.gui` | Worked in-game, but rejected architecturally because it copies too much vanilla UI and is patch-fragile. |
| `scripted_widgets` standalone widget | Rejected. The widget can be loaded/validated, but it is not automatically instantiated into the UI tree. |
| `GetVariableSystem` | Valid as UI state (`Toggle`, `Set`, `Clear`, `Exists`), but it does not provide an injection point by itself. |
| `production_main_tabs` injection | Valid for adding a visible top tab. Rejected as final body injection point. |
| Current best direction | ModeU5 should be a Production-hosted internal display mode/body, not a custom lateralview and not a floating overlay. |
| Current risk | We do not yet have a clean additive body injection point without overriding a larger part of `production_lateralview.gui`. |

## M&T / vanilla Production observations

### `production_main_tabs`

M&T keeps `production_main_tabs` as the top-level lateralview selector. The vanilla-style tabs call known lateralview IDs only:

```gui
OpenLateralView('production')
OpenLateralView('goods_production')
OpenLateralView('food_production')
OpenLateralView('town_rights')
```

Observation:

- This supports the idea that top tabs are only view selectors.
- ModeU5 should not call `OpenLateralView('modeu5_*')`.
- If ModeU5 is attached here, it can call `OpenLateralView('production')` and then set an internal UI state.
- However, `production_main_tabs` is not a good final body injection point. It is a selector row, not the body area. Injecting body here caused clipping / missing panel / overlay behavior.
- Test result confirmed this: a top-tab ModeU5 state can exist while the actual body remains the vanilla Production/Buildings body.

### `production_lateralview` body structure

M&T defines the actual `production_lateralview` root and places the top tabs in `panel_content` with:

```gui
header_main_tabs = {
    blockoverride "content" {
        using = production_main_tabs
    }
}
```

Then the body is a main `vbox` containing several `filtered_sorted_list` blocks.

Important observed body blocks:

```gui
filtered_sorted_list = {
    visible = "[ProductionView.Vars.NotExistOrHasValue( 'display', 'lists' )]"
    name = "production_filtered_list"
    ...
}

filtered_sorted_list = {
    visible = "[ProductionView.Vars.HasValue( 'display', 'cards' )]"
    name = "building_categories_filtered_list"
    ...
}
```

Observation:

- The body is not driven by `GetVariableSystem` at this level; it is driven by `ProductionView.Vars('display')`.
- The cleanest body integration is likely to add a new `filtered_sorted_list`/body block visible when `display = modeu5_stocks`.
- But that likely requires overriding more of the `production_lateralview` root than the current `production_main_tabs` micro-override.

### `production_view_subtabs`

M&T has an internal display-mode template called `production_view_subtabs`.

It uses `ProductionView.Vars.Set('display', ...)` and `ProductionView.Vars.HasValue(...)` / `NotExistOrHasValue(...)` to toggle internal body modes such as:

```gui
ProductionView.Vars.Set('display', 'lists')
ProductionView.Vars.Set('display', 'cards')
ProductionView.Vars.Set('display', 'foreign')
ProductionView.Vars.Set('display', 'estate')
```

Observation:

- This is closer to what ModeU5 needs than a top-level lateralview.
- Best candidate direction: ModeU5 should become an internal Production display mode, not a separate lateralview.
- Earlier attempts to call `ProductionView.Vars.Set(...)` from the top tab row failed because the tab template did not have a valid `ProductionView` context. Inside `production_view_subtabs`, the context should be correct.
- However, `production_view_subtabs` is inserted inside each visible `filtered_sorted_list` through `searchbar_extra_pre_content`.
- If we set `display = modeu5_stocks`, the existing `lists`/`cards` lists may hide, which can also hide the subtab template that would hold the ModeU5 button/body.
- Therefore, overriding only `production_view_subtabs` may be enough for a button, but probably not enough for a full body unless we also add a ModeU5 body block in the lateralview content.

### Vanilla market selector pattern

M&T/vanilla do not simply render an inline market-card datamodel for market selection inside Production. They use a dedicated `select_menu_left` block with:

```gui
select_menu_left = {
    datacontext = "[GetQuickVisibleMarkets(Player.Self)]"
    blockoverride "menu_setup" {
        name = "production_select_market"
    }
    ...
    datamodel = "[QuickVisibleMarkets.GetVisibleMarkets]"
    ...
    on_action = "[ProductionSelectMarket.Parent.FilterByMarket(Market.Self)]"
}
```

The menu is opened from a parent filtered list with:

```gui
ProductionView.ToggleProductionSelectMarket(PdxGuiWidget.FindParent('production_filtered_list').Self)
```

Observation:

- This is the strongest market-selector learning so far.
- Vanilla market selection is tied to a parent widget/list (`production_filtered_list` or `building_categories_filtered_list`).
- The selected market is applied by `ProductionSelectMarket.Parent.FilterByMarket(Market.Self)`.
- For ModeU5 we should not yet clone the full market selector. First we need a stable body/list parent. Then we can either:
  - reuse the vanilla select-menu pattern if we can attach it to our ModeU5 parent list; or
  - emulate it only after the body is stable.

### Market card / market navigation patterns

M&T/vanilla use market context functions and market list/card patterns, including:

```gui
GetQuickVisibleMarkets(Player.Self)
QuickVisibleMarkets.GetVisibleMarkets
Market.GetCountryPopulation(Player.Self)
Market.GetTotalMerchantCapacity(Player.Self)
SetUIFocusMarket(Market.Self)
ShowGoodsProductionViewWithMarketAndFilter(...)
ShowFoodProductionViewWithMarket(...)
```

Observation:

- We should keep vanilla market cards as inspiration, but not reintroduce dynamic datamodels until the static ModeU5 body is stable.
- For US-10 market filtering, the debated hook remains `every_market_present_in_country`. Do not replace it with `every_owned_location` until its runtime semantics are confirmed.

## Trail of attempts and results

| Step | Change / hypothesis | Result | Decision |
|---|---|---|---|
| 1 | Create custom ModeU5 lateralview and open it via `OpenLateralView('modeu5_*')`. | Fails with `Invalid ViewName`. | Rejected. Custom lateralviews appear not registered by mod files alone. |
| 2 | Full override `production_lateralview.gui`, add a ModeU5 tab and table. | Worked: tab/table visible in game. Also produced `ProductionView` context warnings. | Functionally proven, architecturally rejected as too patch-fragile. |
| 3 | Use `scripted_widgets` with standalone root widget. | First failed because widget root was not found. After root fix, loaded but did not appear. | Rejected as injection mechanism. It registers/loads but does not instantiate globally. |
| 4 | Add ModeU5 tab by overriding `production_main_tabs`; use `GetVariableSystem.Toggle`. | Tab appears. Good proof that micro tab override works. | Keep this part, but ensure state does not conflict with other vanilla tabs. |
| 5 | Inject a movable overlay/window from the tab template. | Panel appeared once but was badly positioned, captured input, and could freeze the game when datamodel/read-model logic ran. | Rejected as final body strategy. Avoid floating overlay and heavy click actions. |
| 6 | Replace body with safe static placeholder; remove scripted refresh and datamodel. | Safer, but latest report: tab can be active while another lateralview is active; placeholder not visible. | Need to move body injection into Production body, not tab row. |
| 7 | Make ModeU5 a Production sub-mode by clicking `OpenLateralView('production')` then `GetVariableSystem.Set(...)`. | Negative test on `12086c9`: clicking ModeU5 opens the Buildings panel; no ModeU5 body is visible. Logs are mostly noisy unused-variable warnings and no decisive GUI parser error. | Confirms top-tab state alone is insufficient. `OpenLateralView('production')` simply opens vanilla Buildings because no Production body display mode was actually added. |

## Test notes

### 2026-07-04 — `source_commit=12086c901e68c2803a4a70b21a35b64834b901d5`

User result:

- Negative.
- Clicking `ModeU5 Stocks` goes to the vanilla Buildings panel.
- No ModeU5 panel/body visible.
- Logs contain the usual `anti_aliasing` / `portrait_multi_sampling` noise and many `Variable ... is set but is never used` warnings.
- No strong GUI parse error was reported for this commit.

Interpretation:

- This commit proved that `OpenLateralView('production') + GetVariableSystem.Set(...)` is not enough.
- It only selects the vanilla Production lateralview.
- The actual body must be part of Production's `panel_content` display system, most likely as a `ProductionView.Vars('display')` mode and a matching body block.

## Important runtime log learnings

### Logs that are probably noise for US-10 UI

```txt
Could not clone setting 'anti_aliasing'
Could not clone setting 'portrait_multi_sampling'
Variable '...' is set but is never used
```

These are noisy but have not correlated with the tab/body failure.

### Logs that were actionable

```txt
Invalid ViewName: 'modeu5_*'
```

Custom lateralview open failed.

```txt
Duplicated key modeu5_us10_ui_rebuild_country_market_selector
Duplicated key modeu5_us10_ui_capture_good_row
```

Scripted effect shadowing via duplicate keys does not work. Modify the original effect file instead of creating duplicate-key override files.

```txt
Could not find widget 'modeu5_us10_stock'
```

The scripted widget root was wrong.

```txt
Property 'ignoreinvisible' not handled
```

Unsupported root property for the attempted scripted widget.

```txt
Unsupported property: size with a percentage on widgets that are a child of a vbox/hbox
```

Do not use `size = { 100% 100% }` inside hbox/vbox children. Use fixed size, `-1`, layout policies, or place it somewhere else.

```txt
Could not push the provided stack context. ID: 0
```

Still unclear. It appeared even outside hard GUI failures. Treat as warning unless directly tied to a click/freeze.

## Current branch state at time of this update

Latest known code state before this document update:

- `zz_modeu5_us10_production_tabs.gui` overrides `production_main_tabs`.
- ModeU5 tab uses `OpenLateralView('production')` + `GetVariableSystem.Set('modeu5_us10_stock_tab','yes')`.
- Other production tabs clear `modeu5_us10_stock_tab`.
- `modeu5_us10_stock_lateralview.gui` is currently a safe static placeholder template.
- Heavy refresh/read-model and dynamic market datamodel are intentionally removed from the tab click.

Current assessment:

- The tab part is validated.
- The body part is not validated and is currently in the wrong place.
- The next code batch should focus on body display-mode integration, not market cards or goods rows.

## Proposed next fixing sequence

Do not add market cards or stock rows until these are resolved in order.

### Fix 1 — tab state only

Goal:

- Clicking ModeU5 opens Production and sets only ModeU5 as active.
- Clicking Buildings/Goods/Food/Locations clears ModeU5.
- No freeze.
- No body required yet.

Status:

- Partially validated: tab exists.
- Negative: top-tab state alone can still show vanilla Buildings body.

### Fix 2 — body injection point

Goal:

- Find the correct Production body template / block to conditionally display a static ModeU5 placeholder.
- Avoid a movable window and avoid overlay behavior.

Candidate direction:

- Investigate `production_view_subtabs` and adjacent content templates.
- Add an internal display mode where possible:

```gui
ProductionView.Vars.Set('display', 'modeu5_stocks')
visible = "[ProductionView.Vars.HasValue('display', 'modeu5_stocks')]"
```

Only do this inside templates that already have `ProductionView` context.

Current caution:

- Adding a ModeU5 button to `production_view_subtabs` is likely easy.
- Showing a ModeU5 body probably requires a corresponding `filtered_sorted_list`/body block visible under `display = modeu5_stocks`.
- That may require a larger override than `production_main_tabs`, but still much smaller and more deliberate than the first accidental full override.

### Fix 3 — static ModeU5 body

Goal:

- Show a static placeholder inside Production body.
- No market selector.
- No stock variables.
- No scripted GUI.

### Fix 4 — market selector visual only

Goal:

- Add market list/cards without changing ModeU5 backend state on click.
- Confirm layout and performance first.

### Fix 5 — market selection backend

Goal:

- Pass clicked `Market.MakeScope` safely to a scripted GUI.
- Refresh only after click works.

### Fix 6 — produced goods rows

Goal:

- Show only goods produced in selected market.
- Use original effect file, no duplicate override file.
- Validate `is_produced_in_market` syntax before expanding all goods.

## Working rules from now on

1. One layer per commit.
2. No more heavy datamodel + scripted GUI + layout change in the same commit.
3. Every test result must update this document.
4. Avoid full `production_lateralview.gui` override unless no smaller stable injection point exists.
5. Treat M&T/vanilla Production as primary reference; Vic3/CK3 are secondary references for general Jomini GUI patterns only.
6. Because in-game tests cost several minutes, group safe analysis/code cleanups into coherent batches and ask for one test per batch, not one test per commit.

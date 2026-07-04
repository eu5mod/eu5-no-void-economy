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
| Current approach | Use vanilla Production as host; add a ModeU5 tab/button; inject body into an already-instantiated Production UI area. |
| Current risk | We are still injecting the body too close to `production_main_tabs`; this caused clipping / missing panel / overlay input problems. |

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
- If ModeU5 is attached here, it should probably call `OpenLateralView('production')` and then set an internal UI state.
- However, `production_main_tabs` is not a good final body injection point. It is a selector row, not the body area. Injecting body here caused clipping / missing panel / overlay behavior.

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
- Next likely path: override/extend `production_view_subtabs` to add a ModeU5 internal display button, then use the same `ProductionView.Vars` state to show/hide a ModeU5 body area.

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
| 7 | Make ModeU5 a Production sub-mode by clicking `OpenLateralView('production')` then `GetVariableSystem.Set(...)`. | Pending test. | Transitional only. Long-term likely should use `ProductionView.Vars` inside body/subtab context. |

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

## Current branch state at time of trail creation

Latest known code state before this document:

- `zz_modeu5_us10_production_tabs.gui` overrides `production_main_tabs`.
- ModeU5 tab uses `OpenLateralView('production')` + `GetVariableSystem.Set('modeu5_us10_stock_tab','yes')`.
- Other production tabs clear `modeu5_us10_stock_tab`.
- `modeu5_us10_stock_lateralview.gui` is currently a safe static placeholder template.
- Heavy refresh/read-model and dynamic market datamodel are intentionally removed from the tab click.

## Proposed next fixing sequence

Do not add market cards or stock rows until these are resolved in order.

### Fix 1 — tab state only

Goal:

- Clicking ModeU5 opens Production and sets only ModeU5 as active.
- Clicking Buildings/Goods/Food/Locations clears ModeU5.
- No freeze.
- No body required yet.

Expected result:

- No double-selected Locations + ModeU5 state.

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

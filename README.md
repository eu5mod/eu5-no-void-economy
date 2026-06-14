# ModeU5 — Country Stocks Within Markets

ModeU5 adds a double-accounting layer for goods inside EU5 markets.

The mod does **not** replace the vanilla market system. It adds a stock, control, debug, and consistency layer so that economic value can be checked against goods that actually enter stock.

## Core invariant

```txt
market_good_stock = sum(country_market_good_stock)
```

The country-level stock is the source of truth. Market-level stock is an aggregate/cache.

If the invariant breaks, ModeU5 rebuilds `market_good_stock` from country stocks, never the reverse.

## Non-negotiable stock rule

No feature may mutate stock variables directly. All stock mutations must go through centralized scripted effects:

```txt
modeu5_add_stock
modeu5_remove_stock
modeu5_transfer_stock
modeu5_decay_stock
modeu5_rebuild_market_stock_from_country_stocks
modeu5_validate_stock_consistency
```

## Current MVP specification baseline

The bootstrap documents are aligned with the revised MVP specification:

- double accounting of `country_market_good_stock` and `market_good_stock`;
- centralized stock mutation effects;
- US-00 void economy tracking and future production correction;
- US-10 stock-based consumption and inter-market transfer resolution;
- no ModeU5 intra-market trade simulation;
- optional Economy Rebalance US-05 direct Economic Base replacement for Stability and legitimacy-producing Court/Government Power only;
- no transport-cost, trade-income reconciliation, slider reconciliation, or AI-planning story in the surviving MVP set;
- mandatory debug and TECH-01 exposure tracking.

## Module choices

ModeU5 uses packages rather than a misleading universal runtime toggle:

| Package | Status | Content |
|---|---|---|
| ModeU5 Core - Stock-Constrained Economy | Required | Stock accounting, capacity, initialization/succession, decay, void-economy correction, demand resolution, validation, and core UI/debug |
| ModeU5 Economy Rebalance | Default enabled; removable | US-04, US-05, US-08, US-09 and their UI stories |
| ModeU5 Trade Rebalance | Default enabled; removable | US-07 and US-07-UI |
| ModeU5 War Rebalance | Default enabled; removable | US-13 |

The default ModeU5 playset loads all four packages. The Core package is the identity of the mod and has no supported disabled state. Rebalance companions may be removed in the launcher before campaign load. See `docs/technical/MODULE_OPTION_MODEL.md`.

ModeU5 configuration occurs before campaign start. The launcher/mod playset selects Core and optional rebalance packages. EU5's built-in Game Rules screen configures script-safe settings such as ModeU5 debug output. There is no custom in-game configuration panel.

## Core implementation tickets

The six centralized operations and the two lifecycle tickets have implementation-ready issue files:

```txt
CORE-00    module packaging and option contract
CORE-01.1  modeu5_add_stock
CORE-01.2  modeu5_remove_stock
CORE-01.3  modeu5_transfer_stock
CORE-01.4  modeu5_decay_stock
CORE-01.5  modeu5_rebuild_market_stock_from_country_stocks
CORE-01.6  modeu5_validate_stock_consistency
CORE-02    delayed and versioned start-game stock initialization
CORE-03    country and territory stock succession
```

They are stored in `docs/generated_issues/` and define the transaction contracts, startup ordering, confirmed map layout, debug output, dependencies, acceptance criteria, and deterministic manual tests.

## Runtime contract

The runtime order is normative. The implementation roadmap is only a delivery strategy.

Monthly sequence summary:

```txt
previous penalties
→ Economy Rebalance global modifiers, including US-09, when loaded
→ capacity recalculation
→ production read/estimate
→ modeu5_add_stock
→ US-00.1 ledger
→ US-10.1 consumption
→ US-10.3 unsatisfied demand
→ US-10.2 inter-market transfers
→ modeu5_decay_stock
→ US-00.2 ratios
→ US-00.4 void wealth
→ US-00.3 next-month penalty
→ Economy Rebalance US-05 Economic Base, when loaded
→ Economy Rebalance US-05 formula visibility, when loaded
→ stock consistency validation
→ monthly counter reset
```

Yearly sequence summary:

```txt
validate stock
→ rebuild market aggregate if needed
→ read annual satisfaction counters
→ apply Economy Rebalance US-04 local Pop demand adaptation, when loaded
→ reset annual counters
→ run annual diagnostics
```

## Bootstrap content

This repository contains scaffolding, governance documents, and implementation-ready issue specifications:

- `README.md`
- `CLAUDE.md`
- `AGENTS.md`
- `descriptor.mod`
- `docs/issues/001_bootstrap_mod_structure.md`
- `docs/issues/002_add_claude_agents.md`
- `docs/issues/003_engine_exposure_matrix.md`
- `docs/issues/004_test_plan_debug_conventions.md`
- `.github/ISSUE_TEMPLATE/github_issue_template.md`
- `.github/ISSUE_TEMPLATE/pull_request_template.md`
- `docs/technical/TECH-01_engine_exposure_matrix.md`
- `docs/technical/DEBUG_CONVENTIONS.md`
- `docs/tests/TEST_PLAN.md`
- `docs/generated_issues/core-01-*.md`

No gameplay logic is implemented by these documentation tickets.

## Suggested branch workflow

```txt
main
└── dev
    ├── spike/engine-exposure
    ├── feature/core-stock-effects
    ├── feature/stock-validation
    ├── feature/monthly-stock-cycle
    ├── feature/void-economy-ledger
    ├── feature/void-production-penalty
    ├── feature/storage-capacity
    ├── feature/stock-demand-resolver
    ├── feature/consumption-resolution
    ├── feature/inter-market-transfer
    ├── feature/local-pop-demand-adaptation
    ├── feature/economic-base
    ├── balance/static-overrides
    └── config/game-rules
```

## MVP boundaries

Do not implement without explicit approval:

```txt
full building-level profit reconstruction
RGO-level profit reconstruction
complete custom GUI stock ledger
advanced AI economic planner
detailed logistics routes
transport queues
full replacement of vanilla markets
intra-market trade profit simulation
multiple competing fallback systems for one missing exposure
```

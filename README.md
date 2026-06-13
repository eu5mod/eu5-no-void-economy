# ModeU5 — Country Stocks Within Markets

ModeU5 adds a double-accounting layer for goods inside EU5 markets.

The mod does **not** replace the vanilla market system. It adds a stock, control, debug, and reconciliation layer so that economic value can be checked against goods that actually enter stock.

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
- US-06 transport cost from exposed trade/import/export scopes, with monthly reconciliation as default;
- US-05 slider base limited to Stability and Court/Government Power, with optional US-05.1 void-wealth exclusion where needed;
- mandatory debug and TECH-01 exposure tracking.

## Runtime contract

The runtime order is normative. The implementation roadmap is only a delivery strategy.

Monthly sequence summary:

```txt
previous penalties
→ global modifiers
→ capacity recalculation
→ production read/estimate
→ modeu5_add_stock
→ US-00.1 ledger
→ US-10.1 consumption
→ US-10.3 unsatisfied demand
→ US-10.2 inter-market transfers
→ US-06 transport cost
→ modeu5_decay_stock
→ US-00.2 ratios
→ US-00.4 void wealth
→ US-00.3 next-month penalty
→ US-06 reconciliation
→ US-05 slider base
→ optional US-05.1 correction
→ stock consistency validation
→ monthly counter reset
```

Yearly sequence summary:

```txt
validate stock
→ rebuild market aggregate if needed
→ read annual satisfaction counters
→ apply US-04 local Pop demand adaptation
→ reset annual counters
→ run annual diagnostics
→ update AI signals
```

## Bootstrap content

This repository contains only scaffolding and governance documents:

- `README.md`
- `CLAUDE.md`
- `AGENTS.md`
- `descriptor.mod`
- `docs/issues/001_bootstrap_mod_structure.md`
- `docs/issues/002_add_claude_agents.md`
- `docs/issues/003_engine_exposure_matrix.md`
- `docs/issues/004_test_plan_debug_conventions.md`
- `docs/templates/github_issue_template.md`
- `docs/templates/pull_request_template.md`
- `docs/technical/TECH-01_engine_exposure_matrix.md`
- `docs/technical/DEBUG_CONVENTIONS.md`
- `docs/tests/TEST_PLAN.md`

No gameplay logic is implemented at bootstrap stage.

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
    ├── feature/trade-transport-cost
    ├── feature/local-pop-demand-adaptation
    ├── feature/slider-reconciliation
    ├── balance/static-overrides
    └── ui/debug-panel
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

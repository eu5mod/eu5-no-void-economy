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
- optional Rebalance Economy US-05 direct Economic Base replacement for Stability and legitimacy-producing Court/Government Power only;
- no transport-cost, trade-income reconciliation, slider reconciliation, or AI-planning story in the surviving MVP set;
- mandatory debug and TECH-01 exposure tracking.

## Module choices

ModeU5 uses packages rather than a misleading universal runtime toggle:

| Package | Status | Content |
|---|---|---|
| No Void Economy | Required | Stock accounting, capacity, initialization/succession, decay, void-economy correction, demand resolution, validation, and core UI/debug |
| Rebalance Economy | Optional; included in the recommended playset | US-04, US-05, US-08, US-09 and their UI stories |
| Rebalance Estate Power | Optional; included in the recommended playset | US-07 and US-07-UI |
| Rebalance Early Blobbing | Optional; included in the recommended playset | US-13 |

The recommended ModeU5 playset loads all four packages. The Core package is the identity of the mod and has no supported disabled state. Rebalance companions may be removed in the launcher before campaign load. Keep the selected package set unchanged for the lifetime of that save; no package currently supports mid-campaign addition or removal. See `docs/technical/MODULE_OPTION_MODEL.md`.

ModeU5 configuration occurs before campaign start. The launcher/mod playset selects Core and optional rebalance packages. EU5's built-in Game Rules screen configures script-safe settings such as ModeU5 debug output. There is no custom in-game configuration panel.

The mod manager and selected-playset tooltips show this lifecycle warning from
each package's metadata. `Rebalance Early Blobbing` is currently a reserved
package marker: US-13 gameplay remains unimplemented until its static
conquest-cost hook is confirmed.

### Local package installation

The repository contains four source package roots, but EU5 discovers local
packages as sibling directories. Publish them to the local mod directory with:

```bash
./tools/install_local_packages.sh
```

Then refresh the launcher and enable:

```txt
No Void Economy
Rebalance Economy
Rebalance Estate Power
Rebalance Early Blobbing
```

The installer writes `MODEU5_SOURCE.txt` into every installed package with the
source path, branch, and commit. Check what is installed with:

```bash
./tools/install_local_packages.sh --check
```

If the launcher shows two `No Void Economy` entries, disable the older
single-package entry backed by the `eu5voideco` path and keep the new
`modeu5_core` entry. Each optional package declares `modeu5_core` version
`0.1.*` as a dependency. Selecting a companion automatically enables compatible
Core. The reverse is intentionally not true: selecting Core alone leaves the
optional packages unselected. Disabling Core also does not cascade-disable
already selected companions, so review the playset before campaign load.

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

## Implemented core stock API

CORE-01.1 through CORE-01.6 are implemented in `in_game/common/scripted_effects/`.

Callers pass a literal goods token such as `wheat`. Generated EU5 adapters
contain the literal map reads and remove/re-add replacements required for that
good. Shared scripted effects own validation and arithmetic. The shell generator
only expands the versioned adapter template and contains no stock behavior.

```txt
modeu5_add_stock(country, market, good, quantity, capacity_policy)
modeu5_remove_stock(country, market, good, quantity, reason)
modeu5_transfer_stock(seller_country, buyer_country, source_market,
                      target_market, good, quantity, target_capacity_policy)
modeu5_decay_stock(country, market, good, decay_rate)
modeu5_decay_stock_default(country, market, good)
modeu5_rebuild_market_stock_from_country_stocks(market, good)
modeu5_validate_stock_consistency(market, good)
```

Supported capacity policies:

```txt
enforce
allow_over_capacity
```

`allow_over_capacity` remains reserved for CORE-02 initialization, CORE-03
succession, deterministic tests, and separately approved migrations.

Transaction outputs are temporary scope values, including:

```txt
modeu5_actual_added_quantity
modeu5_rejected_quantity
modeu5_actual_removed_quantity
modeu5_actual_transferred_quantity
modeu5_transferred_quantity
modeu5_unsatisfied_quantity
modeu5_decayed_quantity
```

CORE-01.5 rebuilds only the selected market-good aggregate from authoritative
country stocks. CORE-01.6 is read-only when consistent and delegates every
aggregate correction to CORE-01.5. US-11 remains responsible for global
iteration and monthly/yearly orchestration.

## Runtime contract

The runtime order is normative. The implementation roadmap is only a delivery strategy.

Monthly sequence summary:

```txt
previous penalties
→ Rebalance Economy global modifiers, including US-09, when loaded
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
→ Rebalance Economy US-05 Economic Base, when loaded
→ Rebalance Economy US-05 formula visibility, when loaded
→ stock consistency validation
→ monthly counter reset
```

Yearly sequence summary:

```txt
validate stock
→ rebuild market aggregate if needed
→ read annual satisfaction counters
→ apply Rebalance Economy US-04 local Pop demand adaptation, when loaded
→ reset annual counters
→ run annual diagnostics
```

## Bootstrap content

This repository contains the first centralized stock effects plus governance documents and implementation-ready issue specifications:

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

The generated issue files remain specifications; runtime logic lives under `in_game/`.

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

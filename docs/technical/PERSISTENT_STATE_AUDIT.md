# ModeU5 Persistent State Audit

This audit is the source of truth for ModeU5 persistent variable maps and
variable lists. It intentionally focuses on structured persistent storage:
maps and lists. Runtime scalar flags, counters, and debug result variables are
documented in their owning feature docs and are outside this audit.

## Policy

Persist only state that is one of:

- authoritative stock state;
- capacity state required by stock operations and UI;
- gameplay-critical monthly carryover state;
- current-month UI counters required by an approved UI story;
- scheduling indexes needed to avoid heavier scans;
- debug, audit, migration, or probe state that is explicitly scoped as such.

Any new ModeU5 variable map or variable list must be classified here and must be
accepted by `tools/audit_modeu5_persistent_state.sh`.

## Map Families

| Family | Owner | Key | Lifecycle | Readers | Persistence reason | Fourth-phase target |
| --- | --- | --- | --- | --- | --- | --- |
| `modeu5_<good>_stock_by_market` | country | market | durable save state | CORE-01, CORE-02, CORE-03, US-00, US-10, US-11 | authoritative country-market-good stock | keep |
| `modeu5_<good>_market_stock` | global | market | durable aggregate/cache | CORE-01, CORE-02, CORE-03, US-10, US-11 | market-good aggregate rebuilt from country stock | keep |
| `modeu5_stock_cap_by_market` | country | market | durable capacity snapshot | CORE-01, CORE-02, CORE-03, US-00, US-10, UI/debug | stock admission cap and allocation input | keep |
| `modeu5_base_capacity_by_market` | country | market | durable capacity breakdown | US-02, UI/debug | capacity explanation and diagnostics | keep |
| `modeu5_building_capacity_by_market` | country | market | durable capacity breakdown | US-02, UI/debug | capacity explanation and future storage-building hook | keep |
| `modeu5_foreign_capacity_by_market` | country | market | durable capacity breakdown | US-02, UI/debug | capacity explanation and future foreign-storage hook | keep |
| `modeu5_<good>_production_penalty_by_market` | country | market | gameplay carryover | US-00, generated modifiers | next-month production penalty | keep normal-runtime persistent |
| `modeu5_<good>_us00_active_record_by_market` | country | market | scheduling index | PERF-15 monthly dispatch | cheap previous-state probe | keep while PERF-15 dispatch uses it |
| `modeu5_<good>_consumption_requested_by_market` | country | market | current month | US-10.1, US-10.3, US-10-UI/debug | same-market consumption request quantity | keep until monthly consumers/UI read it |
| `modeu5_<good>_consumption_satisfied_by_market` | country | market | current month | US-10.1, US-10.3, US-10-UI/debug | same-market consumption quantity removed from stock | keep until monthly consumers/UI read it |
| `modeu5_<good>_consumption_unsatisfied_by_market` | country | market | current month | US-10.1, US-10.3, US-10-UI/debug, future US-04 bridge | same-market consumption shortage signal | keep until monthly consumers/UI read it |
| `modeu5_<good>_trade_requested_by_market` | country | target market | current month | US-10.2, US-10.3, US-10-UI/debug | inter-market transfer request quantity attributed to buyer target market | keep until monthly consumers/UI read it |
| `modeu5_<good>_trade_transferred_by_market` | country | target market | current month | US-10.2, US-10.3, US-10-UI/debug, future US-06 | actual inter-market quantity transferred into buyer target market | keep until monthly consumers/UI read it |
| `modeu5_<good>_trade_unsatisfied_by_market` | country | target market | current month | US-10.2, US-10.3, US-10-UI/debug | inter-market transfer shortage signal | keep until monthly consumers/UI read it |
| `modeu5_<good>_ui_monthly_surplus_by_market` | human country | market | current month | US-10-UI / debug | current monthly overproduction display counter | keep only for human UI scope |
| `modeu5_<good>_ui_monthly_consumption_by_market` | human country | market | current month | US-10-UI / debug | current monthly denominator/display counter | keep only for human UI scope |
| `modeu5_<good>_produced_by_market` | country | market | diagnostic ledger | US-00 tests, strict/debug/audit | full production ledger | strict/debug/audit or human-relevant full ledger only |
| `modeu5_<good>_added_by_market` | country | market | diagnostic ledger | US-00 tests, strict/debug/audit | full stock-admission ledger | strict/debug/audit or human-relevant full ledger only |
| `modeu5_<good>_rejected_by_market` | country | market | diagnostic ledger | US-00 tests, strict/debug/audit | full stock-rejection ledger | strict/debug/audit or human-relevant full ledger only |
| `modeu5_<good>_overproduction_ratio_by_market` | country | market | diagnostic ledger | US-00 tests, strict/debug/audit | full overproduction explanation | derive or strict/debug/audit only |
| `modeu5_<good>_effective_overproduction_ratio_by_market` | country | market | diagnostic ledger | US-00 tests, strict/debug/audit | intermediate used to calculate penalty | transaction-local after penalty calculation |
| `modeu5_<good>_void_wealth_by_market` | country | market | diagnostic ledger | US-00 tests, strict/debug/audit | full void-wealth explanation | strict/debug/audit only unless gameplay later requires it |
| `modeu5_<good>_void_taxable_income_proxy_by_market` | country | market | diagnostic ledger | US-00 tests, strict/debug/audit | full taxable proxy explanation | strict/debug/audit only unless gameplay later requires it |
| `modeu5_void_wealth_by_market` | country | market | aggregated diagnostic ledger | US-00 tests, debug/audit | all-goods market void wealth summary | strict/debug/audit or explicit UI only |

## Variable Lists

| List | Owner | Target | Lifecycle | Readers | Persistence reason | Fourth-phase target |
| --- | --- | --- | --- | --- | --- | --- |
| `modeu5_<good>_dirty_markets` | global | market | dirty until reconciliation | US-11 | dirty market-good reconciliation scheduling | keep |
| `modeu5_<good>_active_markets` | global | market | rebuilt maintenance index | US-11 active validation | active market-good validation scheduling | keep |
| `modeu5_active_markets_any_good` | global | market | rebuilt maintenance index | US-11 active validation | active market scheduling across goods | keep |
| `modeu5_countries_present_in_market` | global | country | temporary rebuilt work cache | market-country cache helpers, validation | current-market country work list | keep as rebuilt cache, not durable per-market storage |
| `modeu5_market_country_cache_dirty_markets` | global | market | dirty until repair | market-country cache repair | schedule cache repair after ownership changes | keep |
| `modeu5_monthly_markets_seen_this_cycle` | global | market | reset once per month | PERF-06 diagnostics and market-owned scheduling | monthly seen-market diagnostics | keep as scheduling/diagnostic index |
| `modeu5_performance_relevant_markets` | global | market | rare rebuild | PERF-02 / future human relevance | human-relevant market discovery | keep as rare performance list |
| `modeu5_core03_probe_seen_locations` | global | location | explicit debug probe only | CORE-03 exposure probe | duplicate-hook detection | debug/probe only |

## Normal-Runtime Target

Normal runtime should keep the authoritative and gameplay-carryover maps. Full
US-00 diagnostic ledger maps are classified but should be narrowed by later
PERF-17 through PERF-20 work.

The current target summary is:

```txt
Stock maps: kept
Capacity maps: kept/shared
Capacity breakdown maps: kept
US-00 gameplay carryover maps: kept
US-00 full diagnostic ledger maps: strict/debug/audit or human-relevant only
UI monthly counter maps: human country current-month only
UI shadow maps: 0
Unclassified persistent maps: 0
```

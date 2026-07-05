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
| `modeu5_<good>_vanilla_produced_markets` | global | market | monthly cache | US-00, US-10-UI | vanilla `is_produced_in_market` result so UI can show goods whose production exists even when current stock admission is zero due to capacity saturation | keep as refreshed cache |
| `modeu5_<good>_us00_active_record_by_market` | country | market | scheduling index | PERF-15 monthly dispatch | cheap previous-state probe | keep while PERF-15 dispatch uses it |
| `modeu5_consumption_<good>_pending_requested_by_market` | country | market | current month input queue | US-10.1 monthly runtime integration | explicit country-market consumption request waiting for the next US-10 monthly pass | remove when processed |
| `modeu5_consumption_<good>_requested_by_market` | country | market | current month | US-10.1, US-10.3, US-10-UI/debug | same-market consumption request quantity | keep until monthly consumers/UI read it |
| `modeu5_consumption_<good>_satisfied_by_market` | country | market | current month | US-10.1, US-10.3, US-10-UI/debug | same-market consumption quantity removed from stock | keep until monthly consumers/UI read it |
| `modeu5_consumption_<good>_unsatisfied_by_market` | country | market | current month | US-10.1, US-10.3, US-10-UI/debug, future US-04 bridge | same-market consumption shortage signal | keep until monthly consumers/UI read it |
| `modeu5_trade_<good>_requested_by_market` | country | target market | current month | US-10.2, US-10.3, US-10-UI/debug | inter-market transfer request quantity attributed to buyer target market | keep until monthly consumers/UI read it |
| `modeu5_trade_<good>_transferred_by_market` | country | target market | current month | US-10.2, US-10.3, US-10-UI/debug, future US-06 | actual inter-market quantity transferred into buyer target market | keep until monthly consumers/UI read it |
| `modeu5_trade_<good>_unsatisfied_by_market` | country | target market | current month | US-10.2, US-10.3, US-10-UI/debug | inter-market transfer shortage signal | keep until monthly consumers/UI read it |
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
| `modeu5_<good>_us10_sparse_suppliers` | global | country | rebuilt per current market/good scan | US-10 / PERF-14 | temporary sparse supplier work list before candidate scoring | keep as rebuilt cache, not durable per-market storage |
| `modeu5_active_markets_any_good` | global | market | rebuilt maintenance index | US-11 active validation | active market scheduling across goods | keep |
| `modeu5_countries_present_in_market` | global | country | temporary rebuilt work cache | market-country cache helpers, validation | current-market country work list | keep as rebuilt cache, not durable per-market storage |
| `modeu5_market_country_cache_dirty_markets` | global | market | dirty until repair | market-country cache repair | schedule cache repair after ownership changes | keep |
| `modeu5_monthly_markets_seen_this_cycle` | global | market | reset once per month | PERF-06 diagnostics and market-owned scheduling | monthly seen-market diagnostics | keep as scheduling/diagnostic index |
| `modeu5_performance_relevant_markets` | global | market | rare rebuild | PERF-02 / future human relevance | human-relevant market discovery | keep as rare performance list |
| `modeu5_promoted_markets_this_cycle` | global | market | rebuilt by PR126 promoted-market shell | PR126 dispatcher shell / future monthly promoted-market cycle | current shell work list built from `every_market_present_in_country` and filtered by mode | keep as rebuilt work cache only |
| `modeu5_detailed_accounting_promoted_markets` | global | market | rebuilt/marked by promotion | PERF-14 / promoted-market runtime gates | tracks markets whose aggregate stock has been promoted to detailed country-market records | work cache only; never stock source |
| `modeu5_core03_probe_seen_locations` | global | location | explicit debug probe only | CORE-03 exposure probe | duplicate-hook detection | debug/probe only |

## Ownership, Rebuild, And Reset Plan

Every persistent map/list family must have one owner, one rebuild or write
trigger, and one reset policy before runtime refactor work can depend on it.
This table is intentionally operational: later PR126 runtime PRs should check
this section before moving a reader or deleting a cache.

| Family | Class | Owner | Rebuild / write trigger | Reset policy |
| --- | --- | --- | --- | --- |
| `modeu5_<good>_stock_by_market` | source | country | central stock operators only | never clear except explicit migration/test |
| `modeu5_<good>_market_stock` | derived cache | global | central stock operators or rebuild from country stock | never treat as source; rebuild from country stock |
| `modeu5_stock_cap_by_market` | capacity source | country | capacity refresh, initialization, owner/rank/capital hooks | replace during capacity refresh |
| `modeu5_base_capacity_by_market` | capacity breakdown | country | capacity refresh, initialization, owner/rank/capital hooks | replace during capacity refresh |
| `modeu5_building_capacity_by_market` | capacity breakdown | country | capacity refresh, initialization, owner/rank/capital hooks | replace during capacity refresh |
| `modeu5_foreign_capacity_by_market` | capacity breakdown | country | capacity refresh, initialization, owner/rank/capital hooks | replace during capacity refresh |
| `modeu5_<good>_production_penalty_by_market` | gameplay carryover | country | US-00 next-month penalty finalization | replace when next penalty is finalized |
| `modeu5_<good>_us00_active_record_by_market` | work cache | country | PERF-15 active-record probe/update | rebuild or remove when record becomes inactive |
| `modeu5_<good>_produced_by_market` | monthly ledger | country | US-00 production ingestion | monthly after readers |
| `modeu5_<good>_added_by_market` | monthly ledger | country | US-00 stock-admission result | monthly after readers |
| `modeu5_<good>_rejected_by_market` | monthly ledger | country | US-00 stock-admission result | monthly after readers |
| `modeu5_<good>_overproduction_ratio_by_market` | derived monthly ledger | country | US-00 ratio calculation from frozen facts | monthly after readers |
| `modeu5_<good>_effective_overproduction_ratio_by_market` | derived monthly ledger | country | US-00 ratio finalization from frozen facts | monthly after readers |
| `modeu5_<good>_void_wealth_by_market` | diagnostic ledger | country | US-00 void-wealth finalization | strict/debug/audit or monthly after readers |
| `modeu5_<good>_void_taxable_income_proxy_by_market` | diagnostic ledger | country | US-00 taxable-proxy finalization | strict/debug/audit or monthly after readers |
| `modeu5_void_wealth_by_market` | diagnostic ledger | country | US-00 all-goods void-wealth aggregation | strict/debug/audit or monthly after readers |
| `modeu5_consumption_<good>_pending_requested_by_market` | monthly input queue | country | explicit US-10 request enqueue | remove when processed by monthly pass |
| `modeu5_consumption_<good>_requested_by_market` | monthly ledger | country | US-10 same-market consumption resolution | monthly after US-10.3/UI readers |
| `modeu5_consumption_<good>_satisfied_by_market` | monthly ledger | country | US-10 same-market consumption resolution | monthly after US-10.3/UI readers |
| `modeu5_consumption_<good>_unsatisfied_by_market` | monthly ledger | country | US-10 same-market consumption resolution | monthly after US-10.3/UI readers |
| `modeu5_trade_<good>_requested_by_market` | monthly ledger | country | US-10 inter-market transfer resolution | monthly after US-10.3/UI readers |
| `modeu5_trade_<good>_transferred_by_market` | monthly ledger | country | US-10 inter-market transfer resolution | monthly after US-10.3/UI readers |
| `modeu5_trade_<good>_unsatisfied_by_market` | monthly ledger | country | US-10 inter-market transfer resolution | monthly after US-10.3/UI readers |
| `modeu5_<good>_ui_monthly_surplus_by_market` | UI monthly counter | human country | US-00/UI current-month capture | monthly after UI/readers |
| `modeu5_<good>_ui_monthly_consumption_by_market` | UI monthly counter | human country | US-10/UI current-month capture | monthly after UI/readers |
| `modeu5_<good>_dirty_markets` | work cache | global | central stock mutation marks dirty | clear after reconciliation/explicit reset |
| `modeu5_<good>_active_markets` | work cache | global | mark active market / active-list repair | clear during active-list rebuild |
| `modeu5_<good>_us10_sparse_suppliers` | work cache | global | US-10 sparse supplier preparation | clear before each market/good rebuild |
| `modeu5_active_markets_any_good` | work cache | global | mark active market / active-list repair | clear during active-list rebuild |
| `modeu5_countries_present_in_market` | work cache | global | `modeu5_rebuild_countries_present_in_market` | clear before each target/promoted-market rebuild |
| `modeu5_market_country_cache_dirty_markets` | work cache | global | ownership/cache repair marks affected markets | clear during cache repair |
| `modeu5_monthly_markets_seen_this_cycle` | work cache | global | monthly seen-market preparation | reset once per month |
| `modeu5_performance_relevant_markets` | work cache | global | human/performance relevance rebuild | clear before relevance rebuild |
| `modeu5_promoted_markets_this_cycle` | work cache | global | PR126 promoted-market dispatcher shell preparation | clear before each promoted-market shell preparation |
| `modeu5_detailed_accounting_promoted_markets` | work cache | global | PERF-14 successful promotion | clear on explicit promoted-market rebuild/reset |
| `modeu5_core03_probe_seen_locations` | debug-only | global | CORE-03 explicit debug probe | clear before probe |

`modeu5_countries_present_in_market` deserves special care in PR126 follow-up
work. It is a rebuilt work cache for the current target/promoted market. It is
not durable per market, not a stock source, and not proof that a country has
positive stock. Runtime code may use it to choose which country records to read
or validate after it has just been rebuilt for the target market.

## Scalar Debug And Work State

The executable audit also counts scalar debug/work variables. These are not
persistent map families, but PR126 requires them to be visible because they can
otherwise look like hidden business state.

| Family | Class | Owner | Lifecycle | Rule |
| --- | --- | --- | --- | --- |
| `modeu5_debug_last_*` | debug-only scalar | current debug/probe scope | overwritten by the next capture/probe | never drive business logic |
| `modeu5_debug_us10_*_trace_*` | audit/debug trace scalar | current US-10 resolver scope | overwritten during bounded audit trace | diagnostics only |
| `modeu5_perf13_*`, `modeu5_perf14_*` | work/metric scalar | global | reset by owning probe/helper before measurement | metrics only, not business source |
| `modeu5_performance_*_count` / fallback counters | work/metric scalar | global | reset by owning performance helper | counters only, not stock source |

Adding a scalar debug/work family does not require a map row, but it must remain
diagnostic or metric-only. If a scalar starts controlling business behaviour,
its owner and lifecycle must be documented in the relevant feature docs before
the audit is widened.

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
Work caches: scheduling only, never stock source
Debug variables: diagnostic only, never business source
UI shadow maps: 0
Unclassified persistent maps: 0
Direct stock-map write candidates outside generated adapter template: 0
Ownership/rebuild/reset policy gaps: 0
```

## Executable Audit Contract

`tools/audit_modeu5_persistent_state.sh` is the machine-checkable form of this
document. It must fail when:

- a new ModeU5 persistent map/list family is discovered but not classified;
- an unexpected UI shadow map/list family appears;
- a direct write to `modeu5_<good>_stock_by_market` is found outside the
  generated stock adapter template;
- an inventory entry is missing an owner, rebuild/write trigger, or reset
  policy;
- source/cache/work/debug classifications drift from the documented inventory.

The stock-write guard deliberately allows the generated adapter template because
that template is the literal per-good persistence surface used by the central
stock operators. Gameplay files must still call the central stock effects
instead of writing stock maps directly.

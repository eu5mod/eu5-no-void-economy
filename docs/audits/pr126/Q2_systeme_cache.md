# Q2 — Cache system and ownership

## Conclusion

The cache system is intentionally rich. It is acceptable if every state is classified and if an agent can immediately tell whether it is reading a source of truth, a derived cache, a work cache, a monthly ledger, or a debug variable. The main risk is not the number of caches, but using a scheduling cache as business proof or writing directly outside helpers.

## Canonical classification

| Cache / variable / list | Affected files | Class | Source of truth | Update / reset | Risk | Agent rule |
|---|---|---|---|---|---|---|
| `modeu5_<good>_stock_by_market` | `modeu5_stock_effects.txt`, generated adapters | country×market×good stock source | Yes | Every stock mutation through operators | P0 if direct write | Never write outside `modeu5_add/remove/transfer/decay_stock` |
| `modeu5_<good>_market_stock` | generated adapters, validation | market×good aggregate cache | No, derived from country stock | Centralized mutation, rebuild, validation | P0 if treated as source | Rebuild from country only |
| `modeu5_stock_cap_by_market` | `modeu5_capacity_effects.txt` | calculated country×market capacity source | Yes for current admission | Init, owner/rank/capital hooks, monthly refresh | P1 if stale before production | Refresh capacity before stock admission |
| `modeu5_base_capacity_by_market` | capacity/debug | debug breakdown | No | With capacity | P3 | Explanation only |
| `modeu5_building_capacity_by_market` | capacity/debug | debug/future breakdown | No | With capacity | P3 | Explanation only |
| `modeu5_foreign_capacity_by_market` | capacity/debug | debug/future breakdown | No | With capacity | P3 | Explanation only |
| `modeu5_<good>_produced_by_market` | `modeu5_void_economy_effects.txt` | US-00 monthly fact | Read/estimated production | Freeze after production/admission; reset after readers | P1 if reset/recomputed late | Do not recompute after US-10/decay |
| `modeu5_<good>_added_by_market` | `modeu5_void_economy_effects.txt` | US-00 monthly fact | `modeu5_add_stock` result | Freeze after admission; reset after readers | P1 | Overproduction input |
| `modeu5_<good>_rejected_by_market` | `modeu5_void_economy_effects.txt` | US-00 monthly fact | `modeu5_add_stock` result | Freeze after admission; reset after readers | P1 | Overproduction input |
| `modeu5_<good>_overproduction_ratio_by_market` | `modeu5_void_economy_effects.txt` | derived monthly ledger | produced/added/rejected facts | Calculate from frozen facts | P1 if recomputed after decay | Read frozen facts, not remaining stock |
| `modeu5_<good>_effective_overproduction_ratio_by_market` | `modeu5_void_economy_effects.txt` | derived monthly ledger | ratio + buffer | Monthly | P1 | Penalty basis, not stock truth |
| `modeu5_<good>_void_wealth_by_market` | `modeu5_void_economy_effects.txt` | US-00 finalization/carryover | frozen US-00 facts + prices | After business readers, before reset | P1 | Publish from frozen facts |
| `modeu5_<good>_void_taxable_income_proxy_by_market` | `modeu5_void_economy_effects.txt` | debug/proxy | void wealth | With US-00 finalization | P2 | Proxy sizing/debug only |
| `modeu5_<good>_production_penalty_by_market` | `modeu5_void_economy_effects.txt` | N+1 carryover | frozen effective ratio | Monthly, consumed next month | P1 | Do not base on post-decay stock |
| `modeu5_consumption_<good>_*_by_market` | `modeu5_stock_demand_resolver_effects.txt` | US-10.1 ledger | same-market demand resolution | Monthly; reset after US-10.3/UI | P1 | Same-market consumption, not trade |
| `modeu5_trade_<good>_*_by_market` | `modeu5_stock_demand_resolver_effects.txt` | US-10.2 ledger | actual inter-market transfer | Monthly; reset after readers | P1 | Only `source_market != target_market` |
| `modeu5_performance_relevant_markets` | `modeu5_performance_effects.txt` | scheduling work cache | country→market discovery | Rare/explicit rebuild | P1 if stale | Performance owner; never proof of stock |
| `modeu5_detailed_accounting_promoted_markets` | `modeu5_performance_effects.txt` | scheduling work cache | successful market promotion | Rebuilt/marked by promotion helpers | P1 if treated as stock proof | Promotion owner; detailed mutation gates must still validate readiness |
| `modeu5_active_markets_any_good` | performance + adapters | union work cache | stock/good activity | Additive + rebuild/audit | P1 if never cleaned | Scheduling only |
| `modeu5_<good>_active_markets` | generated adapters | per-good work cache | good activity | Additive + rebuild/audit | P1 | Not proof of positive quantity |
| `modeu5_countries_present_in_market` | `modeu5_market_country_cache_effects.txt` | market→countries work cache | recalculable country/market relations | Rebuild per promoted market | P1 if treated as durable | Rebuild once per promoted market |
| `modeu5_debug_last_*` | `modeu5_debug_effects.txt` | debug state | current operation | At each probe/operation | P3 | Never drive business logic |

## Duplicated or suspicious caches

| Cache A | Cache B | Duplicated information | Decision |
|---|---|---|---|
| `modeu5_<good>_stock_by_market` | `modeu5_<good>_market_stock` | Stock quantity | Keep both: country source vs market aggregate |
| `modeu5_stock_cap_by_market` | `base/building/foreign` breakdown | Capacity | Keep: business total vs debug explanation |
| `modeu5_<good>_active_markets` | `modeu5_active_markets_any_good` | Active market | Keep: per-good vs global union |
| `modeu5_performance_relevant_markets` | active markets | Markets to traverse | Keep separate: performance policy vs stock activity |
| US-00 ledgers | UI monthly stock/consumption | Monthly economic state | Partial merge only after all readers are identified |
| `modeu5_trade_*` | `modeu5_consumption_*` | Satisfied/unsatisfied demand | Do not merge: inter-market vs same-market |

## Reset and rebuild contract

```txt
monthly start:
  refresh capacity prerequisites
  prepare/rebuild promoted-market scheduling work caches when needed

production admission:
  write US-00 produced/added/rejected facts
  freeze US-00 facts for the month

same month readers:
  US-10 consumption/transfer, UI/debug, US-00 finalization read frozen facts

monthly end:
  validation/reconciliation if enabled
  reset monthly ledgers only after all readers
```

## Mandatory questions before adding a cache

| Question | Expected answer |
|---|---|
| Who owns it? | country, market-global map, global list, debug controller, or generated adapter |
| What class is it? | source, derived cache, work cache, monthly ledger, annual ledger, debug |
| What is the rebuild trigger? | init, monthly start, promoted market, validation, annual, manual probe |
| What is the reset policy? | never, monthly after readers, annual after readers, rebuild-only |
| Which readers exist? | list runtime, UI, debug, and tests before deletion |
| Which validation detects divergence? | audit script, runtime probe, consistency validator, or TECH-01 entry |

## PR1 executable audit coverage

`tools/audit_modeu5_persistent_state.sh` turns this classification into a
machine-checkable inventory. It reports source, derived/cache/diagnostic,
work-cache, monthly/carryover, debug-scalar, and work/metric-scalar counts. It
also fails if a stock map write appears outside the generated stock adapter
template, which protects the central-operator rule before later promoted-market
runtime PRs start moving dispatchers around.

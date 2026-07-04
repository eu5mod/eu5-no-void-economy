# Q1 — Target file architecture

## Conclusion

ModeU5's architecture is healthy if each domain remains the owner of a precise type of responsibility. The PR126 refactor must not try to reduce the number of files at all costs; it must make the responsibility graph readable for an agent: which file owns the scope, which file owns the state, which file owns the calculation, and which file should only be an adapter or a test.

## Canonical responsibilities

| Domain | Owning file(s) | Allowed responsibility | Out of scope in this domain |
|---|---|---|---|
| Stock core | `in_game/common/scripted_effects/modeu5_stock_effects.txt` | central operators, validation, rebuild, minimal orchestration | long US-00/US-10 logic, performance policy, balance rules |
| Capacity | `in_game/common/scripted_effects/modeu5_capacity_effects.txt` | country×market capacity, breakdowns, capacity refresh | stock mutation, promoted-market selection |
| Market-country cache | `in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt` | `countries_present_in_market`, dirty market-country work cache | stock source of truth, gameplay decisions |
| Performance / promotion | `in_game/common/scripted_effects/modeu5_performance_effects.txt` | mode gates, human-relevant markets, promoted-market scheduling | direct economic mutation |
| US-00 | `in_game/common/scripted_effects/modeu5_void_economy_effects.txt` + generated adapters | production facts, admission/rejection ledgers, overproduction, void wealth, next-month penalty | consumption, inter-market trade |
| US-10 | `in_game/common/scripted_effects/modeu5_stock_demand_resolver_effects.txt` | same-market consumption, inter-market stock transfer | vanilla production, US-00 penalty |
| Configuration | `modeu5_configuration_effects.txt`, `modeu5_cmm_runtime_effects.txt`, main menu files | pre-campaign configuration, package markers, script-safe settings | fake runtime toggle for statically loaded packages |
| Debug / tests | `modeu5_debug_effects.txt`, `packages/modeu5_core_tests/...` | standardized captures, deterministic probes, dumps | new business logic |
| Generated adapters | generated files + `tools/templates/` | literal per-good expansion | business policy hidden inside a generator |
| Tools | `tools/*.sh`, `tools/templates/`, validators | generation, validation, audit, local offline probes | unconfirmed runtime assumptions |

## Audit of current files

| File | Current responsibility | Identified issue | Severity | Recommendation | Effort |
|---|---|---|---|---|---|
| `modeu5_stock_effects.txt` | Central mutation, read, rebuild, and validation operators | Critical and large file | P0 | Keep it as the single core; move long US rules into their domains | M |
| `modeu5_capacity_effects.txt` | Country-market capacity calculation and cache | Risk if callers redo location scans outside helpers | P1 | List the authorized entry points | S |
| `modeu5_market_country_cache_effects.txt` | Market↔country cache | Cross-dependency with performance and validation | P1 | Declare caches as work caches, not stock sources | S |
| `modeu5_performance_effects.txt` | Runtime gates and performance caches | Mixes mode, scheduling, and repair | P1 | Split only if the file grows further; do not move stock mutation here | M |
| `modeu5_void_economy_effects.txt` | US-00 ledgers, ratios, void wealth, penalty | Several pipeline stages in one domain | P1 | Clearly separate ingestion facts and finalization/carryover | S |
| `modeu5_stock_demand_resolver_effects.txt` | US-10 demand resolution and transfer | Risk of drifting into intra-market trade | P1 | Same-market = consumption; inter-market = transfer only | S |
| `modeu5_configuration_effects.txt` | Script-safe configuration initialization | Scattered entry points | P2 | Single configuration index | S |
| `modeu5_cmm_runtime_effects.txt` | CMM callbacks and restrictions | May imply runtime toggles | P1 | Repeat that CMM initializes/displays, but does not unload packages | S |
| `modeu5_debug_effects.txt` | Debug captures | Accumulation of `modeu5_debug_last_*` fields | P2 | Document inventory in `DEBUG_CONVENTIONS.md` | S |
| `modeu5_stock_on_actions.txt` | Pulse orchestration | Critical for runtime order | P0 | Call documented dispatchers only | S |
| `packages/modeu5_core_tests/...` | Deterministic probes and tests | Long and similar scenarios | P2 | Factor dumps only after contracts stabilize | M |
| `tools/generate_*` and templates | Per-good adapter generation | Risk of business logic moving into the generator | P1 | Generator = orchestration/template; business rules = runtime/docs | S |

## Change-routing table for agents

| Requested change type | Read first | Main file to modify | Validate with |
|---|---|---|---|
| Stock invariant, add/remove/transfer/decay/rebuild | `VARIABLE_MAP_STORAGE_MODEL.md` | `modeu5_stock_effects.txt` | stock consistency probes |
| Country×market capacity | US-02 docs + Q2 | `modeu5_capacity_effects.txt` | capacity/debug probes |
| Performance market selection | Q4/Q5 | `modeu5_performance_effects.txt` | promoted-market counters |
| Production, rejection, overproduction, penalty | Q5/Q6 | `modeu5_void_economy_effects.txt` + adapters | US-00 debug |
| Same-market consumption | Q5/Q6 | `modeu5_stock_demand_resolver_effects.txt` | US-10.1 probes |
| Inter-market transfer | TECH-01 + Q5/Q6 | `modeu5_stock_demand_resolver_effects.txt` | US-10.2 probes |
| Repeated per-good block | `GENERATOR_AND_VALIDATOR_MODEL.md` | template + generator | `generate_all`, `validate_generators` |
| Configuration / package marker | `MODULE_OPTION_MODEL.md` | configuration/CMM files | package validation |

## Target structure contract

```txt
monthly dispatcher
  -> readiness / fail-closed
  -> capacity prerequisites
  -> promoted-market work list
  -> US-00 production facts
  -> US-10 consumption / transfer
  -> decay
  -> US-00 finalization from frozen facts
  -> validation / reconciliation
  -> reset after readers
```

Each new PR must state which block it changes. If it does not fit any block, the architecture documentation must be corrected before the code.

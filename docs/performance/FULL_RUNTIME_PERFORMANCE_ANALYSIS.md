# Full Runtime Performance Analysis

## Status

This document is a static work-shape analysis of the runtime stacked on PR #211.
It was reviewed on 2026-07-21 against commit
`112788e296a06b290ff743fdef7ce1b5c3937535`.

It does **not** claim measured EU5 frame time, monthly tick duration, CPU time, or
save-size impact. Those claims require a controlled in-game benchmark. The goal
here is to identify the work executed, rank likely cost centres, and define a
safe measurement and optimisation programme without changing economic rules.

The normative orchestration diagram is
[`docs/architecture/RUNTIME_FLOW.md`](../architecture/RUNTIME_FLOW.md).
Historical Q8 documents remain evidence of how the current design was reached;
they are not substitutes for the current runtime sources.

## Executive summary

The current architecture has already removed several catastrophic shapes:

- market-local US-00 and US-10 run once per market per month through the Q8.7
  global owner rather than once per country present in the market;
- US-00 completes for every present country before US-10 starts;
- country-wide capacity-pool facts are cached once per country and month;
- `every_trade` remains country-owned;
- monthly full consistency validation is audit-only;
- four-yearly validation is globally stamped.

The remaining high-value optimisation opportunities are mostly duplicated
preparation, diagnostic writes inside production loops, and broad discovery
loops that precede sparse business work.

| Rank | Finding | Confidence | Primary cost type |
|---:|---|---:|---|
| 1 | Country-market capacity records can be recalculated by both the current-country preparation pass and the global detailed-market pass in the same month. | High | Duplicate calculation and map writes |
| 2 | Rebuilding `cbp_countries_present_in_market` scans every location in each detailed market and updates several global counters for each location. | High | Location traversal plus hot-path writes |
| 3 | Q8.7, promoted-market, and trade-owner diagnostic counters are updated unconditionally in normal runtime. | High | Persistent/global write amplification |
| 4 | CORE-04 performs a second monthly `every_owned_location` traversal after capacity preparation has already scanned the country's locations. | High | Duplicate country-location traversal |
| 5 | Performance Mode still enters `every_market_in_world`; relevance only decides whether each market receives detailed accounting. | High | Broad discovery loop |
| 6 | US-04 independently traverses country markets, 74 supported goods, and qualifying owned locations, then clears and rewrites many per-good diagnostic maps. | High | Multiplicative generated work and map churn |
| 7 | The country trade-owner pass writes several global counters per trade in addition to the required US-17/US-20 work. | High | Per-trade diagnostic overhead |
| 8 | Human-relevant markets are rebuilt through `every_country` and `every_market_present_in_country` once per month in Performance Mode. | Medium | Monthly world discovery |

The recommended first implementation layer is deliberately conservative:

```txt
1. Gate non-business counters behind debug/audit.
2. Add a country-market monthly capacity stamp and make all callers use an
   idempotent ensure-capacity entry point.
3. Measure the resulting work-shape before altering traversal ownership.
```

These changes can reduce repeated work without changing stock, demand, trade,
capacity formulas, accounting modes, or market eligibility.

## Performance notation

| Symbol | Meaning |
|---|---|
| `C` | countries receiving `monthly_country_pulse` |
| `L_c` | owned locations of country `c` |
| `M_c` | markets present in country `c` |
| `M_world` | markets returned by `every_market_in_world` |
| `M_rel` | human-relevant markets in Performance Mode |
| `M_det` | markets that enter detailed CBP accounting |
| `L_m` | locations in market `m` |
| `K_m` | deduplicated countries present in market `m` |
| `G` | supported generated goods; currently 74 |
| `G_a(c,m)` | active US-00 goods for country-market `(c,m)` |
| `G_p(c,m)` | pending US-10 goods for country-market `(c,m)` |
| `T_c` | trades returned by country-scoped `every_trade` |
| `U(c,m,g)` | owned locations inspected by US-04 for country-market-good |

The analysis distinguishes **iterator count** from **write count**. A loop that
only checks scopes is not equivalent to a loop that repeatedly updates global
variables or variable maps.

## Current monthly work shape

### Global and country preparation

```txt
Performance Mode relevant-market refresh, once globally per month:
    O(C + sum(M_c for human countries))

Current-country capacity preparation, once for every country pulse:
    O(sum(M_c)) country-market refreshes
    + O(sum(L_c)) country-wide location scans on first capacity-pool use

Monthly market registry and persistence preparation:
    month-stamped global list/counter maintenance
```

### Market-local owner

The default Q8.7 path is:

```txt
first monthly country pulse
  -> every_market_in_world
     -> classify each market
     -> for each detailed market:
          every_location_in_market to rebuild countries-present cache
          pass 1 over K_m countries: capacity + US-00 active goods
          pass 2 over K_m countries: US-10 pending goods

later monthly country pulses
  -> skip the global market-local pass by global month stamp
```

Static work shape:

```txt
O(M_world)
+ O(sum(L_m for m in M_det))
+ O(sum(K_m * (G_a + G_p) for m in M_det))
```

The explicit rollback path instead uses `every_market_center_in_country` on each
country pulse. It remains a recovery/debug path and should not be used as the
performance baseline.

### Country trade owner

```txt
O(sum(T_c))
```

Every trade captures owner, source market, target market, traded good, and
`trade_volume`. It then applies US-17 route reconciliation and, when enabled,
US-20 route-loss/goods reconciliation.

### US-04 monthly signed delta

```txt
O(sum over countries and markets of:
    G market-level checks
    + sum(U(c,m,g)) for goods that pass the market gate)
```

The canonical registry contains 74 goods. Per-good helpers also clear a broad
monthly diagnostic record and conditionally write the new non-zero values.

### CORE-04 location memory

At the end of every country pulse:

```txt
O(sum(L_c))
```

Each owned location writes its current market and current month stamp.

### Validation

Monthly validation is audit-only and globally month-stamped. Four-yearly active
stock validation is globally year-stamped. These are intentionally outside the
normal monthly performance baseline.

## Detailed findings

## P1 — Duplicate country-market capacity refresh

### Evidence

`cbp_run_monthly_capacity_refresh_for_current_country` iterates every market
present in the current country and refreshes each country-market capacity record.
The detailed market-local pass later iterates every present country and calls
`cbp_prepare_promoted_country_market_capacity` for the same country-market
records.

Q8.3 already prevents repeated country-wide pool reconstruction: the country
pool is monthly stamped. However, every caller still recalculates the
market-specific merchant/trade-capacity contribution and rewrites the current
country-market capacity record.

### Approximate duplicate surface

```txt
current-country preparation: sum(M_c)
global detailed-market pass: sum(K_m for m in M_det)
```

For a country-market that is detailed and present during the same month, both
surfaces can touch the same record. The first country pulse also runs its own
country preparation before launching the global market pass; later country
pulses prepare their markets again after the global pass has already completed.

### Safe optimisation

Introduce one idempotent public entry point:

```txt
cbp_ensure_country_market_capacity_current_month(country, market)
```

Contract:

```txt
if country-market capacity stamp == current month
    load/reuse the record
else
    ensure country pool current
    calculate market-specific contribution
    write capacity record and stamp
```

Both the current-country preparation and market-local pass must call this same
entry point. Do not remove either caller until runtime evidence proves its other
consumers no longer require the preparation boundary.

### Expected benefit

Reduces country-market calculation and map-write count while preserving all
phase ordering and both dispatcher modes.

## P2 — Market-to-country cache rebuild scans every market location

### Evidence

For every detailed market, `cbp_rebuild_countries_present_in_market`:

```txt
clear one global work list
every_location_in_market
  increment locations-scanned counter
  if owner exists:
    increment owner counter
    deduplicate owner into global country list
    increment countries-added counter when new
```

The work cache is correct and avoids `every_country`, but its cost is proportional
to locations, not countries. The current implementation also performs global
counter writes inside that location loop.

### Safe optimisation layer 1

Split business work from diagnostic instrumentation:

```txt
normal runtime:
  scan locations and build the country list only

debug/audit:
  additionally update location/country counters
```

### Candidate layer 2

Use lifecycle dirty events to retain a durable or semi-durable per-market
country membership index only after its storage ownership and invalidation
contract is proven. Required invalidation producers include at least:

- location owner change;
- location market change;
- country creation/destruction where relevant;
- load repair and schema migration.

Until every producer is confirmed, the rebuild-per-detailed-market model remains
the safer source of truth.

## P3 — Unconditional global metric writes in production loops

### Evidence

The following families contain production-loop counters that are not generally
guarded by debug/audit before the write:

- Q8.7 owner runs, skips, markets seen, detailed/fallback/blocked markets;
- promoted-market cache rebuilds, country passes, good scans, processed markets;
- market-country cache locations scanned, owned locations, countries added;
- country trade-owner passes, trades seen, quantity outcomes, inter-market
  classifications;
- monthly market-seen new/duplicate counters.

These counters are valuable for deterministic validation, but global-variable
writes can dominate otherwise cheap guards when multiplied by world markets,
locations, goods, and trades.

### Safe optimisation

Define two categories:

```txt
correctness state:
  required for gates, ownership, idempotence, or economic output
  -> always retained

observability state:
  counters and traces used only by tests/profiling
  -> update only when cbp_debug_capture_enabled_trigger or
     cbp_audit_enabled_trigger is true
```

Add a static validator that rejects calls to known observability-only `cbp_note_*`
and `cbp_increment_*` effects from hot paths unless they are enclosed by the
approved observability gate.

### Expected benefit

Low-risk reduction in writes without changing any iterator or economic result.
This should be the first runtime optimisation PR after the analysis.

## P4 — Two monthly country-location scans

### Evidence

The capacity pool's first monthly calculation uses `every_owned_location` to sum
location-rank capacity. After monthly economic work, CORE-04 again uses
`every_owned_location` to persist each location's current market and month stamp.

Current shape:

```txt
capacity preparation: every_owned_location -> rank contribution and count
end of pulse:         every_owned_location -> market memory and stamp
```

### Candidate optimisation

Fuse the CORE-04 memory writes into the capacity-pool location traversal, then
retain an end-of-pulse verification/repair only for locations known to have
changed market during the cycle.

This is higher risk than metric gating because CORE-04 deliberately snapshots
market topology after economic work. A safe implementation requires proof that
no monthly phase can change location market membership after the fused scan, or
an explicit dirty-location list maintained by every topology-changing hook.

### Recommendation

Do not implement this before P1-P3. First add counters for:

- capacity location scans;
- CORE-04 memory location writes;
- locations whose market actually differs from stored memory.

The optimisation is attractive only if unchanged locations overwhelmingly
dominate.

## P5 — Performance Mode still scans every world market

### Evidence

The default global owner always enters `every_market_in_world`. In Performance
Mode, `cbp_prepare_market_runtime_accounting_mode` checks whether the market is
human relevant. Non-relevant markets become Vanilla fallback, but they are still
visited and receive classification and fallback instrumentation.

Current shape:

```txt
O(M_world) classification
+ detailed work for M_rel/promoted markets
```

### Candidate optimisation

Use dispatcher-specific iterators:

```txt
Normal Mode:
  every_market_in_world

Performance Mode:
  every_in_global_list(cbp_performance_relevant_markets)
  + explicit processing of newly promoted/dirty markets not yet represented

Deactivated Mode:
  skip market-local traversal unless diagnostic coverage is requested
```

### Required proof

The alternative must preserve:

- promotion of newly relevant markets;
- fallback semantics for stock mutation attempts;
- monthly market-seen consumers;
- country coverage within every relevant market;
- no market-scope `every_trade`;
- US-00-before-US-10 ordering.

Skipping non-relevant fallback counters is acceptable only after proving they
are diagnostic rather than business state.

## P6 — US-04 multiplicative traversal and record churn

### Evidence

US-04 runs independently after trade for every country when its option is
enabled:

```txt
every_market_present_in_country
  all 74 supported goods
    market demand gate
    owned locations in that market when applicable
      coefficient and four Estate proxy families
      stock/supply/gold delta
    clear broad per-good monthly record
    write non-zero record values
```

The rule must remain global across runtime modes; Performance Mode cannot simply
skip AI countries or non-human markets without changing the business rule.

### Candidate optimisation

Build sparse work lists from actual writers:

```txt
location-good coefficient differs from 1
OR location-good Estate proxy is present
OR prior monthly record requires clearing
```

Then process only sparse country-market-good entries and remove them when all
three conditions become false.

### Guardrails

- Missing state still fails closed to coefficient 1.
- No fixed Estate fallback.
- Base US-10 consumption remains separate from the US-04 signed delta.
- Stock and Vanilla supply must use the actual quantity applied by central
  operators.
- Sparse indexes need explicit initialization, write, removal, and load-repair
  contracts.

## P7 — Per-trade diagnostic overhead

### Evidence

The country-owned `every_trade` pass is the correct ownership surface. In
addition to US-17/US-20 work, it increments multiple global counters for each
trade and quantity outcome.

### Safe optimisation

Retain the iterator and route logic, but gate all purely diagnostic trade metrics
behind debug/audit. Keep only state that is read by economic logic or required to
prevent duplicate execution.

A later optimisation may add a top-level feature gate only if it can prove that
both US-17 and US-20 are inactive. Do not infer this from package names or one
CMM setting; the native US-17 modifier refresh and route reconciliation have
separate responsibilities.

## P8 — Human-relevant market discovery

### Evidence

Once per month in Performance Mode:

```txt
every_country
  is_ai = no
every_market_present_in_country
  deduplicate into cbp_performance_relevant_markets
```

This is bounded by human countries and runs once per month, so it is not the
first optimisation target. It becomes more important in multiplayer or when
relevance expands beyond directly present markets.

### Candidate optimisation

Maintain the list from confirmed human-country market-entry/exit hooks, with a
monthly or yearly verifier. This has the same invalidation challenge as the
market-country cache and should be attempted only with complete topology-hook
coverage.

## Work that should not be optimised away

The following are correctness boundaries, not accidental duplication:

- two present-country passes inside each detailed market: US-00 for all countries
  must finish before any US-10 consumption;
- country-owned `every_trade` rather than a market-owned trade scan;
- central stock operators updating country source-of-truth and market aggregate
  in one transaction;
- audit reconciliation after US-04, because US-04 can mutate both stock layers;
- four-yearly active-stock validation as a safety net;
- fail-closed runtime readiness and accounting-mode gates.

## Recommended implementation roadmap

### Layer A — observability gating

Scope:

- identify correctness versus diagnostic counters;
- gate diagnostic `cbp_note_*` and `cbp_increment_*` writes;
- preserve test coverage by enabling audit/debug in profiling events.

Risk: low.

Acceptance:

- no economic file or business formula changes;
- normal-runtime counter writes materially reduced;
- debug/audit tests still see the expected counters;
- no new parser/runtime errors.

### Layer B — idempotent country-market capacity

Scope:

- add monthly country-market stamp;
- route both preparation callers through one ensure-current effect;
- expose cache-hit and calculation counters only in debug/audit.

Risk: low to medium.

Acceptance:

- capacity values byte/value-equivalent to the current calculation;
- at most one calculation per country-market-month;
- location pool remains at most one raw calculation per country-month;
- CORE-03 and market-entry invalidation clears the relevant stamp.

### Layer C — Performance Mode relevant-market iterator

Scope:

- retain world iterator in Normal Mode;
- iterate relevant/promoted/dirty lists in Performance Mode;
- preserve promotion and fallback contracts.

Risk: medium to high.

Acceptance:

- same detailed-market set as the baseline;
- every relevant market retains all present countries;
- US-00 and US-10 economic dumps match;
- no market-scope trade loop;
- reduced market classifications when `M_rel << M_world`.

### Layer D — sparse US-04 work index

Scope:

- index only active coefficient/proxy/record combinations;
- process sparse country-market-good work;
- define lifecycle repair and removal.

Risk: high.

Acceptance:

- exact signed-delta equivalence;
- no missing clear of prior monthly records;
- identical stock, supply, Estate charge/refund, and annual counters;
- substantial reduction in goods/location checks in sparse scenarios.

### Layer E — fused location traversal

Scope:

- combine capacity and CORE-04 location work where lifecycle proof permits;
- dirty-list repair for topology changes after the fused point.

Risk: high.

Acceptance:

- same capacity pool;
- same last-known market state at pulse end;
- market-entry migration remains correct;
- fewer total owned-location visits.

## Measurement plan

## Benchmark discipline

Use the same EU5 build, mod stack, save, hardware, game speed, runtime mode, and
observation window for baseline and candidate. Do not compare a fresh game with
a late-game save or audit mode with normal mode.

Minimum matrix:

| Scenario | Runtime mode | Save shape | Purpose |
|---|---|---|---|
| A | Normal | mid/late game | Full detailed-market upper bound |
| B | Performance | same save | Relevant-market reduction |
| C | Performance | same save, debug/audit profiling enabled | Work-shape counters |
| D | Deactivated | same save | Framework/control overhead |

Recommended observation window:

```txt
1 warm-up month
12 measured monthly ticks
1 yearly boundary when US-04 annual work is enabled
```

## Counters to capture

Required work-shape counters:

- countries receiving monthly pulse;
- world markets visited;
- detailed/fallback/blocked markets;
- market locations scanned for country-cache rebuild;
- countries added to each market cache;
- capacity pool raw calculations and cache hits;
- country-market capacity calculations and cache hits;
- US-00 country passes and active-good dispatches;
- US-10 country passes and pending-good dispatches;
- trade-owner passes and trades seen;
- US-04 market, good, location, and Estate-proxy checks;
- CORE-04 owned locations visited;
- stock consistency validations and rebuilds.

Measured outputs where EU5 tooling permits:

- monthly tick elapsed time;
- script profiler time by effect or file;
- save size before/after twelve months;
- log volume in normal versus debug/audit mode.

## Economic equivalence record

Every optimisation PR must capture before/after values for the same save and
month window:

- total country stock by sampled country-market-good;
- market aggregate for the same goods;
- production admitted/rejected;
- US-10 requested/satisfied/unsatisfied;
- trade quantities and US-17/US-20 deltas;
- US-04 removed/restored quantities and Estate charge/refund;
- country-market capacity;
- CORE-04 last-known market;
- validation failure/rebuild counts.

A performance improvement with an unexplained economic delta is a failed test.

## Static validation for future PRs

Before runtime measurement:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/validate_cbp_script_safety.sh
./tools/audit_cbp_persistent_state.sh
python3 tools/validate_ci_static_contracts.py
python3 tools/validate_cmm_configuration.py
git diff --check
```

Then install and run the relevant deterministic events and full revalidation.
Static CI success is not a performance result; it only proves that the candidate
is structurally testable.

## Decision

The architecture is not dominated by one obviously wrong world-times-country
loop anymore. The largest remaining gains should come from reducing write
amplification and making repeated preparation idempotent before attempting
another ownership rewrite.

Priority order:

```txt
P3 observability gating
-> P1 country-market capacity stamp
-> measure
-> P5 Performance Mode iterator narrowing
-> P6 sparse US-04
-> P4 traversal fusion
```

This order maximizes reversible, evidence-producing changes before touching the
business-sensitive traversal boundaries.

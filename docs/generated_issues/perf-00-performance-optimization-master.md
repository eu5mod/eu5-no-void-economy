# Master Issue - Performance Optimization

## Context

ModeU5 has accumulated several performance layers around generated stock
adapters, dirty validation, active-market indexes, and relationship traversal.
The original optimization model was useful but incomplete because it sometimes
treated the monthly runtime as if it started from a global/root scope.

Confirmed correction:

```txt
monthly_country_pulse already iterates every country.
The current monthly ModeU5 entry point is called once per country, with that
country as the current scope.
```

Therefore, the safe monthly country-owned loop is:

```txt
current pulse country -> every_market_present_in_country -> active/generated goods
```

It is not:

```txt
market -> country -> good
```

and it must not accidentally become:

```txt
country pulse -> market -> every_country -> good
```

## Core Architectural Rule

Separate three categories of work.

### 1. Country-Owned Work

Country-owned work must still run for every relevant country-market-good tuple:

```txt
country -> every_market_present_in_country -> good
```

Examples:

- country storage-capacity refresh once per country-market;
- country production recognition;
- stock admission into country-market-good stock;
- US-00 country x market x good ledger updates;
- country-owned stock/capacity debug.

Do not skip this work just because the market was already seen by another
country in the same monthly cycle. Countries sharing a market still own distinct
stock and ledger records.

### 2. Market-Owned Work

Market-owned work may be deduplicated once per market per cycle:

```txt
monthly seen/active market -> cached countries present in market -> active goods
```

Examples:

- market aggregate maintenance;
- market-level validation scheduling;
- market-level audit/repair;
- market-level diagnostics.

This category may use a seen/processed-market registry, but only when the task
is genuinely market-owned and independent from unprocessed country-owned work.

### 3. Good-Specific Work

Good-specific work should stay narrow:

```txt
known country/market relation -> one good
```

Never loop all goods when one good is already known.

## Monthly Seen-Market Registry

Add and maintain:

```txt
modeu5_monthly_markets_seen_this_cycle
modeu5_monthly_markets_seen_new_count
modeu5_monthly_markets_seen_duplicate_count
modeu5_monthly_market_seen_stamp
```

The registry is reset once per calendar month and populated during the monthly
country-owned pass:

```txt
current pulse country
  -> every_market_present_in_country
    -> mark market seen
    -> process generated goods for this country-market tuple
```

Important:

```txt
The registry is a scheduling/diagnostic index.
It is not a stock source.
It must not skip country-owned processing.
```

`duplicate_count > 0` means several countries in the monthly country-pulse cycle
were present in the same market. That is expected in shared markets and is not a
failure by itself.

## Optimization Track Status

### Implemented

| Track | Implemented result | Validation status |
|---|---|---|
| PERF-01 - Low-risk quick wins | Zero-work guards, zero-value map hygiene, explicit normal/debug/audit flags, and no frequent full validation. | Implemented; validate through the PERF-01 runbook when touching runtime gates. |
| PERF-02 - Native relationship traversal | Country-driven flows prefer `every_market_present_in_country`; human-relevant market discovery uses native country-to-market traversal. | Implemented; PERF-02 probe validates owned-location market coverage. |
| PERF-03 - Current-market country work cache | Market-driven scans rebuild a current-market work list from `market -> every_location_in_market -> guarded owner`. | Implemented with MVP boundary; it is a rebuilt work cache, not a durable per-market record. |
| PERF-04 - Monthly US-00 loop fusion | Monthly US-00 all-goods dispatcher follows `current country -> every_market_present_in_country -> generated goods`. | Implemented; validate with US-00 controlled and monthly runtime tests. |
| PERF-05 - Reduce global market scans | Active market lists, active validation, dirty reconciliation, and validation-triggered rebuild reduce unnecessary exhaustive scans. | Implemented; validate with the US-11 dirty/active reconciliation dump. |
| PERF-06 - Country-pulse scope contract and seen-market registry | Monthly reconciliation reuses the current pulse country as controller and records markets seen during the monthly country cycle. | Implemented in PR #74; US-11 runtime validation passed on commit `2cb1ca4d65b326f0fb5aad0e55e23fbd5fc947c9`. |
| PERF-07 - Market-owned runtime pass boundary | Active validation rebuilds the current-market country work cache once per active market, then validates active goods from that prepared cache. | Implemented; validate with the PERF-07 market-owned runtime dump in the US-11 deterministic reconciliation test. |
| PERF-08 - Shared storage capacity cache | US-02 capacity is persisted once per country-market and read by all generated per-good adapters instead of being recomputed and stored once per good. | Implemented by the shared-capacity PR; validate with US-02 and CORE-01 capacity-enforcement tests. |
| PERF-09 - Good-neutral US-02 capacity refresh | Shared capacity refresh is hand-authored as a good-neutral effect and no longer routes through `good_wheat` generated helpers. | Implemented by issue #89 follow-up; validate with US-02, CORE-01, CORE-02, and main revalidation tests. |
| PERF-10 - Per-good loop audit and preservation | `tools/audit_modeu5_per_good_loops.sh` documents and guards the remaining legitimate generated per-good loops while blocking shared-capacity regression. | Implemented; validate with `./tools/validate_module_packages.sh`. |
| PERF-11 - Active-list semantics and repair | Generated active-list repair rebuilds active market-good scheduling lists from stock, aggregate, ledger, and dirty state while ignoring capacity-only maps. | Implemented as debug/maintenance repair; validate through main revalidation's `perf10_13_active_repair_metrics` scenario. |
| PERF-12 - Market-scope value/link probes | `produced_in_market:<good>`, `stockpile_in_market(goods:<good>)`, and `traded_in_market:<good>` have controlled runtime probes. | Implemented; TECH-01 135 confirms the traded-in-market value syntax and scope, but runtime use belongs to a separate feature PR. |
| PERF-13 - Batch and metrics layer | Active-list repair emits focused debug metrics only when explicitly invoked by test/debug code. | Implemented for the current bottleneck; metrics remain disabled in normal runtime. |
| PERF-15 - Narrow US-00 monthly good dispatch | US-00 monthly helpers read the production gate before full record load, use a country-scoped active-record marker for previous-state detection, and avoid loading the same record twice during monthly clear. | Implemented in the PERF-15 PR; validate with main revalidation and US-00 monthly runtime dumps. |
| PERF-16 - Persistent-state audit | `docs/technical/PERSISTENT_STATE_AUDIT.md` and `tools/audit_modeu5_persistent_state.sh` classify the structured persistent map/list surface before minimal-persistence work starts. | Implemented as static guardrail; validate with `./tools/audit_modeu5_persistent_state.sh` and `./tools/validate_module_packages.sh`. |
| PERF-17 - Minimal US-00 carryover record | Normal runtime keeps US-00 production penalty and active marker while writing full diagnostic ledger maps only in strict/debug/audit mode. | Implemented as opt-in strict fallback plus minimal default; needs runtime strict/minimal comparison before release validation. |
| PERF-18 - UI-bound monthly summary counters | Generated per-good UI counters persist current-month surplus and consumption only for human country UI scope, without creating stock/capacity shadow maps. | Implemented as UI counter surface; consumption remains unavailable until US-10 writes a real counter. |
| PERF-19 - Human-relevant full-ledger policy | Accounting persistence now supports Minimal, Human-Relevant Full Ledger, and Strict Full Ledger; human-relevant mode gates full US-00 diagnostic ledger writes to markets in the human-relevant list. | Implemented as opt-in policy; validate with the CMM save-mode setting and main revalidation. |
| PERF-20 - Migration, audit, and validation guardrails | Generated migration helpers clear retired US-00 diagnostic ledger fields while preserving stock, capacity, production penalty, and active markers. | Implemented as explicit migration primitive; runtime migration smoke remains pending. |

### To Be Implemented

| Track | Why it remains open | Required condition |
|---|---|---|
| Durable per-market country-list cache | The current PERF-03 list is rebuilt for one target market, not persisted per market. | Requires TECH-01 126 or another confirmed static/generated storage design. |
| Market-change repair hook | Ownership changes are handled, but a dedicated market reassignment hook is not confirmed. | Requires TECH-01 127 confirmation or an accepted explicit rebuild/repair cadence. |
| Human/performance mode policy | Human-relevant market lists exist as rare discovery helpers, but no player-facing performance mode is selected. | Needs a concrete runtime use case and testable player/debug contract. |
| Log-noise cleanup | UTF-8 BOM warnings, metadata warnings, and static modifier localization placeholders make review harder. | Hygiene PRs should classify or remove each warning without weakening tests. |
| PERF-14 | Fourth-phase candidate from issue #94 remains analysis or future scoped work. | Reassess after PERF-16 through PERF-20 runtime validation. |

### Not Actual / Not Relevant Anymore

| Former idea | Decision | Reason |
|---|---|---|
| Main monthly runtime as `market -> country -> good` | Not actual. | `monthly_country_pulse` already iterates countries; ModeU5 starts from the current country scope. |
| Monthly country pulse followed by `market -> every_country -> good` | Invalid anti-pattern. | It creates `country -> market -> country -> good`, which duplicates work and can mix controllers. |
| Using seen-market lists to skip country-owned work | Invalid anti-pattern. | Countries sharing one market still own distinct stock, capacity, and ledger records. Seen-market lists are scheduling/diagnostic indexes only. |
| PR #71 / non-territorial market presence as an MVP blocker | Not relevant for current MVP performance work. | Non-owned/non-territorial market presence is accepted as negligible economic weight unless future dumps show meaningful stock/capacity there. |
| Dynamic variable-list names or Market-owned variable records | Not confirmed. | Market scope variable storage and runtime list-name construction are not confirmed; use generated static names or rebuilt global work lists only. |
| Single country-level location pool divided across markets | Implemented by PERF-08. | The gameplay design was accepted for the storage-capacity performance PR: capacity still persists as country x market, but each record is the current market trade-capacity contribution plus the country location-pool share. |

## Review Label Policy For This Track

A validation comment with `PASS` proves the tested scenario for one commit. It
does not automatically mean the PR should receive `ai-review:ok`.

Add `ai-review:ok` only when:

- required dumps and PASS markers are present;
- `error.log`, `game.log`, `debug.log`, and `system.log` have been reviewed;
- any remaining errors are explicitly classified as tolerated, vanilla noise,
  or non-blocking technical debt;
- the PR body and issue status reflect the real scope.

## Updated Loop-Order Matrix

| Context | Recommended Loop Order | Notes |
|---|---|---|
| Monthly country-owned stock cycle | `current pulse country -> every_market_present_in_country -> generated goods` | Main implemented monthly country-owned path. Do not skip country work because a market was seen before. |
| Monthly market-owned maintenance | `seen/active market -> cached countries_present_in_market -> active goods` | Implemented for active validation through the rebuilt current-market work cache. Not used to skip country-owned monthly work. |
| Dirty validation | `dirty market-good indexes -> validation source scan` | Frequent repair path; avoid full validation. |
| Active validation | `active market -> per-good active membership -> validation` | Audit/maintenance path. |
| Full audit | `all markets -> all goods` | Manual/debug/migration only. |
| Country ownership event | `known country/location -> every_market_present_in_country -> active goods` | Country is already known. |
| Building/capacity event | `known country -> every_market_present_in_country -> active goods` | Country is already known. |
| Human performance filter rebuild | `human country -> every_market_present_in_country -> relevant markets` | Rebuild rarely. |
| Good-specific event | `known country/market relation -> single good` | Never loop all goods if only one good is affected. |
| Initialization | `market/good with positive source -> eligible countries -> active goods` | Skip zero-source markets before heavy processing. |

## Implementation Rules

- Treat `monthly_country_pulse` and `yearly_country_pulse` as country-scoped
  engine iterators.
- Use the current pulse country as controller for monthly country-scoped
  validation/reconciliation entry points.
- Keep a global fallback controller only for initialization, audit, and debug
  entry points that may not already have a country scope.
- Keep country-owned work and market-owned work separate.
- Do not use market-seen registries, active lists, or relationship caches as
  stock sources.
- Do not skip country-owned stock/ledger/capacity work based on a market-seen
  list.
- Keep full audits available for manual repair and migration.
- Preserve centralized stock mutation rules.

## Acceptance Criteria

- Monthly country-owned runtime follows:

```txt
current country -> every_market_present_in_country -> generated goods
```

- `modeu5_monthly_markets_seen_this_cycle` is reset once per month and records
  markets encountered by country pulses.
- Duplicate market encounters are counted but do not suppress country-owned
  processing.
- Monthly reconciliation does not perform a redundant `every_country` controller
  scan when called from a country pulse.
- Active validation and dirty validation keep PASS markers and readable dumps.
- TECH-01 documents the corrected monthly country-pulse semantics.
- PR validation comments include dumps from `debug.log`.

## Recommended Validation

Build/install:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Runtime:

```txt
Start a disposable campaign.
Wait until CORE-02 initialization completes.
Wait at least one monthly tick.
Run event modeu5_debug.1.
Choose "Test US-11 dirty-record reconciliation".
```

Expected logs:

```txt
ModeU5 US-11 DUMP dirty_reconciliation records_checked=1 inconsistencies=1 rebuilds=1 failures=0 market_stock=150.00
ModeU5 US-11 DUMP empty_reconciliation records_checked=0 inconsistencies=0 rebuilds=0 failures=0
ModeU5 US-11 DUMP active_reconciliation type=3 records_checked=1 inconsistencies=1 rebuilds=1 failures=0 market_stock=150.00
ModeU5 US-11 RESULT reconciliation PASS
```

Also inspect, when available:

```txt
modeu5_monthly_markets_seen_new_count
modeu5_monthly_markets_seen_duplicate_count
```

## Known Limitations

- The implemented market-owned pass uses the current-market rebuilt work cache;
  it is not a durable per-market country-list cache.
- Durable per-market country-list storage is still not confirmed.
- Active lists are scheduling indexes and may be overinclusive.
- Full market-first runtime processing remains future work because the engine
  monthly pulse is country-scoped.

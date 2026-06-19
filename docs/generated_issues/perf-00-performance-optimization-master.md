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

- country storage-capacity refresh;
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

## Current Optimization Tracks

| Track | Status | Notes |
|---|---|---|
| PR 1 - Low-risk quick wins | Completed | Zero-work guards, no zero persistence, debug/audit/runtime mode flags, no full validation in frequent ticks. |
| PR 2 - Native relationship traversal | Completed | Country-driven flows prefer `every_market_present_in_country`; PERF-02 validates native iterator behavior. |
| PR 3 - Market-to-country work cache | Completed with MVP boundary | Current-market work cache rebuilt from `every_location_in_market`; durable per-market country lists remain not confirmed. |
| PR #71 - Non-territorial market-presence probe | Deferred | Non-owned/non-territorial market presence is accepted as negligible MVP risk; documented in TECH-01 128. |
| PERF-04 - Monthly US-00 loop fusion | Implemented / requires runtime validation | Refactors US-00 monthly all-goods dispatcher to `country -> market -> goods`. |
| PERF-05 - Reduce global market scans | Implemented / requires runtime validation | Adds active market lists, active validation, and validation-triggered rebuild without a second source scan. |
| PERF-06 - Country-pulse scope contract and seen-market registry | In progress | Confirms monthly country pulse as the outer country loop, avoids redundant controller scans, and records markets seen this cycle. |
| Future market-owned runtime pass | Not started | Only after semantics are safe: `seen/active market -> cached countries -> active goods`. |
| Performance mode | Not started | Human-relevant market mode remains future work. |

## Updated Loop-Order Matrix

| Context | Recommended Loop Order | Notes |
|---|---|---|
| Monthly country-owned stock cycle | `current pulse country -> every_market_present_in_country -> generated goods` | Main implemented monthly country-owned path. Do not skip country work because a market was seen before. |
| Monthly market-owned maintenance | `seen/active market -> cached countries_present_in_market -> active goods` | Future structural target; only for genuinely market-owned tasks. |
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

- The seen-market registry does not yet implement the full future market-owned
  runtime pass.
- Durable per-market country-list storage is still not confirmed.
- Active lists are scheduling indexes and may be overinclusive.
- Full market-first runtime processing remains future work because the engine
  monthly pulse is country-scoped.

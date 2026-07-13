# CORE-04 — Market-entry stock persistence runtime coverage

Labels: `module:core`, `stock-persistence`, `performance-mode`, `runtime-coverage`

## Purpose

Implement runtime coverage for countries entering a market without an existing
`country x market x good` stock record.

The current stack has:

- CORE-03 runtime coverage for location owner changes in the same market:
  `old owner x market x good -> new owner x same market x good`.
- PERF-14 promotion coverage for Performance Mode:
  `market aggregate x good -> country x market x good records`.
- CORE-04 documentation/scaffold for market-topology stock persistence, but not
  the actual runtime implementation.

The missing runtime coverage is:

1. a country enters a new market because market frontiers/topology change;
2. a same-owner location moves from one market to another;
3. a country receives a location in a market where it previously had no
   `country x market x good` record;
4. the above behaves correctly in Normal Mode, Performance Mode, and Deactivated
   mode.

## Implementation status

This branch implements the explicit runtime migration layer:

- `cbp_prepare_core04_market_entry_stock_migration` accepts an explicit
  `country`, `source_market`, `target_market`, and `location`;
- generated per-good helpers move stock through `cbp_transfer_stock`;
- Normal Mode migrates directly;
- Performance Mode calls the stock-mutation gate and promotes human-relevant
  markets before mutation;
- Deactivated Mode blocks and logs a diagnostic;
- a location last-known-market memory is refreshed at campaign initialization
  and after monthly country pulses.

The location market memory is not yet consumed as an automatic stock-migration
source. TECH-01 141 tracks the remaining exposure question: whether a market
scope persisted on a location can safely be re-entered as a script scope later.
Until that is confirmed, stock-affecting CORE-04 callers must pass
`old_market/source_market` and `new_market/target_market` explicitly.

## Core rule

For first entry into a new market, reuse the CORE-03 storage-share principle:

```txt
stock portion moved = storage portion moved
```

For one country, one good, and one first-entry market transition:

```txt
source_stock_before = S
source_capacity_before = C
moved_storage_capacity = D

if C > 0:
  move_ratio = clamp(D / C, 0, 1)
else:
  move_ratio = 0

requested_stock_move = S * move_ratio
```

Then move:

```txt
same country x old market x good
  -> same country x new market x good
```

This is not trade. It must not create trade income, transport cost, demand
records, market-price side effects, or location-level stock persistence.

## Required behavior

### 1. Same-owner market topology change

When a location remains owned by the same country but changes from `old_market`
to `new_market`:

```txt
country A owns location L
L moves from market X to market Y
country A did not previously have persisted stock/capacity history in market Y
```

Then:

1. detect whether `new_market` is new for `country A`;
2. if `new_market` is new:
   - read `country A x old_market x good` stock before capacity refresh;
   - read `country A x old_market` storage capacity before capacity refresh;
   - compute moved location storage capacity using the existing US-02
     location-capacity helper;
   - move proportional stock from `old_market` to `new_market` for every
     generated stock good;
   - mark `country A x new_market` as known;
   - refresh capacities for both markets;
   - mark market-country caches dirty for both markets;
   - validate affected market-good aggregates;
3. if `new_market` is already known for `country A`:
   - do not move stock;
   - preserve existing stock in both markets;
   - refresh capacities/caches only;
   - emit an audit/debug line indicating known-market oscillation.

### 2. Location owner change into a market with no target record

Verify and, if needed, harden CORE-03 so this case is explicitly covered:

```txt
location L in market X changes owner from country A to country B
country B did not previously have country x market X stock records
```

Expected behavior:

```txt
A x market X x good -> B x market X x good
```

using the existing CORE-03 storage-share succession rule.

Add explicit regression coverage proving that the transfer creates or initializes
the target country-market stock record when it is missing.

### 3. Market creation or replacement

If a new market receives a country for the first time:

- perform first-entry stock settlement only when old/source market transition
  data is confirmed;
- if no safe source market or successor market is available, do not guess;
- emit a blocking CORE-04 audit diagnostic;
- leave stock unchanged until an explicit successor/source mapping is available.

### 4. Market removal or merge

If an old market has a confirmed successor:

```txt
old_market -> successor_market
```

migrate stock before old keys are cleared.

If no successor is known:

- do not silently delete stock;
- emit a CORE-04 blocked diagnostic;
- preserve stock records until a safe migration path exists.

## Mode behavior

### Normal Mode

```txt
cbp_no_void_economy_main=2
performance=0
normal=1
deactivated=0
```

Expected:

- detailed country-market stock is active;
- first-entry migration creates/updates `country x new_market x good`;
- no promotion is required;
- market aggregate remains equal to the sum of country stock records.

### Performance Mode

```txt
cbp_no_void_economy_main=1
performance=1
normal=0
deactivated=0
```

Expected:

- if the market is human-relevant, promote/materialize the market before detailed
  stock mutation;
- if promotion succeeds, detailed first-entry migration may proceed;
- if the market is not human-relevant, do not create detailed country-market
  records through the topology path unless the approved gate says detailed
  accounting is allowed;
- use vanilla fallback or blocked diagnostics according to the existing PERF-14
  gate contract;
- never branch directly on read-only eligibility alone.

Safe gate distinction:

```txt
read-only eligibility:
cbp_detailed_country_market_accounting_enabled_trigger

stock-affecting mutation permission:
cbp_detailed_country_market_stock_mutation_allowed_trigger
```

Relevant existing gates/helpers:

```txt
cbp_prepare_stock_mutation_accounting_mode
cbp_detailed_country_market_stock_mutation_allowed_trigger
cbp_market_detailed_accounting_promoted_trigger
cbp_promote_market_to_detailed_accounting
```

### Deactivated

```txt
cbp_no_void_economy_main=3
performance=0
normal=0
deactivated=1
```

Expected:

- no ModeU5 stock-affecting topology migration;
- emit a blocked diagnostic if the topology handler is reached.

## Implementation guidance

Reuse existing helpers where possible:

```txt
cbp_rebuild_countries_present_in_market
cbp_rebuild_and_refresh_country_storage_capacities
cbp_recalculate_saved_country_storage_capacities
cbp_recalculate_country_market_capacity_shared
cbp_calculate_location_storage_capacity
cbp_transfer_stock
cbp_validate_stock_consistency
cbp_promote_market_to_detailed_accounting
cbp_prepare_stock_mutation_accounting_mode
cbp_detailed_country_market_stock_mutation_allowed_trigger
cbp_market_detailed_accounting_promoted_trigger
```

Do not duplicate capacity or allocation formulas. If a reusable storage-share
allocator is needed, extract one helper and use it from CORE-03 and CORE-04 rather
than creating a second formula.

Suggested new helper contracts:

```txt
cbp_country_market_known_trigger = {
  country = <country>
  market = <market>
}

cbp_mark_country_market_known = {
  country = <country>
  market = <market>
}

cbp_prepare_core04_market_entry_stock_migration = {
  country = <country>
  source_market = <old market>
  target_market = <new market>
  location = <location>
}

cbp_move_country_market_stock_by_storage_share = {
  country = <country>
  source_market = <old market>
  target_market = <new market>
  moved_storage_capacity = <capacity contribution>
}
```

All stock writes must still go through centralized CORE-01 operators.

## Audit logging

Add explicit `ModeU5 CORE-04` log lines for all important branches.

Expected patterns:

```txt
ModeU5 CORE-04 MARKET_ENTRY mode=normal result=migrated country=... source_market=... target_market=... moved_capacity=... source_capacity=... ratio=...
ModeU5 CORE-04 MARKET_ENTRY mode=performance result=promoted_and_migrated country=... source_market=... target_market=... promotion_result=1
ModeU5 CORE-04 MARKET_ENTRY mode=performance result=vanilla_fallback country=... target_market=... reason=market_not_human_relevant
ModeU5 CORE-04 MARKET_ENTRY result=known_market_oscillation country=... source_market=... target_market=... moved_stock=0
ModeU5 CORE-04 MARKET_ENTRY result=blocked reason=missing_old_new_market_scope
ModeU5 CORE-04 MARKET_ENTRY result=blocked reason=cbp_deactivated
```

Update `./tools/summarize_test_cbp_logs.sh` to include:

```txt
CORE-04 topology diagnostics: <n>
```

and a section:

```txt
CORE-04 topology diagnostic lines:
...
```

## Validation / test coverage

Add or extend debug event coverage so the following scenarios are explicit:

1. **Normal Mode first-entry topology migration**
   - country has stock in old market;
   - target market is unknown;
   - location enters target market;
   - proportional stock moves;
   - market aggregates remain conserved.

2. **Performance Mode first-entry topology migration**
   - target market is human-relevant or becomes human-relevant;
   - promotion occurs if needed;
   - detailed migration proceeds only after mutation permission is true;
   - aggregates remain conserved.

3. **Performance Mode non-human-relevant market**
   - no detailed country-market mutation;
   - vanilla fallback or blocked result is logged according to the existing gate
     contract.

4. **Known-market oscillation**
   - country already has known history in both markets;
   - location moves between them;
   - no stock moves;
   - capacities/caches refresh.

5. **Location owner change into missing target record**
   - loser has stock in market;
   - winner has no stock record in that market;
   - owner change creates/updates winner record correctly;
   - test in Normal Mode and Performance Mode.

6. **Missing old/new market exposure**
   - do not guess;
   - log blocked diagnostic;
   - preserve stock.

## Acceptance criteria

- No location-level stock storage is introduced.
- No stock is dropped when a country first enters a market.
- First-entry migration uses storage-share proportional movement.
- Known-market oscillation does not move stock.
- Location owner changes initialize missing target country-market stock records.
- Performance Mode never mutates detailed country-market stock unless the market
  is promoted or the mutation gate allows it.
- Normal Mode works without promotion.
- Deactivated mode blocks.
- Market aggregates remain equal to country stock sums after migration.
- Re-running migration/promotion does not duplicate stock.
- Summary script surfaces CORE-04 topology diagnostics.
- Runbook and #119/#CORE-04 docs are updated with Normal vs Performance examples.

## Static checks target

```txt
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/audit_cbp_persistent_state.sh
./tools/normalize_cmm_value_links.sh --check
python3 ./tools/validate_cmm_configuration.py
./tools/audit_cbp_per_good_loops.sh
git diff --check
```

## Runtime validation target

```txt
event cbp_core04_debug.1
event cbp_perf14_debug.1
./tools/summarize_test_cbp_logs.sh
```

Expected runtime summary should include:

```txt
CORE-04 topology diagnostics: ...
ModeU5 CORE-04 MARKET_ENTRY ... result=migrated ...
ModeU5 CORE-04 MARKET_ENTRY ... result=known_market_oscillation ...
ModeU5 CORE-04 MARKET_ENTRY ... result=blocked ...
ModeU5 PERF-14 RESULT performance_mode_cmm PASS
```

## Deliverable scope

Open the implementation PR stacked on `feature/perf14-sparse-supplier-cache`.
Keep the PR scoped to CORE-04 topology/first-entry stock persistence and explicit
regression coverage. Do not implement sparse supplier cache or US-10 UI work in
this PR.

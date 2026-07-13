# PERF-14 / US-10-UI Master PR — Performance Mode, Sparse Supplier Cache, and Stock Resolution Visibility

## Scope

This master PR prepares the next feature branch after the #109 fast-path/pruning work. It covers three linked concerns:

1. Replace the #109 MVP “generated per-good pruning before expensive reads” with a true sparse supplier cache/list where lifecycle and invalidation are safe.
2. Specify and implement CMM `cbp_no_void_economy_main` option 1: `Activate (Performance Mode)`.
3. Implement the debug/read-only visibility required by #37 / US-10-UI for stock resolution.

This is intentionally a master/scaffold PR. Implementation commits may be split into narrower child PRs if needed.

## CMM performance mode contract

`cbp_no_void_economy_main` is interpreted as:

| Option | Meaning |
|---:|---|
| 1 | Activate Performance Mode |
| 2 | Activate Normal Mode |
| 3 | Deactivated |

Performance Mode narrows detailed Market x Country accounting.

### Performance Mode eligibility

In Performance Mode, detailed country x market x good accounting is maintained
for human-relevant markets. A market is human-relevant when at least one
human-played country is present in it through the confirmed iterator:

- `every_country limit = { is_ai = no }`; then
- `every_market_present_in_country`.

Once a market is human-relevant and promoted, all stock-affecting country x
market mutations inside that market use the detailed path, including AI country
records. This preserves the central invariant that the market stock is a cache
of country stocks.

Phase 1 uses the confirmed country-market iterator as the human-relevant market
discovery path:

```txt
every_country limit = { is_ai = no }
  -> every_market_present_in_country
```

The human-relevant list is a scheduling/detail gate, not authoritative stock
state. ModeU5 must not pre-materialize zero-valued country x market x good
records for every possible tuple. When a previously non-detailed market becomes
human-relevant, the accounting gate may mark it as human-relevant on demand for
read-only eligibility. It does not split aggregate stock or authorize
stock-affecting detailed mutation by itself. Capacity refresh and stock/ledger
creation still belong to the existing US-02 and CORE-01/CORE-02/CORE-03/US-00
paths.

Two edge cases are explicitly in scope for the first stacked PR:

- new country finalizers refresh the new country's storage-capacity records and
  mark its present markets as human-relevant if the new country is human-played;
- a human country entering a new market converts that market from non-detailed
  to detailed either through the CORE-03 owner-change hook or on demand when the
  country-market accounting gate sees the market in
  `every_market_present_in_country`.

For this first read-only plumbing PR, “detailed accounting enabled” means the
country-market pair is eligible for detailed accounting diagnostics. It must
not be treated as permission for stock-affecting code to mutate country x
market records until the dedicated promotion initializer below exists and
succeeds.

If later tests prove this iterator is broader than the desired
owned-location-market definition, the fallback PR must either accept that scope
or introduce a confirmed narrower discovery hook. Do not replace it with an
unconfirmed one-off scan in the hot path.

Normal Mode keeps the existing broad accounting behavior.

Deactivated Mode should not run the main NVE economic mutations where supported by the current module-option model.

## Vanilla fallback contract

When a market is not eligible for detailed accounting in Performance Mode,
ModeU5 must not silently create partial country-market state and must not invent
a second aggregate-only stock system. The fallback is vanilla behavior: ModeU5
skips its stock-affecting runtime logic for that market and logs that the market
was left to vanilla.

Initial consumers to gate:

- US-00 monthly production ingestion and ledger writes;
- US-10 monthly consumption / transfer resolution;
- US-03 monthly decay;
- US-17 trade-efficiency repurpose / reconciliation;
- US-20 trade-maintenance received-goods loss factor.

Fallback rule:

```txt
if market_runtime_accounting_mode(market) = detailed:
  apply ModeU5 mutation through country x market stock maps and market aggregate
else:
  skip ModeU5 mutation for this market
  leave vanilla economy behavior untouched
  record debug/audit that ModeU5 used vanilla fallback for this market
```

This avoids high-cardinality country x market storage for non-human-relevant
markets without weakening the central invariant. There is no persistent
ModeU5-only market aggregate for skipped markets.

## Monthly runtime business rule

Performance Mode is a market-level runtime filter, not a replacement economy.

The monthly runtime rule is:

```txt
1. Identify human-relevant markets.
2. monthly_country_pulse
   -> every_market_center_in_country
   -> cbp_prepare_market_runtime_accounting_mode(market)
3. If the market is human-relevant and promoted:
   -> run the normal ModeU5 detailed runtime for that market
   -> use centralized stock operators such as add/remove/transfer/decay through
      their existing callers
   -> run the relevant ModeU5 balance mechanisms for that market
4. Otherwise:
   -> skip ModeU5 stock-affecting runtime for that market
   -> leave vanilla behavior untouched
   -> log vanilla fallback when debug/audit is active
```

Current implementation boundary:

- US-00 monthly production ingestion, rejection ledger, overproduction ratios,
  void wealth, and production-penalty bookkeeping are gated by the market
  runtime decision.
- US-10 monthly consumption and inter-market transfer resolution are gated by
  the same market runtime decision.
- US-03 decay, US-17, US-20, and any future monthly balancing/runtime systems
  must use this same gate before invoking stock-affecting ModeU5 logic.
- US-09 static/generated economy rebalance overrides are package-level static
  data, not a monthly stock mutation path. If a future US-09-adjacent runtime
  balance mechanic is added, it must follow the same market runtime rule.

This preserves the spirit of the mod in human-relevant markets while avoiding
side effects and high-cardinality storage in markets where vanilla behavior is
the intended fallback.

## Sparse supplier cache/list objective

#109 accepted generated per-good pruning before expensive reads as the MVP. This follow-up should replace that with a true sparse supplier path where safe.

Target behavior:

- Prepare per-good meaningful supplier lists for the current market before US-10
  candidate scans. This first safe layer is rebuilt on demand from the existing
  `cbp_countries_present_in_market` cache, so it cannot become stale across
  market/country movement.
- Include only countries with meaningful stock or production/balance state for that market/good.
- Exclude countries that have no stock and no relevant monthly added/requested signal before relation/scoring work.
- Preserve the all-country `cbp_countries_present_in_market` scan as a fallback/debug path.
- Keep durable invalidation/repair out of this layer unless a later PR introduces
  persisted market x good supplier caches. On-demand rebuild is the safety
  mechanism for now.
- Do not introduce direct stock mutation; keep centralized operators authoritative.

## US-10-UI / #37 visibility objective

The UI/debug layer remains read-only. It must not create a second authoritative resolver or outcome map.

Required visible fields:

- demand type: consumption vs inter-market transfer;
- demanding/consumer/buyer country;
- source market and target market where relevant;
- good;
- requested, satisfied/transferred, and unsatisfied quantities;
- ordered candidate trace;
- candidate bucket, score, stock, selected quantity, actual mutated quantity;
- exclusion reason ID and human-readable reason;
- aggregate prefilter used/blocked markers;
- own-stock fast-path used/taken markers;
- whether detailed country x market accounting was skipped by Performance Mode;
- whether vanilla fallback was used.

Same-market consumption must be labelled as non-trade. Inter-market transfer must show source, target, target capacity policy, actual transferred quantity, and unsatisfied transfer quantity.

## Implementation outline

### Phase 1 — specification and CMM plumbing

- Add parser-safe helpers for reading the `cbp_no_void_economy_main` CMM setting.
- Define temporary flags:
  - `cbp_cbp_main_mode`
  - `cbp_performance_mode_enabled`
  - `cbp_detailed_country_market_accounting_enabled`
  - `cbp_market_level_fallback_required`
- Add debug capture for the resolved mode and accounting decision.
- Update localization/tooltips so Performance Mode explicitly says it tracks human-relevant market detail only.

Implementation note for the first stacked PR:

- `cbp_refresh_cbp_main_mode_from_cmm_country_scope` derives script-safe
  `performance`, `normal`, and `deactivated` runtime flags from CMM.
- Performance Mode refresh rebuilds `cbp_performance_relevant_markets` from
  human countries with `every_market_present_in_country`.
- The rebuild is monthly-stamped so `monthly_country_pulse` does not rebuild the
  global human-relevant list once per country.
- `cbp_prepare_country_market_accounting_decision` can mark a human-present
  market as human-relevant on demand when it was not yet in the list.
- CORE-03 owner-change and new-country finalizer hooks opportunistically mark
  new human-relevant markets without waiting for the next monthly rebuild.
- `cbp_prepare_country_market_accounting_decision` computes the read-only
  country-market decision used by the later mutation and vanilla-fallback gates.
- `event cbp_perf14_debug.1` validates CMM values `1/2/3`, the rebuilt
  human-relevant market list, the non-detailed -> detailed eligibility edge case,
  the positive human market-presence Performance Mode decision, and negative
  Performance Mode decisions for AI countries and human countries in markets not
  returned by `every_market_present_in_country`.
- The first stacked PR deliberately does not route real runtime stock mutations
  through the Performance Mode gate or prove the foreign-building-only negative
  case.
- The promotion initializer exists so later stock-affecting PRs have a safe
  boundary between read-only eligibility and detailed mutation permission.

### Promotion initializer

Before any later PR routes US-03 decay, US-10 resolution, US-17, US-20, or any
other stock-affecting path through the Performance Mode accounting gate, the
target market must have completed the dedicated promotion initializer:

```txt
cbp_promote_market_to_detailed_accounting = {
  market = <market>

  # no-op if the market is already promoted for the current schema/version
  # refresh country x market capacities for countries present in this market
  # allocate existing market-level aggregate stock into country records
  # preserve market aggregate exactly
  # mark affected market/good records dirty or validation-required
}
```

Promotion requirements:

- delegate to existing US-02 capacity refresh and CORE-02-style
  capacity-proportional allocation policy;
- split any existing market-level aggregate stock by the approved
  capacity-proportional allocation policy;
- preserve `sum(country x market stock) == market aggregate stock`;
- be idempotent, so running promotion twice cannot duplicate stock;
- only after successful promotion may stock-affecting code use detailed
  country x market mutation paths for that market.

Implemented boundary:

- `cbp_detailed_country_market_accounting_enabled` means read-only
  eligibility only.
- `cbp_market_detailed_accounting_promoted_trigger` proves that a market has
  completed detailed-accounting promotion in Performance Mode.
- `cbp_detailed_country_market_stock_mutation_allowed_trigger` is the
  stricter gate for later stock-affecting paths. In Normal Mode it remains true
  for detailed accounting; in Performance Mode it also requires the promotion
  marker.
- `cbp_promote_market_to_detailed_accounting` is idempotent, rebuilds the
  market countries-present cache, refreshes country x market capacity for
  present countries, materializes aggregate-only stock into country records by
  capacity share, preserves the market aggregate, and marks affected market-good
  records dirty for later validation.
- `event cbp_perf14_debug.1` covers positive aggregate-only promotion,
  idempotent re-run, partial-state promotion where some country stock already
  exists, and a negative non-human-relevant market path.

### Phase 2 — accounting gate and vanilla fallback

- Introduce a shared accounting gate effect used before country x market map writes.
- Add a market-runtime gate so monthly market-owned dispatch can decide once per
  market before traversing countries and goods.
- Skip ModeU5 stock-affecting runtime work when the gate selects vanilla
  fallback.
- Add audit logs for fallback usage without mutating ModeU5 stock maps.
- Block detailed stock-affecting country x market routing unless
  `cbp_detailed_country_market_stock_mutation_allowed_trigger` is true, and
  select vanilla fallback otherwise.

Second stacked PR boundary:

- `cbp_prepare_stock_mutation_accounting_mode` is the shared pre-mutation
  gate for future stock-affecting callers.
- The gate first reuses `cbp_prepare_country_market_accounting_decision`.
- In Normal Mode, it allows detailed country x market mutation immediately.
- In Performance Mode, the stock-affecting decision is market-level: if the
  target market is human-relevant but has not been promoted, it attempts
  `cbp_promote_market_to_detailed_accounting`.
- If the market is promoted, the gate sets
  `cbp_stock_mutation_use_detailed_accounting`.
- If the market is not human-relevant or promotion fails, the gate sets
  `cbp_stock_mutation_use_market_level_fallback`. In this master PR, that
  means vanilla fallback, not an aggregate-only ModeU5 mutation operator.
- If No Void Economy is deactivated, the gate sets
  `cbp_stock_mutation_blocked`.
- Once a market is promoted, all country x market stock mutations inside that
  market must use the detailed path, including AI countries, so the market
  aggregate remains a cache of the detailed country records.
- `cbp_prepare_market_runtime_accounting_mode` applies the same market-level
  rule at monthly dispatch time: promoted human-relevant markets enter ModeU5
  detailed runtime; non-human-relevant or failed-promotion markets use vanilla
  fallback; deactivated mode blocks ModeU5 runtime.
- US-00 monthly production ingestion and US-10 monthly demand resolution are
  gated by `cbp_prepare_market_runtime_accounting_mode`.
- This PR does not yet route US-03, US-17, or US-20 through the gate. Those
  callers must be wired in later stacked PRs and must not use the weaker
  read-only eligibility trigger as mutation permission.

### Phase 3 — sparse supplier lists

- Add per-good sparse supplier list generation for the current market.
- Update US-10 candidate scanning and bucket mutation loops to prefer sparse
  supplier lists.
- Keep all-country market scan behind fallback/debug mode.
- Validate that the sparse list is used only when available, that debug can
  force the all-country scan, and that no durable stale cache is introduced.

### Phase 4 — #37 debug visibility

- Add debug event/log output for last stock resolution and candidate/exclusion traces.
- Add human-readable localization for exclusion reason IDs.
- Ensure consumption and inter-market transfer displays differ clearly.
- Add Performance Mode fallback markers to the same diagnostics.

Implemented boundary for the #119 stack:

- `event cbp_us10_debug.1` includes `Run US-10 UI visibility summary`.
- `event cbp_revalidate_debug.1` includes `scenario=us10_ui_visibility`.
- `tools/summarize_test_cbp_logs.sh` prints `ModeU5 US-10-UI ...` lines
  and bounded US-10 candidate / mutation traces.
- The visibility layer is read-only and reuses existing stock, capacity,
  outcome, resolver-debug, sparse-supplier, and Performance Mode fallback
  values. It does not introduce a second authoritative UI map.
- Same-market consumption is labelled as non-trade and explicitly shows no
  trade income, no transport cost, and no trade-capacity usage.
- Market capacity, current overproduction, and Production Efficiency are shown
  as unavailable when no authoritative value is exposed; this layer must not
  guess those values.
- The current presentation is a localized debug/result-event and log summary,
  not a full custom scripted GUI panel.

## Acceptance criteria

- Performance Mode maintains detailed Market x Country accounting for promoted
  human-relevant markets returned by `every_market_present_in_country` from at
  least one human country.
- Foreign-building-only or indirect market presence remains a Phase 2 boundary question unless it is covered by the confirmed iterator.
- In Performance Mode, skipped non-human-relevant markets fall back to vanilla
  behavior rather than creating aggregate-only ModeU5 stock.
- US-03, US-17, and US-20 have explicit fallback plans/tests before they rely on detailed country x market state.
- US-10 supplier scanning prefers sparse supplier lists and only falls back to all-country scans in debug/fallback conditions.
- #37 debug visibility shows ordered candidates, exclusions, quantities, scores, final outcomes, and same-market vs inter-market distinction.
- No new direct stock mutation path is introduced.
- Existing #109 own-stock fast path, aggregate prefilter, reserve pruning, and monthly integration remain valid.

## Suggested tests

Static/generation:

```txt
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/audit_cbp_persistent_state.sh
./tools/normalize_cmm_value_links.sh --check
python3 ./tools/validate_cmm_configuration.py
git diff --check
```

Runtime/debug:

```txt
event cbp_us10_debug.1
event cbp_revalidate_debug.1
./tools/summarize_test_cbp_logs.sh
```

New targeted scenarios:

- Performance Mode human country owns a location in the market: the market
  becomes human-relevant and detailed accounting is retained after promotion.
- Performance Mode AI country in a human-relevant promoted market: detailed
  accounting is used because the market aggregate is now a cache of detailed
  country records.
- Performance Mode AI country in a non-human-relevant market: vanilla fallback
  is selected and ModeU5 stock mutation is skipped.
- Performance Mode human country has only foreign-building/indirect presence:
  detailed accounting is skipped and vanilla fallback is used unless a
  confirmed iterator later proves that presence should make the market relevant.
- Normal Mode: existing detailed accounting path remains available.
- Sparse supplier list: only countries with positive current stock for the good
  are scanned in the hot path; the full present-country scan remains available
  for debug/fallback.
- Debug fallback: all-country scan can still be forced for diagnostics.
- US-10-UI: candidate order, exclusion reason, and mutation quantity are visible for consumption and transfer.
- US-10-UI: run `Run US-10 UI visibility summary` and confirm
  `ModeU5 US-10-UI SUMMARY`, `RESOLUTION`, `CANDIDATE_TRACE`,
  `MUTATION_TRACE`, `FAST_PATH`, and `REASON_MAP` lines appear.

## Open design questions

- Whether a later durable sparse supplier cache should be keyed by market x good
  only, or market x good x accounting-mode. The current PR avoids that choice by
  rebuilding the list on demand.
- How much of US-17 / US-20 should be implemented in this master PR versus reserved for child PRs after the vanilla fallback gate exists.
- Whether Performance Mode should track all human-relevant markets for every human country in multiplayer, or only the current player country in single-player contexts.

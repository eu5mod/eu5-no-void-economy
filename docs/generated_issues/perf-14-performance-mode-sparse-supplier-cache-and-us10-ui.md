# PERF-14 / US-10-UI Master PR — Performance Mode, Sparse Supplier Cache, and Stock Resolution Visibility

## Scope

This master PR prepares the next feature branch after the #109 fast-path/pruning work. It covers three linked concerns:

1. Replace the #109 MVP “generated per-good pruning before expensive reads” with a true sparse supplier cache/list where lifecycle and invalidation are safe.
2. Specify and implement CMM `nve_no_void_economy_main` option 1: `Activate (Performance Mode)`.
3. Implement the debug/read-only visibility required by #37 / US-10-UI for stock resolution.

This is intentionally a master/scaffold PR. Implementation commits may be split into narrower child PRs if needed.

## CMM performance mode contract

`nve_no_void_economy_main` is interpreted as:

| Option | Meaning |
|---:|---|
| 1 | Activate Performance Mode |
| 2 | Activate Normal Mode |
| 3 | Deactivated |

Performance Mode narrows detailed Market x Country accounting.

### Performance Mode eligibility

In Performance Mode, detailed country x market x good accounting is maintained only when all of these are true:

- the country is human-played; and
- the market is returned by `every_market_present_in_country` for that country.

Phase 1 uses the confirmed country-market iterator as the human-relevant market
discovery path:

```txt
every_country limit = { is_ai = no }
  -> every_market_present_in_country
```

The human-relevant list is a scheduling/detail gate, not authoritative stock
state. ModeU5 must not pre-materialize zero-valued country x market x good
records for every possible tuple. When a previously non-detailed market becomes
human-relevant, the accounting gate promotes it on demand, refreshes/uses the
existing country x market capacity path, and lets CORE-01/CORE-02/CORE-03/US-00
create stock and ledger entries only through their normal non-zero mutation or
ledger-update paths.

Two edge cases are explicitly in scope for the first stacked PR:

- new country finalizers refresh the new country's storage-capacity records and
  mark its present markets as human-relevant if the new country is human-played;
- a human country entering a new market converts that market from non-detailed
  to detailed either through the CORE-03 owner-change hook or on demand when the
  country-market accounting gate sees the market in
  `every_market_present_in_country`.

If later tests prove this iterator is broader than the desired
owned-location-market definition, the fallback PR must either accept that scope
or introduce a confirmed narrower discovery hook. Do not replace it with an
unconfirmed one-off scan in the hot path.

Normal Mode keeps the existing broad accounting behavior.

Deactivated Mode should not run the main NVE economic mutations where supported by the current module-option model.

## Market-level fallback contract

When a country x market pair is not eligible for detailed accounting in Performance Mode, stock-changing systems must not silently disappear. They must fall back to market-level aggregate accounting.

Initial fallback consumers to plan for:

- US-03 monthly decay;
- US-17 trade-efficiency repurpose / reconciliation;
- US-20 trade-maintenance received-goods loss factor.

Fallback rule:

```txt
if detailed_country_market_accounting_enabled(country, market) = yes:
  apply mutation through country x market stock maps and market aggregate
else:
  apply mutation to the market aggregate only
  record debug that the country x market detail was skipped by Performance Mode
```

This keeps aggregate market stock meaningful for non-human / non-owned-location markets while avoiding high-cardinality country x market storage.

## Sparse supplier cache/list objective

#109 accepted generated per-good pruning before expensive reads as the MVP. This follow-up should replace that with a true sparse supplier path where safe.

Target behavior:

- Maintain per-good meaningful supplier lists keyed by market or active market/good.
- Include only countries with meaningful stock or production/balance state for that market/good.
- Exclude countries that have no stock and no relevant monthly added/requested signal before relation/scoring work.
- Preserve the all-country `modeu5_countries_present_in_market` scan as a fallback/debug path.
- Invalidate or repair sparse lists when stock is added, removed, transferred, decayed, cleared, initialized, reconciled, or when market/country presence changes.
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
- whether a market-level fallback mutation was used.

Same-market consumption must be labelled as non-trade. Inter-market transfer must show source, target, target capacity policy, actual transferred quantity, and unsatisfied transfer quantity.

## Implementation outline

### Phase 1 — specification and CMM plumbing

- Add parser-safe helpers for reading the `nve_no_void_economy_main` CMM setting.
- Define temporary flags:
  - `modeu5_nve_main_mode`
  - `modeu5_performance_mode_enabled`
  - `modeu5_detailed_country_market_accounting_enabled`
  - `modeu5_market_level_fallback_required`
- Add debug capture for the resolved mode and accounting decision.
- Update localization/tooltips so Performance Mode explicitly says it tracks human-relevant market detail only.

Implementation note for the first stacked PR:

- `modeu5_refresh_nve_main_mode_from_cmm_country_scope` derives script-safe
  `performance`, `normal`, and `deactivated` runtime flags from CMM.
- Performance Mode refresh rebuilds `modeu5_performance_relevant_markets` from
  human countries with `every_market_present_in_country`.
- The rebuild is monthly-stamped so `monthly_country_pulse` does not rebuild the
  global human-relevant list once per country.
- `modeu5_prepare_country_market_accounting_decision` can promote a
  human-present market to detailed on demand when it was not yet in the list.
- CORE-03 owner-change and new-country finalizer hooks opportunistically mark
  new human-relevant markets without waiting for the next monthly rebuild.
- `modeu5_prepare_country_market_accounting_decision` computes the read-only
  country-market decision for the next fallback PR.
- `event modeu5_perf14_debug.1` validates CMM values `1/2/3`, the rebuilt
  human-relevant market list, the non-detailed -> detailed promotion edge case,
  and the positive human market-presence Performance Mode decision.
- The first stacked PR deliberately does not mutate stock, implement
  market-level fallback, or prove the foreign-building-only negative case.

### Phase 2 — accounting gate and fallback operators

- Introduce a shared accounting gate effect used before country x market map writes.
- Add market-level-only variants or branches for systems that change stock while detailed accounting is disabled.
- Ensure market aggregate deltas remain consistent with centralized stock mutation semantics.
- Add audit logs for fallback usage.

### Phase 3 — sparse supplier lists

- Add per-good sparse supplier list generation and maintenance.
- Update US-10 candidate scanning to prefer sparse supplier lists.
- Keep all-country market scan behind fallback/debug mode.
- Validate cache repair/invalidation against stock consistency checks.

### Phase 4 — #37 debug visibility

- Add debug event/log output for last stock resolution and candidate/exclusion traces.
- Add human-readable localization for exclusion reason IDs.
- Ensure consumption and inter-market transfer displays differ clearly.
- Add Performance Mode fallback markers to the same diagnostics.

## Acceptance criteria

- Performance Mode only maintains detailed Market x Country accounting for human countries in markets returned by `every_market_present_in_country`.
- Foreign-building-only or indirect market presence remains a Phase 2 boundary question unless it is covered by the confirmed iterator.
- In Performance Mode, skipped country x market mutations fall back to market-level aggregate changes rather than being dropped.
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
./tools/audit_modeu5_persistent_state.sh
./tools/normalize_cmm_value_links.sh --check
python3 ./tools/validate_cmm_configuration.py
git diff --check
```

Runtime/debug:

```txt
event modeu5_us10_debug.1
event modeu5_revalidate_debug.1
./tools/summarize_modeu5_test_logs.sh
```

New targeted scenarios:

- Performance Mode human country owns a location in the market: detailed country x market accounting is retained.
- Performance Mode human country has only foreign-building/indirect presence: detailed accounting is skipped and market aggregate fallback is used.
- Performance Mode AI country: detailed accounting is skipped and market aggregate fallback is used where a supported mutation applies.
- Normal Mode: existing detailed accounting path remains available.
- Sparse supplier cache: only meaningful suppliers are scanned in the hot path.
- Debug fallback: all-country scan can still be forced for diagnostics.
- US-10-UI: candidate order, exclusion reason, and mutation quantity are visible for consumption and transfer.

## Open design questions

- Whether sparse supplier cache entries should be keyed by market x good only, or market x good x accounting-mode.
- Whether market-level-only fallback should be implemented as new central operators or as explicit branches inside existing central operators.
- How much of US-17 / US-20 should be implemented in this master PR versus reserved for child PRs after the fallback contract exists.
- Whether Performance Mode should track all human-relevant markets for every human country in multiplayer, or only the current player country in single-player contexts.

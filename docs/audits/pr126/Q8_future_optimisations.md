# Q8 — Future optimisation findings after Q4.1 / PR7.1

## Purpose

This file records optimisation findings that should not be mixed into PR146 unless they become necessary for correctness.

PR146 / Q4.1 / PR7.1 is allowed to change the generated runtime handoff so that:

```txt
promoted market
  -> rebuild countries_present_in_market once
  -> every present country:
       refresh capacity
       run US-00 guarded active-good dispatch
  -> every present country:
       run US-10 guarded pending-request dispatch
```

The items below are follow-up candidates for a later stable branch or dedicated optimisation PR. They should remain separate from PR146 runtime validation unless a blocker proves otherwise.

## F1 — Avoid repeated country capacity-pool calculation inside promoted markets

### Finding

`modeu5_prepare_promoted_country_market_capacity` refreshes a selected country-market capacity record from the country capacity pool and the selected market's trade-capacity contribution.

The current promoted-market path calls this helper once per present country in the promoted market. The helper recalculates the country storage capacity pool before applying it to the current market. That keeps correctness local, but it can repeat country-wide preparation work when the same country appears in multiple promoted markets during the same monthly cycle.

### Target optimisation

Introduce a monthly country capacity-pool stamp:

```txt
for current country / present country:
  if capacity pool stamp != current month:
    calculate country storage capacity pool once
    persist or snapshot the reusable country-pool facts

for each promoted country-market:
  reuse the stamped pool facts
  refresh only the market-specific trade-capacity contribution
  store the country-market capacity record
```

### Guardrails

- Do not rebuild the owned-location pool in the monthly hot path unless a lifecycle hook marked it dirty.
- Do not reuse a pool across countries.
- Do not skip the market-specific trade-capacity contribution; only the country-wide pool should be reused.
- Keep capacity refresh before US-00 for the selected country-market.

### Exit criterion

A future PR can prove that the same country capacity pool is calculated at most once per monthly cycle while country-market capacity records are still refreshed for each detailed promoted market.

## F2 — Verify US-10 aggregate pending-request gating before adding another gate

### Finding

PR7.1 adds a per-good pending-request guard before the heavy US-10 resolver. A proposed additional optimisation would be to skip the whole generated US-10 pending-good dispatcher when the country has no pending same-market request for the current market.

However, the existing US-10 implementation may already perform practical bucket sorting in sub-loops before requests reach the per-good resolver. If that bucket sorting already prevents no-request country-market pairs from entering the hot path, adding another aggregate gate may duplicate existing scheduling logic.

### Target verification

Before implementing a new aggregate gate, trace the current US-10 request-bucket flow:

```txt
same-market request creation
  -> bucket / pending-request map write
  -> country + market + good pending request surface
  -> generated PR7.1 per-good guard
  -> heavy resolver only for pending requests
```

### Guardrails

- Do not add a second scheduler until the bucket-sorting path is confirmed insufficient.
- Preserve the existing rule: sparse supplier lists narrow candidate countries after a good/request is selected; they are not the market-good scheduler.
- Preserve the Q5 order: all present-country US-00 work must finish before any US-10 same-market request scans stock.

### Exit criterion

A future audit or probe should classify one of these states:

```txt
A. Already implemented:
   bucket sorting ensures no-request country-market pairs do not enter US-10 generated dispatch;
   no new aggregate gate needed.

B. Partially implemented:
   bucket sorting narrows some work, but no-request country-market pairs still enter generated dispatch;
   add a cheap country-market has-any-pending-request gate.

C. Not implemented:
   generated dispatch remains the first meaningful request gate;
   add aggregate gating before per-good generated dispatch.
```

## F3 — Remove or gate PR7.1 profiling counters on stable main

### Finding

PR7.1 counters are useful during validation because they separate generated guards considered from meaningful work processed.

They are not intended to become permanent hot-path cost in stable gameplay.

### Target optimisation

After runtime validation, either remove the PR7.1 temporary counters from stable main or wrap them behind a debug/profile gate:

```txt
if ModeU5 profiling/debug metrics enabled:
  increment considered / processed counters
else:
  run guarded dispatch without metric writes
```

### Guardrails

- Keep counters until PR146 runtime validation is complete.
- Do not remove business-result counters that are needed for gameplay correctness.
- Do not let metrics influence business logic.

### Exit criterion

Stable main has no unconditional per-good debug counter writes in the monthly hot path.

## F4 — Split legacy guarded helpers from heavy helper bodies

### Finding

PR7.1 adds a generated guard before calling the existing heavy per-good helpers. The existing helpers may still carry their original inner business gates. That is safe, but processed goods may pay for two guard layers:

```txt
PR7.1 generated wrapper guard
  -> existing per-good helper guard
      -> actual business work
```

### Target optimisation

Keep the public legacy helper as a safe guarded entry point, but extract a body helper that assumes the PR7.1 guard has already passed:

```txt
modeu5_process_us00_monthly_market_good_wheat
  -> legacy guarded entry

modeu5_process_us00_monthly_market_good_wheat_body
  -> heavy body; assumes production / previous-state gate already passed

modeu5_pr71_process_us00_monthly_market_good_wheat
  -> PR7.1 guard
  -> body helper
```

The same pattern may apply to US-10 if the existing resolver repeats the pending-request gate.

### Guardrails

- Do not remove the legacy guarded public helper until all callers are identified.
- Do not call the body helper from any surface that has not already proven the required business gate.
- Generate body helpers from the canonical goods registry and template system; do not create a private goods list.

### Exit criterion

Runtime validation shows equivalent economic results with fewer repeated guard checks on processed goods.

## F5 — Reuse `countries_present_in_market` with a market dirty/stamp policy

### Finding

PR146 correctly rebuilds `countries_present_in_market` once per detailed promoted market. That is the right local invariant for Q4.1 / PR7.1.

A later optimisation can avoid rebuilding the same market-country cache when market composition has not changed.

### Target optimisation

Introduce a market cache stamp or dirty flag:

```txt
if market country cache dirty or stamp != current month:
  rebuild countries_present_in_market
else:
  reuse stamped market-country cache for the current monthly cycle
```

### Guardrails

- Treat `countries_present_in_market` as a work cache, never as stock source of truth.
- Dirty the cache when market membership, location ownership, or market links change.
- Do not reuse a cache across markets.
- Do not let cache reuse hide ownership changes after conquest, colonisation, market split, or market merge events.

### Exit criterion

A future PR proves that unchanged markets avoid repeated location scans while changed markets still rebuild before stock-affecting work.

## F6 — Preserve the two-pass US-00 then US-10 order

### Finding

Merging US-10 into the fused capacity + US-00 pass would reduce one country-present loop but would break the Q5 ordering invariant.

The invariant remains:

```txt
all present countries' US-00 production/admission facts are updated
before any same-market US-10 consumption request scans market stock
```

### Decision

Do not optimise by fusing US-10 into the US-00 pass. US-10 may be further gated or bucket-sorted, but it must remain a second pass after all present-country US-00 work.

## F7 — Replace market-center ownership workaround with a native global market pass

### Finding

PR144 / PR146 currently routes market-local work through a country pulse and uses `every_market_center_in_country` as a deterministic market-owner selector:

```txt
monthly_country_pulse(country)
  -> modeu5_run_monthly_stock_cycle
      -> modeu5_run_monthly_promoted_market_local_cycle
          -> every_market_center_in_country
              -> run market-local work for markets whose center is owned by this country
```

This is valid as an ownership workaround because it avoids running the same promoted-market local branch once for every country present in the market. The branch is not logically country-owned; it is market-owned, but the country-scoped market-center iterator is used to select a single deterministic owner.

The EU5 scope table gives a cleaner future option:

```txt
every_market_center_in_country : country -> market
every_market_in_world          : none    -> market
```

If `every_market_in_world` can be triggered once per monthly cycle from a true `none` / global scope, it is a better owner for market-local work than `every_market_center_in_country`.

### Why this matters

The current model is efficient only if the ownership convention stays perfectly true:

```txt
for each country pulse:
  process only markets whose center is owned by this country
```

This gives an effective cost close to:

```txt
C country pulses
+ M_d detailed/promoted markets processed once through their market-center owner
+ country-owned trade / other country work
```

But the safety property is conventional rather than structural. A future change that accidentally weakens the market-center gate can turn the cost into the dangerous shape:

```txt
for each country pulse:
  scan or process many markets
    -> rebuild countries_present_in_market
    -> loop present countries
    -> loop generated goods
```

The pathological cost shape is:

```txt
C countries
  * M markets
  * P_m present countries per market
  * G generated goods considered
```

Even if PR7.1 prevents most heavy per-good work, the outer orchestration error would still be expensive because it would repeat market scans, cache rebuilds, country-present loops, guard checks, and metrics.

A true global market pass makes the ownership contract structural:

```txt
for each market in world once:
  if detailed/promoted/human-relevant:
    run market-local work
```

The target cost shape becomes:

```txt
M_d detailed/promoted markets
  * P_m present countries per market
  * G_guarded generated goods considered
+
C countries
  * country-owned work
```

That is easier to reason about, easier to document, and less exposed to accidental country-pulse duplication.

### Target architecture

The long-term PR126 architecture should be split into explicit sequential passes:

```txt
monthly orchestration
  -> country preparation pass
  -> global market-local pass
  -> country trade-owner pass
  -> validation / reconciliation pass
```

Detailed target shape:

```txt
1. Country preparation pass
   for each country:
     runtime readiness / participation checks
     prepare performance markers needed by country-owned work
     prepare or refresh country capacity pool
     prepare country-level request/input state
     do not run market-local stock mutation here

2. Global market-local pass
   every_market_in_world:
     limit to detailed/promoted/human-relevant markets
     save current market scopes
     mark market processed for diagnostics only, not ownership gating
     prepare market runtime accounting mode

     if detailed:
       rebuild or reuse countries_present_in_market

       for each country present in market:
         refresh country-market capacity from prepared/stamped country pool
         run US-00 active-good guarded dispatch

       for each country present in market:
         run US-10 pending-request guarded dispatch

     if vanilla fallback:
       record fallback only; no ModeU5 stock mutation

     if blocked:
       record blocked only

3. Country trade-owner pass
   for each country:
     run confirmed country-scope every_trade ownership pass
     process only inter-market trade
     delegate stock consequences to central stock operators

4. Validation / reconciliation pass
   run scoped audit validation after the month-local mutation sequence
   do not rely on reconciliation to hide earlier orchestration duplication
```

### Why this is maintainability-positive

The current market-center version requires future contributors to understand this implicit sentence:

```txt
This code is inside a country pulse, but it is not country-owned work; the country is only a deterministic owner proxy for the market center.
```

That is easy to forget during future refactors. It creates two recurring risks:

```txt
1. A contributor adds country-level logic inside the market-local branch because the branch is nested under country pulse.
2. A contributor adds market-local work elsewhere because the market-local branch does not look globally owned.
```

The global market-pass version encodes the domain boundary directly:

```txt
market-local stock work lives under market scope
country-local work lives under country scope
trade-owner work lives under confirmed country-scope trade iteration
```

That improves readability, reduces the need for explanatory caches/registries, and makes review questions simpler:

```txt
Is this operation market-local? Put it in the global market pass.
Is this operation country-local? Put it in the country pass.
Is this operation trade-owned? Put it in the country trade-owner pass.
```

### Which caches may be removed or simplified

A global market pass should allow a later PR to simplify or remove caches whose only purpose is to compensate for country-pulse ownership ambiguity.

Potentially simplified:

```txt
modeu5_prepare_monthly_market_seen_registry
modeu5_mark_monthly_market_seen
market-center local-branch owner/seen diagnostics
anti-duplicate local-market processing guards
some PR144 dispatcher comparison counters tied to ownership proof
```

These may remain useful as diagnostics during migration, but they should no longer be required as correctness gates once the native global market pass owns market-local work.

Not automatically removed:

```txt
countries_present_in_market
country-market capacity records
country stock source maps
market stock/cache maps
pending request maps
active-good / pending-good generated literal call surfaces
```

`countries_present_in_market` probably still exists unless a native market -> present countries iterator is confirmed. The global market pass removes the market ownership workaround; it does not automatically provide a country-participant list for each market.

### Interaction with F1 capacity-pool reuse

F7 and F1 are compatible.

In fact, the global market pass makes F1 more important, because a country can appear in multiple detailed markets during the same monthly global market pass. The correct target is:

```txt
country preparation pass:
  prepare/stamp country-wide capacity pool once per country/month

global market pass:
  for each present country in selected market:
    load prepared country-wide pool facts
    apply only the selected market's trade-capacity contribution
    store country-market capacity record
```

This preserves the requirement that US-00 sees a fresh country-market capacity record while avoiding repeated country-wide pool scans.

### Interaction with F2 US-10 bucket sorting

F7 does not replace F2.

The global market pass changes the outer owner of market-local work. US-10 bucket sorting is an inner scheduling question:

```txt
global market pass
  -> market
      -> present country
          -> generated goods / pending requests
```

If the existing US-10 buckets already prevent no-request country-market pairs from entering generated dispatch, no additional aggregate gate is needed. If no-request country-market pairs still enter generated dispatch, add a cheap country-market `has_any_pending_request` gate before the per-good generated surface.

### Interaction with F5 `countries_present_in_market` reuse

F7 and F5 are compatible, but F7 should come first.

The global market pass gives the cache a natural owner:

```txt
market scope owns countries_present_in_market work cache
```

A later F5 PR can then add:

```txt
market country-cache stamp
market country-cache dirty flag
market participant-cache rebuild reason
```

without mixing those concerns with country-pulse ownership.

### Ordering risks

The main risk is monthly pass ordering. The market-local pass should not run before the inputs it consumes exist.

Likely safe order:

```txt
1. Country preparation pass
   - readiness / participation state
   - country capacity pool facts
   - country-level input/request preparation if required

2. Global market-local pass
   - market runtime mode
   - countries_present_in_market
   - country-market capacity records
   - US-00 active-good dispatch
   - US-10 pending-request dispatch

3. Country trade-owner pass
   - every_trade in confirmed country scope
   - inter-market stock consequences

4. Validation / reconciliation
```

Potential alternative if trade creates requests consumed by US-10:

```txt
1. Country preparation pass
2. Country trade-owner request-building pass
3. Global market-local US-00 pass
4. Global market-local US-10 pass
5. Trade settlement / transfer pass if needed
6. Validation / reconciliation
```

The future implementation must first classify whether `every_trade` produces stock mutations immediately, request objects for later market-local consumption, or both. Do not move trade relative to US-00 / US-10 blindly.

### Migration strategy

Do not rewrite the whole monthly cycle in one unmeasured commit.

Recommended stack:

```txt
F7.0 Documentation only
  - record the target architecture in Q8
  - keep PR146 runtime unchanged

F7.1 No-op global market iterator probe
  - add a debug-only effect using every_market_in_world
  - count world markets, detailed markets, fallback markets, blocked markets
  - prove it runs once per intended monthly cycle
  - prove it does not run once per country

F7.2 Shadow comparison pass
  - keep existing market-center branch as live path
  - add optional debug-only global market pass that records which markets it would process
  - compare market sets:
      market-center-owned set == global detailed/promoted set
  - log mismatches: missing, extra, duplicate, fallback, blocked
  - current #159 increment: Normal Mode market-universe comparison only; no stock mutation, no US-00/US-10, no live switch

F7.3 Switch market-local ownership
  - move live market-local branch to every_market_in_world
  - keep market-center path disabled or debug-only for one PR
  - retain diagnostic market-seen counters only as safety proof

F7.4 Delete ownership workaround
  - remove market-center local-branch ownership guard
  - remove duplicate-prevention caches that are no longer needed
  - keep only diagnostics that still provide value

F7.5 Optimise under the new architecture
  - implement F1 country capacity-pool stamping
  - decide F2 after bucket-sorting audit
  - decide F5 market participant-cache reuse
```

### Validation proof required

A future F7 PR should include explicit runtime proof, not only static reasoning.

Minimum metrics:

```txt
global_market_pass_runs_per_month = 1
world_markets_considered = expected market count
detailed_markets_processed = expected detailed/promoted count
fallback_markets_recorded = expected fallback count
blocked_markets_recorded = expected blocked count
market_center_shadow_missing = 0
market_center_shadow_extra = 0
market_center_shadow_duplicates = 0
```

For economic equivalence:

```txt
Before F7 switch:
  controlled market stock before / after monthly cycle
  controlled country stock before / after monthly cycle
  US-00 processed goods
  US-10 processed requests
  trade-owner processed trades

After F7 switch:
  same values in controlled fixture
```

For performance equivalence/improvement:

```txt
old market-center live branch:
  country pulses entered
  market-center iterations
  detailed markets processed
  countries_present_in_market rebuilds
  present-country iterations
  generated goods considered
  heavy goods processed

new global market live branch:
  global market pass entries
  world market iterations
  detailed markets processed
  countries_present_in_market rebuilds
  present-country iterations
  generated goods considered
  heavy goods processed
```

Expected result:

```txt
detailed markets processed: equal
heavy goods processed: equal
country-pulse market-owner dependency: removed
market ownership duplicate guards: reduced or removed
```

### Guardrails

- Do not call `every_market_in_world` from inside `monthly_country_pulse`; that would create the worst `C * M` shape.
- Do not move country-owned trade work into market scope unless the engine has a confirmed market-scope trade iterator.
- Do not delete `countries_present_in_market` until a native market -> country participant iterator is confirmed.
- Do not let global market pass process fallback/blocked markets as partial ModeU5 markets.
- Do not run US-10 before all relevant US-00 production/admission facts for the market are updated.
- Do not use the global market pass to bypass central stock operators.
- Keep generated per-good helpers based on the canonical goods registry; do not introduce dynamic runtime-built helper names.
- Keep the shadow comparison until runtime logs prove that the global market set matches the old market-center-owned set.

### Decision

F7 is likely a better long-term architecture than the market-center-in-country ownership workaround, provided `every_market_in_world` can be run once from true global / none scope in the monthly lifecycle.

It should not be merged into PR146, because PR146 already changes live generated dispatch behavior and still needs EU5 runtime validation. F7 should be its own stacked refactor after PR146, with a no-op probe first.

### Exit criterion

A future PR can replace the live market-center-owned local branch with a native global market pass when all of the following are true:

```txt
1. every_market_in_world is proven to run once per intended monthly cycle, not once per country.
2. The global market set matches the market-center-owned detailed/promoted market set.
3. Controlled economic fixtures produce equivalent stock, request, and trade results.
4. Ownership/duplicate-prevention caches are reduced without losing diagnostics.
5. Runtime metrics show no increase in market-local branch entries, present-country loops, or heavy generated-good processing.
```

## F8 — Optimisation sequencing when F7 is likely

### Finding

If F7 becomes the next major architecture target, some local performance improvements are still worth doing, while others should wait.

The key question is whether an optimisation survives the future ownership model.

### Worth doing before or alongside F7

These improvements are compatible with both the current market-center workaround and the future global market pass:

```txt
PR146 runtime validation
PR7.1 metric interpretation and cleanup plan
F3 profile counter removal/gating for stable main once validation is done
F1 country capacity-pool stamping, if implemented as a country-owned monthly prep contract
instrumentation that measures loop entries and heavy helper entries
small documentation/checklist fixes that prevent future ownership mistakes
```

These reduce risk and remain useful under both architectures.

### Usually not worth doing before F7

Avoid spending too much time optimising structures that F7 may delete or simplify:

```txt
market-center owner guard micro-optimisations
monthly market-seen registry tuning
anti-duplicate caches whose only purpose is country-pulse market ownership
complex improvements to the current nested diagram shape
large refactors inside modeu5_run_monthly_promoted_market_local_cycle before the owner is settled
```

Those may become throwaway work if the global market pass replaces the market-center branch.

### Conditional work

Some items should be investigated but not implemented blindly:

```txt
F2 US-10 aggregate pending-request gate:
  audit bucket sorting first; implement only if no-request country-market pairs still enter dispatch

F4 body-helper extraction:
  useful if profiling shows repeated inner guards matter after PR7.1/F7

F5 countries_present_in_market dirty/stamp cache:
  likely useful, but easier and cleaner after F7 gives the cache a market-scope owner
```

### Decision rule

Use this decision rule for further performance PRs:

```txt
If the optimisation reduces hot-path work and remains valid after F7:
  it is a good candidate now.

If the optimisation only improves the market-center ownership workaround:
  defer until F7 is accepted or rejected.

If the optimisation changes business ordering:
  do not implement until a runtime probe proves equivalence.
```

### Recommended next sequence

```txt
1. Finish PR146 validation.
2. Gate/remove PR7.1 profiling counters for stable main once validation is done.
3. Create F7.1 no-op every_market_in_world probe.
4. If F7.1 proves true global once-per-month execution, prioritise F7 over deeper nested-branch optimisation.
5. After F7 ownership is settled, implement F1/F2/F5 under the final architecture.
```

After #159, step 3/4 should be read as partially advanced:

```txt
- F7.1/F7.2 proof track now has a Normal Mode market-universe shadow comparison.
- The next proof is still performance-mode / human-relevant market equivalence.
- Live runtime remains unchanged until both the ownership and economic equivalence proofs pass.
```

## Priority order

| Priority | Finding | Recommended handling |
|---|---|---|
| P0 | F7 native global market pass | Architecture spike/probe first; likely better long-term owner for market-local work |
| P1 | F1 capacity-pool reuse | Strong next optimisation candidate; implement as country-owned prep so it survives F7 |
| P1 | F2 US-10 bucket-sorting verification | Audit/probe first; do not duplicate scheduler blindly |
| P1 | F3 profile counter removal/gating | Stable-main cleanup after validation |
| P1 | F8 optimisation sequencing | Avoid throwaway optimisation of the market-center workaround if F7 is likely |
| P2 | F4 helper body extraction | Later generated-helper refactor once callers are known |
| P2 | F5 market-country cache dirty/stamp | Later cache-lifecycle PR, preferably after F7 |
| Guardrail | F6 keep US-10 second pass | Do not implement as optimisation |

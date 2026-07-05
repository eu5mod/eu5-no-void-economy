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

## Priority order

| Priority | Finding | Recommended handling |
|---|---|---|
| P1 | F1 capacity-pool reuse | Strong next optimisation candidate after PR146 runtime validation |
| P1 | F2 US-10 bucket-sorting verification | Audit/probe first; do not duplicate scheduler blindly |
| P1 | F3 profile counter removal/gating | Stable-main cleanup after validation |
| P2 | F4 helper body extraction | Later generated-helper refactor once callers are known |
| P2 | F5 market-country cache dirty/stamp | Later cache-lifecycle PR |
| Guardrail | F6 keep US-10 second pass | Do not implement as optimisation |

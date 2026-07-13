# Q8.7 — Performance market-owner work-shape shadow proof

## Status

Implemented in PR #160 as a test-package proof only.

```txt
event cbp_q8_probe_debug.9
```

Scenario marker:

```txt
q87_performance_market_owner_workshape_shadow
```

## Purpose

This is the next Q8.7/F7 step after the Performance Mode relevant-market global shadow comparison.

The previous proof showed that:

```txt
cbp_performance_relevant_markets
  == every_market_in_world filtered to cbp_performance_relevant_markets
```

This proof compares the current live owner shape against the candidate owner shape at the work-shape level:

```txt
current owner shape:
  every_country
    -> every_market_center_in_country
       -> filter market in cbp_performance_relevant_markets
       -> rebuild countries_present_in_market
       -> count present-country passes

candidate Q8.7 owner shape:
  every_market_in_world
    -> filter market in cbp_performance_relevant_markets
    -> rebuild countries_present_in_market
    -> count present-country passes
```

## What is compared

The probe compares:

```txt
- current owner market set vs candidate global market set;
- duplicate / missing / extra market counters;
- current owner cache rebuild count vs candidate cache rebuild count;
- current owner present-country pass count vs candidate present-country pass count;
- human and AI present-country diagnostic counts.
```

## Non-goals / guardrails

```txt
- No live dispatcher replacement.
- No generated-good loop.
- No US-00 execution.
- No US-10 execution.
- No country trade-owner pass.
- No validation/reconciliation pass.
- No stock mutation.
- No every_trade from market scope.
```

## Spec boundary

This proof preserves the clarified Performance Mode boundary:

```txt
human-relevant market
not human-country-only
```

Once the market is relevant, the future market-local pass must cover all countries present in that market, including AI countries. This is why the probe counts present-country passes and exposes human/AI diagnostics, rather than filtering country passes to human countries only.

## Pass meaning

A pass means:

```txt
For Performance Mode relevant markets, a candidate global market-local owner pass can cover the same market set and present-country work surface as the current market-center owner workaround, without invoking mutating economic work.
```

A pass still does not authorise a live dispatcher switch. The next step after this proof should be a guarded live pilot or a deeper no-op ordering proof that mirrors US-00-before-US-10 ordering per market without calling the generated mutating helpers.

## Expected validation

Runtime:

```txt
event cbp_q8_probe_debug.9
```

Expected log markers:

```txt
ModeU5 TEST ENTERED scenario=q87_performance_market_owner_workshape_shadow
ModeU5 Q8.7 WORKSHAPE_SHADOW current_markets=... global_markets=... current_country_passes=... global_country_passes=... mode=performance no_stock_mutation=1 no_us00=1 no_us10=1 no_trade_owner=1
ModeU5 TEST PASS scenario=q87_performance_market_owner_workshape_shadow
```

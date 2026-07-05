# PR7.1 — Active-good root-cause summary

This file is a short pointer for reviewers. The full analysis lives in:

```txt
docs/audits/pr126/Q5.2_active_good_root_cause.md
```

## Summary

The unexpectedly high monthly-good counters observed during PR7 validation do not mean EU5 has more goods than expected.

They mean the current PR7 dispatcher still invokes generated all-good helper surfaces once per country-present pass:

```txt
countries-present in detailed market
  x generated goods
  x US phase
```

This all-good generated dispatch shape already exists on `main`. PR7 changes ownership and live flow, but it does not yet introduce an active / relevant-good pre-dispatch scheduler.

## Root cause

```txt
Main already has:
  generated all-good US-00 / US-10 helper dispatch
  inner per-good early exits / business gates

PR7 preserves:
  the generated all-good helper dispatch
  inside the promoted-market local branch

PR7 does not yet implement:
  active-good scheduling before helper invocation
```

## Business rules to preserve

US-00 should only do full business work when:

```txt
produced_in_market:<good> > 0
OR previous ModeU5 US-00 record / active state exists
```

US-10 should only resolve stock when:

```txt
pending same-market consumption request exists for country + market + good
```

Sparse supplier lists remain a supplier-country narrowing mechanism after a US-10 good/request is selected; they are not the market-good scheduler.

## PR7.1 safe target

The safe first stacked PR is instrumentation and documentation:

```txt
- document that PR7 is an ownership switch, not the active-good optimization;
- split counters between generated helper calls and meaningful business work;
- avoid claiming the Q4 `G_a` performance target until active-good scheduling lands;
- keep runtime behavior unchanged except debug/audit counters.
```

A later/full implementation may replace or guard all-good helper invocation with a safe active-good scheduler, but that requires EU5 runtime validation.

# Observability Counter Gating

## Status

Implemented in the PR stacked directly on #212.

This is Layer A from
[`FULL_RUNTIME_PERFORMANCE_ANALYSIS.md`](FULL_RUNTIME_PERFORMANCE_ANALYSIS.md):
normal runtime no longer writes the selected hot-path profiling counters, while
debug and audit runtime retain the same observability surfaces.

## Shared gate

```txt
cbp_observability_enabled_trigger
  = cbp_debug_capture_enabled_trigger
    OR cbp_audit_enabled_trigger
```

`cbp_pr71_metrics_enabled_trigger` now delegates to the shared gate so existing
PR7.1 generated metrics and the newly gated families use one policy.

## Gated families

The implementation gates resets, increments, accumulated quantities, and related
debug logs for:

- Q8.7 global market-owner metrics;
- promoted-market shell, local-branch, and live-dispatcher metrics;
- market-to-country cache scan/rebuild metrics;
- country trade-owner metrics;
- Performance Mode human/relevant-market discovery counters;
- Vanilla fallback and blocked-market counters.

The gate encloses generated-good count capture where that capture exists only to
feed a profiling counter.

## State deliberately left unconditional

The following are not observability and remain active in every runtime mode:

- Q8.7 global month stamp and owner switch;
- relevant, promoted, dirty, monthly-seen, and countries-present work lists;
- Performance Mode market-accounting decisions;
- market promotion result/failure state used by mutation admission;
- country and country-market capacity calculations;
- trade scope and `trade_volume` capture;
- US-17 and US-20 calculations;
- US-00 and US-10 generated dispatch;
- US-04 reconciliation;
- all central stock operators and consistency gates.

PERF-13 active-repair counters are unchanged because their callers are already
restricted to debug/test repair surfaces rather than the normal monthly path.

The monthly market-seen registry remains active because it also owns the monthly
registry/list lifecycle and US-10 runtime-counter reset. This PR does not attempt
to split that coupled responsibility.

## Expected work-shape change

Normal runtime still evaluates the lightweight observability trigger at the
metric effect boundary, but avoids the associated global-variable remove, set,
and accumulation writes. Debug/audit runtime retains counters for deterministic
proof and profiling.

This PR does not claim a measured wall-clock improvement. The benchmark matrix
and economic-equivalence record remain defined in the full performance analysis.

## Static validation

`tools/validate_cbp_observability_gates.py` checks that:

- the shared gate contains both debug and audit paths;
- selected metric effects contain the shared gate;
- market and country work lists remain present;
- Q8.7 retains its global month stamp and world-market owner;
- the live market branch retains two country passes with US-00 before US-10;
- `every_trade`, US-17, and US-20 remain in the country-owned pass;
- market-promotion business state remains outside the observability policy.

The validator runs through the `Observability Gates` GitHub Actions workflow.

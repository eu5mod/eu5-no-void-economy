# Observability Counter Gating

## Status

Implemented in the PR stacked directly on #212.

This is Layer A from
[`FULL_RUNTIME_PERFORMANCE_ANALYSIS.md`](FULL_RUNTIME_PERFORMANCE_ANALYSIS.md):
normal runtime no longer writes the selected hot-path profiling counters, while
debug and audit runtime retain the same observability surfaces.

The same PR also corrects the native trade-rework option boundary discovered
while reviewing the country trade-owner hot path. The detailed decision is
recorded in [`TRADE_REWORK_GATE_CORRECTION.md`](TRADE_REWORK_GATE_CORRECTION.md).

## Shared observability gate

```txt
cbp_observability_enabled_trigger
  = cbp_debug_capture_enabled_trigger
    OR cbp_audit_enabled_trigger
```

`cbp_pr71_metrics_enabled_trigger` now delegates to the shared gate so existing
PR7.1 generated metrics and the newly gated families use one policy.

## Gated counter families

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

## Trade-rework gate correction

The CMM trade-rework option now owns the complete native US-17/US-20 cycle:

```txt
trade rework enabled
  -> refresh US-17 country modifier state
  -> every_trade
     -> capture owner / markets / good / trade_volume
     -> US-17 route compatibility surface
     -> US-20 goods reconciliation

trade rework disabled
  -> clear persisted US-17/US-20 country state
  -> skip every_trade
```

Previously, US-17 country refresh was internally gated and the route-level US-17
wrapper returned a zero money delta, but the outer monthly call and native trade
iterator still executed. The corrected boundary is both clearer and cheaper.

Explicit ModeU5-owned inter-market transfer requests remain independent of this
CMM option because they are not native trade-rework processing.

## State deliberately left unconditional

The following are not observability and remain active in every runtime mode:

- Q8.7 global month stamp and owner switch;
- relevant, promoted, dirty, monthly-seen, and countries-present work lists;
- Performance Mode market-accounting decisions;
- market promotion result/failure state used by mutation admission;
- country and country-market capacity calculations;
- US-00 and US-10 generated dispatch;
- US-04 reconciliation;
- all central stock operators and consistency gates.

US-17/US-20 calculations and native `every_trade` are business state, but they
now run only inside their own CMM trade-rework gate rather than unconditionally.

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

When trade rework is disabled, the monthly country pass also avoids the complete
native `every_trade` traversal and all associated US-17/US-20 route preparation.

This PR does not claim a measured wall-clock improvement. The benchmark matrix
and economic-equivalence record remain defined in the full performance analysis.

## Static validation

`tools/validate_cbp_observability_gates.py` checks that:

- the shared observability gate contains both debug and audit paths;
- selected metric effects contain the shared gate;
- market and country work lists remain present;
- Q8.7 retains its global month stamp and world-market owner;
- the live market branch retains two country passes with US-00 before US-10;
- market-promotion business state remains outside the observability policy.

`tools/validate_cbp_trade_rework_gate.py` additionally checks that:

- one authoritative CMM gate contains refresh, `every_trade`, US-17 and US-20;
- the order remains refresh -> iterator -> US-17 -> US-20;
- no native trade iterator or US-17/US-20 call exists outside that gate;
- the disabled branch clears persisted country modifier/coefficient state;
- explicit ModeU5 transfer requests remain independent.

Both validators run through the `Observability Gates` GitHub Actions workflow.

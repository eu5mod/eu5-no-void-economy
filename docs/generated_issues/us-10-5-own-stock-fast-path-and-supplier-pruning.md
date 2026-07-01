# US-10.5 — Own-Stock Fast Path And Supplier Pruning

## Summary

Implement the follow-up requested by issue #109 for US-10 demand resolution:

- consume the demanding country's own same-market stock before scanning external suppliers;
- skip the fallback supplier scan when own stock fully satisfies the request, unless the debug full-scan flag is enabled;
- fail closed through a ModeU5 market aggregate prefilter before rebuilding candidate lists;
- prune external suppliers that are below reserve floors or currently stock-negative;
- expose bounded audit diagnostics for candidate buckets, exclusions, and mutation traces.

## Business Rule

For same-market consumption, own stock is always the first candidate. If it fully
satisfies the request, US-10 does not scan other countries unless
`modeu5_us10_debug_force_full_candidate_scan` is enabled for a debug probe.

External suppliers are pruned before expensive relation or score reads when:

- they have no usable stock;
- their stock is below the minimum stock threshold;
- their stock is below `capacity * modeu5_us10_supplier_min_stock_ratio`;
- their monthly ModeU5 net balance is negative and their stock is below
  `capacity * modeu5_us10_supplier_negative_balance_reserve_ratio`.

Own-country consumption is exempt from the supplier reserve floor. The reserve
floor is a supplier-protection rule, not a block on a country's own consumption.

## Implementation Notes

The mutating US-10.1 and US-10.2 wrappers now prepare resolver context without
running the read-only generic candidate scan first. This keeps the fast path a
real fast path and avoids doing the expensive work before the optimization can
decide to skip it.

`is_in_surplus_in_market` is confirmed as a vanilla trigger and recorded in
TECH-01, but the runtime prefilter remains based on the ModeU5 market stock
aggregate because ModeU5 country-market stock is the source of truth. The
vanilla surplus trigger is diagnostic only in this PR.

## Debug Output

When audit mode is enabled, US-10 emits bounded candidate and mutation traces:

```txt
ModeU5 US-10 CANDIDATE TRACE ...
ModeU5 US-10 MUTATION TRACE ...
```

The focused #109 test also dumps:

```txt
ModeU5 US-10 DUMP issue109 fast_path ...
ModeU5 US-10 DUMP issue109 supplier_floor ...
ModeU5 US-10 DUMP issue109 aggregate_prefilter ...
```

## Test Scenario

Run:

```txt
event modeu5_us10_debug.1
```

Choose:

```txt
Run US-10 #109 fast-path/pruning test
```

Expected result:

```txt
ModeU5 TEST PASS scenario=us10_issue109_fast_path_pruning
```

Then run:

```txt
event modeu5_revalidate_debug.1
./tools/summarize_modeu5_test_logs.sh
```

Expected broad result:

```txt
Failed:  0
Missing expected scenarios: 0
```

## Known Limitations

- This PR does not claim exact vanilla trade quantity integration.
- Vanilla `is_in_surplus_in_market` is diagnostic; ModeU5 stock aggregate remains
  the fail-closed runtime prefilter.
- Candidate ordering remains bucketed and deterministic. Full score tie-break
  ordering and richer UI presentation remain follow-up work.

## TECH-01

Adds TECH-01 row 140 for `is_in_surplus_in_market`.

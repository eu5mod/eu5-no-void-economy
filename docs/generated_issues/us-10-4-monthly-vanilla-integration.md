# US-10.4 - Monthly Runtime Integration With ModeU5 Stocks

## Goal

Integrate US-10 demand resolution into the monthly stock cycle without replacing
vanilla markets.

The monthly pass must:

- process explicit country x market x good consumption requests from ModeU5
  stock;
- record requested, satisfied, and unsatisfied quantities through US-10.3;
- keep all stock mutations behind `cbp_remove_stock` or
  `cbp_transfer_stock`;
- detect vanilla market trade activity only as a diagnostic signal until exact
  per-trade quantities are confirmed.

## Runtime Design

The monthly country pulse still fires once per country. Market-owned US-10 work
is scheduled from:

```txt
every_market_center_in_country
```

For each market center reached by the current country, ModeU5 rebuilds the
current-market country work cache:

```txt
cbp_countries_present_in_market
```

Then it processes each country present in that market. Consumption requests are
stored as a current-month input queue:

```txt
cbp_consumption_<good>_pending_requested_by_market[market]
```

When the monthly pass sees a positive queued request, it removes the queue entry
and calls:

```txt
cbp_resolve_stock_consumption = {
  consumer_country = scope:cbp_country
  market = scope:cbp_market
  good = <good>
  requested_quantity = queued_quantity
}
```

This makes consumption draw from ModeU5 country x market x good stock and lets
the existing US-10.3 outcome maps record the result.

## Trade Signal Guard

TECH-01 confirms the market-scope value:

```txt
traded_in_market:<good>
```

But TECH-01 still does not confirm an exact vanilla trade requested or actual
quantity from trade scope. Therefore the monthly pass may count a positive
`traded_in_market:<good>` value as a blocked diagnostic signal, but it must not
move stock from that value.

Inter-market stock transfer remains available only through explicit calls to:

```txt
cbp_resolve_inter_market_stock_transfer
```

## Capacity-To-Quantity Diagnostics

ModeU5 now generates a static transport-cost helper per good from vanilla
`common/goods`:

```txt
cbp_compute_goods_quantity_from_trade_capacity_good_<good>
```

The helper computes:

```txt
cbp_computed_goods_quantity = capacity_volume / static transport_cost
```

This is an estimated conversion from a known capacity-like volume, not an exact
vanilla trade quantity. Missing static `transport_cost` fields use the vanilla
default `1`, and denominators are clamped so the helper cannot divide by zero.

A native trade uses the direct trade-scope value:

```txt
good_quantity = trade_volume
```

Static transport-cost helpers are not part of this path. They are retained for
explicit capacity-like inputs and focused diagnostics.

## Acceptance Criteria

- A monthly queued consumption request is processed once and removed.
- The corresponding country stock decreases through the centralized operator.
- US-10.3 requested/satisfied/unsatisfied outcome maps are updated.
- Monthly runtime counters expose processed requests and blocked trade signals.
- Positive `traded_in_market:<good>` never triggers stock transfer without an
  explicit requested quantity.
- Capacity-to-goods conversion helpers expose `cbp_computed_goods_quantity`
  and are labelled as estimated/diagnostic, never actual vanilla quantity.

## Test Protocol

Run static checks:

```bash
./tools/generate_all.sh
./tools/audit_cbp_persistent_state.sh
./tools/audit_cbp_per_good_loops.sh
./tools/validate_module_packages.sh
git diff --check
```

Run focused in-game validation:

```txt
event cbp_us10_debug.1
```

Choose:

```txt
Run US-10 monthly runtime integration test
```

Expected log lines:

```txt
ModeU5 TEST ENTERED scenario=us10_monthly_runtime_integration
ModeU5 US-10 DUMP monthly_runtime requested=30 satisfied=30 unsatisfied=0 stock_after=20 processed=1
ModeU5 TEST PASS scenario=us10_monthly_runtime_integration
```

Then run:

```txt
event cbp_us10_debug.1
```

Choose:

```txt
Run US-10 trade-capacity conversion test
```

Then run:

```txt
event cbp_us10_debug.1
```

Choose:

```txt
Probe direct trade quantity formula
```

This probe may return `BLOCKED` if no trade scope is iterated. Script errors
from this probe mean TECH-01 138 remains unconfirmed.

Then run:

```txt
event cbp_us10_debug.1
```

Choose:

```txt
Run US-10 demand-resolution test
```

Finally run broad revalidation:

```txt
event cbp_revalidate_debug.1
```

Close EU5 and summarize:

```bash
./tools/summarize_cbp_logs.sh
```

Logs remain the source of truth for PR validation comments.

## Known Limitations

- Live vanilla Pop/Estate requested quantities remain fallback-only.
- Vanilla requested quantity remains separate from the confirmed actual
  `trade_volume` moved quantity.
- `traded_in_market:<good>` is used only as a blocked trade signal.
- The generated transport-cost helper estimates quantity from a known capacity
  volume. It does not prove the exact vanilla trade quantity endpoint.
- Native `trade_volume` is copied directly as the moved-goods quantity; static
  `transport_cost` conversion is limited to explicit capacity-like inputs.
- Location-level Pop integration and US-04 read/reset timing remain follow-up
  work.

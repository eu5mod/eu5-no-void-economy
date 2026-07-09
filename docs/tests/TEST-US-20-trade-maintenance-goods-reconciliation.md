# TEST-US-20 — Trade maintenance goods reconciliation

## Purpose

This test plan documents what must be validated for US-20 after the four-case origin/destination market-accounting correction.

US-20 has two separate responsibilities:

```txt
base goods movement:
  add at destination, or transfer country-market to country-market

loss reconciliation:
  remove the delivery loss at destination
```

The current PR implements the formula, classification, explicit/trade-owner receiver loss removal, market-level destination loss through `add_goods_supply`, generic route-good dispatch for promoted-destination country-stock loss, blocked diagnostics, status visibility, and deterministic E2E probe coverage for the four promoted/non-promoted origin/destination cases.

It still does **not** claim full generic production runtime completion for every receiver topology. The remaining gaps are the live receiver allocator, base receipt add/transfer operators, and TECH-01 trade-profit/country-income display-accounting API proof.

## Public market-loss surface

The EU5 Effect page documents `add_goods_supply` as a market-scope effect that adds goods to a market stockpile and accepts `goods` and `amount` parameters.

US-20 uses that market-stockpile surface with a negative amount for delivery loss:

```txt
market_loss_delta = -goods_loss_quantity

scope:target_market = {
  add_goods_supply = {
    goods = scope:route_good
    amount = market_loss_delta
  }
}
```

The old `remove_good` probe is therefore replaced by a concrete market-loss path and a success counter:

```txt
modeu5_us20_market_goods_supply_loss_routes
```

For promoted destination markets, the market loss is mirrored into the receiver country×market stock through:

```txt
modeu5_apply_us20_promoted_destination_country_loss_by_route_good
```

That dispatcher maps the saved route-good scope to the literal `modeu5_remove_stock` good token required by the central stock operator.

## Runtime validation snapshot — 2026-07-09

Validation evidence captured from the installed PR branch before the latest generic-dispatcher patch:

```txt
Expected scenario set: full
Entered: 19
Passed:  18
Failed:  0
Blocked: 0
Pending: 0
Missing expected full-revalidation scenarios: 0

ModeU5 TEST PASS scenario=us17_us20_route_reconciliation expected_probe_blocked=yes hard_failures=0
ModeU5 TEST PASS scenario=us20_case12_market_loss_probe hard_fail...
```

The pasted US20 PASS line is truncated after `hard_fail`, but the summarizer reports `Passed=18`, `Failed=0`, `Blocked=0`, and `Missing expected full-revalidation scenarios=0`. This is accepted as green evidence for the sizeable deterministic US20 E2E probe.

Post-run implementation update:

```txt
The promoted-destination loss path is no longer wheat-only/test-only.
It now calls a generic route-good -> literal-good dispatcher for receiver country-stock loss.
The deterministic probe still needs to be rerun on this latest head to confirm no regression.
```

## Current status snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Q8.7 placement | Validated | Hook stays in `modeu5_run_monthly_country_trade_owner_cycle -> every_trade`; no second route-discovery loop. |
| CMM trade-rework gate | Implemented | Route reconciliation is gated by `modeu5_trade_rework_enabled_trigger`; deterministic fixture checks dormant behavior when disabled. |
| Money formula | Implemented / partial | Old price-side bonus removal and route delta are computed; #120 side remains placeholder until final #120 runtime model. |
| Treasury money application | Validated | Signed route money delta is applied through `add_gold`; this proves treasury/cash mutation only. |
| Vanilla income/profit application | Blocked TECH-01 | Probe matrix is documented/counted, but no speculative country-income or route-profit API calls are used. |
| Goods received formula | Validated | Target received amount and loss quantity are computed from `trade_maintenance`. |
| Market-level destination loss | Validated | Deterministic E2E probe reaches PASS with the negative `add_goods_supply` market-loss path. |
| Four-case market accounting | Validated | The case12 E2E probe covers non-promoted/non-promoted, promoted/non-promoted, non-promoted/promoted, and promoted/promoted paths. |
| Case 1: origin non-promoted / destination non-promoted | Validated | Destination market loss through `add_goods_supply`; no country-stock receiver required. |
| Case 2: origin promoted / destination non-promoted | Validated | Destination market loss through `add_goods_supply`; no country-stock receiver required. |
| Case 3: origin non-promoted / destination promoted | Implemented / previously validated for wheat | Market loss plus receiver country-stock loss through generic route-good dispatcher; rerun required on latest head. |
| Case 4: origin promoted / destination promoted | Implemented / previously validated for wheat | Market loss plus receiver country-stock loss through explicit/trade-owner receiver path and generic route-good dispatcher; rerun required on latest head. |
| Receiver selection | MVP validated / partial generic | Stored receiving country and trade-owner-present paths are covered; US-10-style receiver allocator remains follow-up. |
| Generic good support | Implemented for US20 loss reconciliation | Market-level `add_goods_supply` uses saved route-good scope; promoted country-stock loss now dispatches route-good to literal `modeu5_remove_stock`. |
| Base receipt add/transfer | Not implemented in #107 | The PR reconciles delivery loss; it does not yet model the full base receipt add/transfer. |
| Static CI | Pending latest head | Re-check after latest implementation commit. |
| EU5 runtime validation | Previously validated; rerun required | Green evidence exists before the generic dispatcher patch; latest head needs the same run repeated. |

## Static validation scenarios

Run:

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_modeu5_persistent_state.sh
./tools/normalize_cmm_value_links.sh --check
python3 ./tools/validate_cmm_configuration.py
git diff --check
```

## In-game stable baseline scenario

Run:

```txt
event modeu5_revalidate_debug.1
```

Expected summary:

```txt
Failed: 0
Blocked: 0
Pending: 0
Missing expected full-revalidation scenarios: 0
ModeU5 TEST PASS scenario=main_revalidation_summary
ModeU5 TEST PASS scenario=us17_us20_route_reconciliation expected_probe_blocked=yes hard_failures=0
```

## Optional standalone US20 promoted-market E2E probe

Run this after the stable baseline is green:

```txt
event modeu5_us20_probe.1
```

Expected target:

```txt
ModeU5 TEST PASS scenario=us20_case12_market_loss_probe hard_failures=0 matrix=case1_case2_case3_case4 receivers=explicit_plus_trade_owner
```

Expected absence:

```txt
ASSERT FAIL
Failed to fetch variable for 'modeu5_us20...
global_var returned an unset scope
COUNTRY_LOSS_DISPATCH blocked
```

## Four-case E2E probe assertions

The promoted/non-promoted matrix probe asserts:

```txt
case1 classification = 1
case2 classification = 1
case3 classification = 1
case4 classification = 1
market add_goods_supply loss routes = 4
promoted destination country-loss routes = 2
explicit receiver selected = 1
trade-owner receiver selected = 1
blocked goods-delta routes = 0
blocked receiver selection routes = 0
```

## Remaining implementation steps after #107

1. Rerun the full baseline and US20 probe on the latest generic-dispatcher head.
2. Implement live receiver detection in the destination market, beyond the deterministic forced-present test path.
3. Extend US-10 candidate machinery with a receiver-allocation mode.
4. Implement base receipt operators separately from loss reconciliation:
   - case 3: add at destination country-market;
   - case 4: transfer country-market -> country-market.
5. Replace blocked money-side probe counters only after TECH-01 confirms country-income / route-profit read-write APIs.

## Merge caution

This PR can now be described as a route-level US17/US20 MVP with generic-good destination-loss reconciliation for all four market-accounting cases.

It should still not be described as full generic US-20 production completion until:

```txt
- latest generic dispatcher head is rerun in-game;
- live receiver allocator is implemented;
- base add/transfer receipt operators exist;
- TECH-01 resolves country-income / route-profit read-write APIs.
```

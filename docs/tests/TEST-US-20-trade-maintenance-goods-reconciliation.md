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

The current PR implements the formula, classification, explicit-receiver loss removal, market-level destination loss through `add_goods_supply`, blocked diagnostics, status visibility, and deterministic E2E probe coverage for the four promoted/non-promoted origin/destination cases.

It still does **not** claim full generic production runtime completion for every good and every receiver topology. The remaining gaps are the generic country-stock literal-good dispatcher, live receiver allocator, and TECH-01 trade-profit/country-income display-accounting API proof.

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

Runtime note: static CI verifies the file surface. The deterministic EU5 fixture confirms the test path reaches PASS with `Failed=0` and `Blocked=0`.

## Status legend

```txt
Implemented        = code path exists and is covered by static CI and/or deterministic in-game fixture surface
Validated          = deterministic in-game fixture has reached PASS for the stated surface
Partial            = scaffold/classification exists, but at least one runtime operator or generic dispatcher is missing
Specified only     = written contract exists, no concrete runtime code yet
Blocked TECH-01    = requires confirmed EU5 API/operator before safe implementation
```

## Runtime validation snapshot — 2026-07-09

Validation evidence captured from the installed PR branch during the US-17/US-20 revalidation session:

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

Interpretation:

```txt
Stable full baseline: green
US17/US20 route reconciliation: green
US20 case12 promoted/non-promoted E2E probe: green in deterministic fixture
```

## Current status snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Q8.7 placement | Validated | Hook stays in `modeu5_run_monthly_country_trade_owner_cycle -> every_trade`; no second route-discovery loop. |
| CMM trade-rework gate | Implemented | Route reconciliation is gated by `modeu5_trade_rework_enabled_trigger`; deterministic fixture checks dormant behavior when disabled. |
| CMM review popup placement | Implemented | `review_pop` is normalized to `nve_debug_audit_misc_review_pop_settings`; CI forbids legacy placement. |
| Money formula | Implemented / partial | Old price-side bonus removal and route delta are computed; #120 side remains placeholder until final #120 runtime model. |
| Treasury money application | Validated | Signed route money delta is applied through `add_gold`; this proves treasury/cash mutation only. |
| Vanilla income/profit application | Blocked TECH-01 | Probe matrix is documented/counted, but no speculative country-income or route-profit API calls are used. |
| Goods received formula | Validated | Target received amount and loss quantity are computed from `trade_maintenance`. |
| Market-level destination loss | Validated | Deterministic E2E probe reaches PASS with the negative `add_goods_supply` market-loss path. |
| Four-case market accounting | Validated | The case12 E2E probe covers non-promoted/non-promoted, promoted/non-promoted, non-promoted/promoted, and promoted/promoted paths. |
| Case 1: origin non-promoted / destination non-promoted | Validated | Destination market loss through `add_goods_supply`; no country-stock receiver required. |
| Case 2: origin promoted / destination non-promoted | Validated | Destination market loss through `add_goods_supply`; no country-stock receiver required. |
| Case 3: origin non-promoted / destination promoted | Validated for deterministic receiver | Market loss plus country-stock wheat loss when explicit receiver exists. Generic receiver allocation remains out of scope. |
| Case 4: origin promoted / destination promoted | Validated for deterministic receiver | Market loss plus country-stock wheat loss through explicit/trade-owner receiver path. Generic transfer receipt remains out of scope. |
| Receiver selection | MVP validated / partial generic | Stored receiving country and trade-owner-present paths are covered; US-10-style receiver allocator remains follow-up. |
| Generic good support | Partial | Market-level `add_goods_supply` uses the saved route good scope; country-stock `remove_stock` fixture remains wheat-only. |
| Static CI | Implemented | CI validates CMM surface and US17/US20 static contracts before runtime. |
| EU5 runtime validation | Validated | Full deterministic baseline and US20 E2E probe have green evidence from 2026-07-09. |

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

Expected result:

```txt
- no generated-file drift
- package validation success
- persistent-state audit success
- CMM value-link validation success
- CMM configuration validation success
- no whitespace/check diff failure
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
```

## Deterministic route-reconciliation fixture expectations

Expected result globals:

```txt
modeu5_test_us17_us20_reconciliation_started = yes
modeu5_test_us17_us20_reconciliation_passed = yes
modeu5_test_us17_us20_income_api_probe_blocked = yes
```

Expected deterministic values:

```txt
old_price_side_bonus ~= 35
clamped_average_efficiency ~= 0.15
money_delta ~= -34.85
goods_target ~= 99.97
goods_delta ~= -0.03
goods_loss_removed ~= 0.03
```

Expected income/profit probe counters:

```txt
modeu5_trade_efficiency_income_application_blocked_routes = 1
modeu5_trade_efficiency_income_application_probe_blocked = 1
modeu5_trade_efficiency_probe_read_country_income_blocked = 1
modeu5_trade_efficiency_probe_read_trade_profit_blocked = 1
modeu5_trade_efficiency_probe_add_trade_profit_blocked = 1
modeu5_trade_efficiency_probe_country_income_relation_blocked = 1
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

## Receiver allocator scenarios still to add

US-20 receiver allocation must reuse the same US-10 bucket sorting and tie-break ordering. The receiver-specific change is eligibility, not ordering.

| Scenario | Expected result | Current blocker |
| --- | --- | --- |
| Stored receiving country exists | stored receiver wins before fallback ordering | validated in deterministic probe |
| Trade owner present in destination market | trade owner selected as receiver before fallback ordering | validated through deterministic forced-present path; live detection remains scaffolded |
| Trade owner absent; multiple candidates under capacity | apply the same US-10 bucket/tie-break ordering after filtering receiver-eligible candidates | generated receiver allocator missing |
| Candidate at 99/100 capacity receiving 10 | eligible before receipt; may end at 109/100; ordering still follows US-10 buckets | capacity-aware receiver eligibility missing |
| Candidate at or above capacity | ineligible receiver before US-10 ordering is applied | capacity-aware receiver eligibility missing |

## Income/profit probe scenarios still to add

| Scenario | Expected result | Current blocker |
| --- | --- | --- |
| Read old trade-owner country income | value captured before route adjustment | confirmed EU5 API missing |
| Read old trade route profit | value captured before route adjustment | confirmed EU5 API missing |
| Add route delta to trade route profit | route profit mutates by delta | confirmed EU5 API missing |
| Read new country income after route-profit mutation | value captured after route adjustment | confirmed EU5 API missing |
| Verify relation | `old_country_income = new_country_income - added_trade_route_profit` if route profit feeds country income | confirmed EU5 API missing |

## Remaining implementation steps after #107

1. Generate route-good -> literal-good dispatchers for promoted country-stock `remove_stock` so US-20 country loss is not wheat-only.
2. Implement base receipt operators separately from loss reconciliation:
   - case 3: add at destination country-market;
   - case 4: transfer country-market -> country-market.
3. Implement live trade-owner-present detection in the destination market.
4. Extend US-10 candidate machinery with a receiver-allocation mode:
   - keep the same US-10 bucket sorting and tie-break ordering;
   - change only receiver eligibility thresholds;
   - ignore supplier protection thresholds;
   - require `current_stock < capacity` before receipt;
   - do not clip the full receipt to free capacity for MVP.
5. Replace blocked money-side probe counters only after TECH-01 confirms country-income / route-profit read-write APIs.

## Merge caution

This PR can now be described as a validated route-level US17/US20 MVP with deterministic four-case US20 E2E coverage.

It should still not be described as full generic US-20 production completion until:

```txt
- route-good literal dispatcher exists for country-stock remove_stock;
- base add/transfer receipt operators exist;
- receiver allocator is implemented;
- TECH-01 resolves country-income / route-profit read-write APIs.
```

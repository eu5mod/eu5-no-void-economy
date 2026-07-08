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

The current PR implements/scaffolds formula, classification, explicit-receiver loss removal, market-level destination loss through `add_goods_supply`, blocked diagnostics, and status visibility. It does not yet implement every base add/transfer and generic country-stock path.

## Status legend

```txt
Implemented        = code path exists and is covered by static CI and/or deterministic in-game fixture surface
Partial            = scaffold/classification exists, but at least one runtime operator or generic dispatcher is missing
Specified only     = written contract exists, no concrete runtime code yet
Blocked TECH-01    = requires confirmed EU5 API/operator before safe implementation
```

## Current status snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Q8.7 placement | Implemented | Hook stays in `modeu5_run_monthly_country_trade_owner_cycle -> every_trade`; no second route-discovery loop. |
| CMM trade-rework gate | Implemented | Route reconciliation is gated by `modeu5_trade_rework_enabled_trigger`; deterministic fixture checks dormant behavior when disabled. |
| Money formula | Implemented / partial | Old price-side bonus removal and route delta are computed; #120 side remains placeholder until final #120 runtime model. |
| Vanilla income/profit application | Blocked TECH-01 | Probe matrix is documented/counted, but no speculative country-income or route-profit API calls are used. |
| Goods received formula | Implemented | Target received amount and loss quantity are computed from `trade_maintenance`. |
| Market-level destination loss | Implemented | Uses documented market-scope `add_goods_supply` with a negative amount. |
| Four-case market accounting | Implemented as classification | Runtime classifies origin/destination promoted status and counts all four paths. |
| Case 1: origin non-promoted / destination non-promoted | Partial | Correct path is destination market loss through `add_goods_supply`; needs explicit non-promoted in-game fixture. |
| Case 2: origin promoted / destination non-promoted | Partial | Same destination market loss as case 1; needs explicit non-promoted in-game fixture. |
| Case 3: origin non-promoted / destination promoted | Partial | Requires base add-at-destination country-market operator; destination market loss exists; country-stock loss path exists only for explicit receiver + wheat fixture. |
| Case 4: origin promoted / destination promoted | Partial | Deterministic fixture covers classification + market loss + explicit receiver + wheat `remove_stock` loss; generic transfer receipt still missing. |
| Receiver selection | Partial / specified | Stored receiving country wins; trade-owner-present is scaffolded; US-10-style receiver allocator is still specified only. |
| Generic good support | Partial | Market-level `add_goods_supply` uses the saved route good scope; country-stock `remove_stock` fixture is still wheat-only. |
| Static CI | Implemented | Generated Files and Generate README pass. |
| EU5 runtime validation | Not run here | Needs in-game debug event execution. |

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

## In-game deterministic fixture scenario

Run the existing debug entry:

```txt
modeu5_revalidate_debug.2
  -> option: US-17 / US-20 route reconciliation fixture
```

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

Expected path counters:

```txt
modeu5_us20_case_origin_promoted_destination_promoted_routes = 1
modeu5_us20_market_goods_supply_loss_routes = 1
modeu5_us20_goods_loss_routes = 1
modeu5_us20_market_level_remove_good_blocked_routes = 0
modeu5_us20_goods_loss_target_selection_blocked_routes = 0
modeu5_us20_receiver_capacity_sort_blocked_routes = 0
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

## CMM gate scenario

Run the same fixture with the CMM trade-rework setting absent or disabled.

Expected result:

```txt
modeu5_trade_efficiency_routes_seen is absent or 0
modeu5_trade_efficiency_routes_quantity_confirmed is absent or 0
no US-17/US-20 route metrics are emitted
```

This proves the hook is dormant when the trade-rework setting is not active.

## Four-case matrix scenarios still to add

| Scenario | Fixture setup | Expected behavior | Current blocker |
| --- | --- | --- | --- |
| Case 1: origin non-promoted / destination non-promoted | `origin_promoted = 0`, `destination_promoted = 0`, saved route good | classify case 1; remove destination market loss through `add_goods_supply` | needs explicit case-1 fixture and in-game run |
| Case 2: origin promoted / destination non-promoted | `origin_promoted = 1`, `destination_promoted = 0`, saved route good | classify case 2; remove destination market loss through `add_goods_supply` | needs explicit case-2 fixture and in-game run |
| Case 3: origin non-promoted / destination promoted | `origin_promoted = 0`, `destination_promoted = 1`, explicit receiver | add received goods at destination country-market; remove loss at destination market and country-market | requires generated literal-good add-at-destination operator |
| Case 4: origin promoted / destination promoted | `origin_promoted = 1`, `destination_promoted = 1`, explicit receiver | transfer country-market to country-market; remove loss at destination market and country-market | current fixture covers classification + market loss + country loss; still needs generic transfer receipt operator |

## Receiver allocator scenarios still to add

US-20 receiver allocation must reuse the same US-10 bucket sorting and tie-break ordering. The receiver-specific change is eligibility, not ordering.

| Scenario | Expected result | Current blocker |
| --- | --- | --- |
| Stored receiving country exists | stored receiver wins before fallback ordering | implemented in fixture path |
| Trade owner present in destination market | trade owner selected as receiver before fallback ordering | live presence detection still scaffolded |
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

## Next implementation steps

1. Add explicit deterministic fixtures for case 1 and case 2 now that the market-level `add_goods_supply` surface is wired.
2. Generate route-good -> literal-good dispatchers for country-stock `remove_stock` so US-20 country loss is not wheat-only.
3. Implement base receipt operators separately from loss reconciliation:
   - case 3: add at destination country-market;
   - case 4: transfer country-market -> country-market.
4. Implement live trade-owner-present detection in the destination market.
5. Extend US-10 candidate machinery with a receiver-allocation mode:
   - keep the same US-10 bucket sorting and tie-break ordering;
   - change only receiver eligibility thresholds;
   - ignore supplier protection thresholds;
   - require `current_stock < capacity` before receipt;
   - do not clip the full receipt to free capacity for MVP.
6. Replace blocked money-side probe counters only after TECH-01 confirms country-income / route-profit read-write APIs.

## Merge caution

This PR is safe as a scaffold/formula/classification/market-loss PR, but it should not be described as full US-20 runtime completion until:

```txt
- case 1 and case 2 are explicitly run in-game;
- route-good literal dispatcher exists for country-stock remove_stock;
- base add/transfer receipt operators exist;
- receiver allocator is implemented;
- in-game debug scenario passes outside static CI.
```

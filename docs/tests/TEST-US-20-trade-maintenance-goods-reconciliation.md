# TEST-US-20 — Trade maintenance goods reconciliation

## Purpose

This plan validates the US-20 route-level MVP after implementation of BR-27
through BR-30.

US-20 has two distinct responsibilities:

```txt
base receipt:
  - add goods at the destination country×market when the origin is non-promoted;
  - transfer goods country×market to country×market when the origin is promoted.

loss reconciliation:
  - remove the delivery loss from the destination market stockpile;
  - when the destination is promoted, mirror that loss into the selected
    receiver country×market stock.
```

## Runtime surfaces

Market loss:

```txt
scope:target_market = {
  add_goods_supply = {
    goods = scope:route_good
    amount = -goods_loss_quantity
  }
}
```

Promoted-destination base receipt:

```txt
origin non-promoted:
  modeu5_add_stock(... capacity_policy = allow_over_capacity)

origin promoted:
  modeu5_transfer_stock(... target_capacity_policy = allow_over_capacity)
```

Promoted-destination receiver loss:

```txt
modeu5_apply_us20_promoted_destination_country_loss_by_route_good
```

The route-good dispatchers are generated from the canonical ModeU5 goods
registry. The deterministic runtime fixture uses wheat; all-goods support is a
static generator contract, not an assertion that every good has been exercised
in-game.

## Business-path matrix

| Probe path | Origin | Destination | Receiver path | Expected base receipt | Expected loss |
| --- | --- | --- | --- | --- | --- |
| Case 1 | non-promoted | non-promoted | none | none in ModeU5 country stock | destination market only |
| Case 2 | promoted | non-promoted | none | none in ModeU5 country stock | destination market only |
| Case 3 | non-promoted | promoted | stored explicit receiver | add at destination | market + receiver country stock |
| Case 4 | promoted | promoted | trade owner present in target market | country-market transfer | market + receiver country stock |
| Case 5 | non-promoted | promoted | allocator after rejecting stored receiver | add at destination | market + receiver country stock |

Case 5 is not a fifth origin/destination combination. It is a dedicated fallback
path proving BR-29/BR-30 receiver allocation and capacity rejection.

## Latest runtime evidence — 2026-07-10

Stable baseline:

```txt
ModeU5 TEST PASS scenario=main_revalidation_summary
ModeU5 TEST PASS scenario=us17_us20_route_reconciliation expected_probe_blocked=yes hard_failures=0
```

Standalone probe:

```txt
ModeU5 TEST PASS scenario=us20_case12_market_loss_probe hard_failures=0 matrix=case1_case2_case3_case4_case5 receivers=explicit_plus_trade_owner_plus_allocator
```

Observed receiver decisions:

```txt
selected=trade_owner reason=present_in_target_market
rejected=stored_receiver reason=capacity_not_eligible
selected=allocator_candidate reason=capacity_eligible_market_country_cache
selected=stored_receiver reason=explicit_receiving_country
```

Observed base-receipt operations:

```txt
BASE_RECEIPT applied=country_market_transfer capacity_policy=allow_over_capacity
BASE_RECEIPT applied=add_at_destination capacity_policy=allow_over_capacity
```

The first run before the fixture hardening showed an inherited stored receiver
being accepted during the allocator path. That produced an extra explicit-
receiver counter and a false assertion failure. The hardened fixture now:

```txt
- assigns a known stored receiver;
- makes it capacity-ineligible in the target market;
- verifies rejection;
- verifies allocator fallback;
- removes the poison stock after the path.
```

A repeated run then passed, and the latest clean run passed on its first
execution.

## Current status

| Area | Status | Evidence boundary |
| --- | --- | --- |
| Q8.7 placement | Validated | Existing country-owned `every_trade` loop. |
| Trade-rework gate | Validated fixture | Disabled route stays dormant. |
| Received-goods formula | Validated | Deterministic route inputs. |
| Case 1 market loss | Validated | Negative `add_goods_supply`. |
| Case 2 market loss | Validated | Negative `add_goods_supply`. |
| BR-27 add-at-destination | Validated | Cases 3 and 5. |
| BR-28 country-market transfer | Validated | Case 4. |
| BR-29 receiver priority/fallback | Validated MVP | Stored receiver, trade owner, allocator. |
| BR-30 capacity eligibility | Validated MVP | Stored receiver rejected above capacity; allocator selected. |
| Receiver country-stock loss | Validated | Three promoted-destination paths. |
| Generic route-good dispatch | Static coverage | Generated for canonical goods; wheat runtime fixture. |
| Repeatability | Validated | Consecutive runs pass after full fixture cleanup. |
| Localization-disabled assertion | Patched; rerun required | Launcher now defers work to hidden event `.10`. |
| TECH-01 money display accounting | Out of US-20 scope | Remains explicit expected block under US-17. |

## Static validation

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_modeu5_persistent_state.sh
./tools/normalize_cmm_value_links.sh --check
python3 ./tools/validate_cmm_configuration.py
git diff --check
```

## Runtime protocol

Install the exact branch head and clear logs:

```sh
./tools/install_local_packages.sh
./tools/clear_eu5_logs.sh
```

Run the stable baseline:

```txt
event modeu5_revalidate_debug.1
```

Run the standalone probe:

```txt
event modeu5_us20_probe.1
```

The console event only schedules a hidden continuation. The probe effect and its
`debug_log` markers execute in that continuation so the first log line is not
processed inside the console command's localization-disabled context.

## Assertions

The probe expects:

```txt
case1 classification = 1
case2 classification = 1
case3 classification = 2
case4 classification = 1
market add_goods_supply loss routes = 5
promoted destination country-loss routes = 3
explicit receiver selected = 1
trade-owner receiver selected = 1
receiver selection blocked routes = 0
market-loss blocked routes = 0
goods-delta blocked routes = 0
```

The two case-3 classifications are the explicit-receiver and allocator paths.

## Post-run grep

```sh
grep -R -E "main_revalidation_summary|us17_us20_route_reconciliation|us20_case12_market_loss_probe|US20 CASE12|BASE_RECEIPT|RECEIVER_SELECTION|rejected=stored_receiver|allocator_candidate|RECEIVER_CAPACITY_DISPATCH|BASE_RECEIPT_DISPATCH|COUNTRY_LOSS_DISPATCH|ASSERT FAIL|Failed to fetch variable for .modeu5_us20|global_var returned an unset scope|Tried to localize with localization disabled" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs" || true
```

Expected positive markers:

```txt
ModeU5 TEST PASS scenario=us20_case12_market_loss_probe hard_failures=0 matrix=case1_case2_case3_case4_case5 receivers=explicit_plus_trade_owner_plus_allocator
ModeU5 US20 RECEIVER_SELECTION rejected=stored_receiver reason=capacity_not_eligible
ModeU5 US20 RECEIVER_SELECTION selected=allocator_candidate
ModeU5 US20 BASE_RECEIPT applied=add_at_destination
ModeU5 US20 BASE_RECEIPT applied=country_market_transfer
```

Expected absence:

```txt
ASSERT FAIL
RECEIVER_CAPACITY_DISPATCH blocked
BASE_RECEIPT_DISPATCH blocked
COUNTRY_LOSS_DISPATCH blocked
Failed to fetch variable for 'modeu5_us20...
global_var returned an unset scope
Tried to localize with localization disabled
```

## Probe-hygiene rules learned from this run

1. **Defer console-triggered logging.** A console launcher should schedule a
   hidden event before running any effect that emits test logs.
2. **Do not rely on scope absence.** Named temporary scopes can remain visible
   through chained effects. Explicitly overwrite or invalidate higher-priority
   candidates.
3. **Force the fallback precondition.** To test an allocator, make the stored
   receiver and trade-owner paths demonstrably ineligible; merely omitting setup
   is not sufficient.
4. **Use symmetric cleanup.** Remove market supply, receiver stock, poison stock,
   global counters, and test markers after or before every run.
5. **Order paths defensively.** Run allocator fallback before the explicit-
   receiver case when the explicit case could leave a reusable receiver scope.
6. **Separate old and current logs.** Clear logs for acceptance. Otherwise a
   historical failure can appear beside a current pass and make the run look
   inconsistent.
7. **Separate static and runtime proof.** Generated all-goods dispatch is static
   proof; a wheat fixture is runtime representative proof.
8. **Keep real blocks visible.** TECH-01 and missing engine surfaces must remain
   expected-blocked rather than being converted into artificial PASS markers.

## Acceptance statement

US-20 BR-27 through BR-30 are accepted for the route-level MVP when:

```txt
- static generator checks pass;
- stable revalidation passes;
- the five-path standalone probe passes with hard_failures=0;
- the localization-disabled assertion is absent after the deferred-launch patch;
- no blocked dispatcher or unset US-20 scope appears.
```

This does not claim exhaustive live-world coverage across every country, market,
route topology, and good. It does establish the implemented business rules,
receiver fallbacks, capacity gate, receipt operations, loss operations, and
repeatable deterministic fixture.

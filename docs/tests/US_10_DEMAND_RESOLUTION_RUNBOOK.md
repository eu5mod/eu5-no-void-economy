# US-10 Demand Resolution Runbook

## Scope

This runbook validates the first explicit-request implementation of:

- US-10.1 consumption stock resolution within one market;
- US-10.2 inter-market stock transfer;
- US-10.3 requested / satisfied / unsatisfied outcome tracking.

The test deliberately uses explicit ModeU5 requests. Runtime vanilla Pop demand
quantity and exact vanilla trade quantity remain partially unconfirmed in
TECH-01, so this PR does not pretend to resolve live Pop or vanilla trade flows
yet.

## Install

```bash
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Focused In-Game Test

Start a disposable campaign where France and England exist and have distinct
capital markets. Then run:

```txt
event modeu5_us10_debug.1
```

Choose:

```txt
Run US-10 demand-resolution test
```

Expected result:

```txt
PASS - US-10 demand resolution
```

Expected dump:

```txt
Consumption requested = 100
Consumption satisfied = 80
Consumption unsatisfied = 20
FRA stock after consumption = 0

Trade requested = 100
Trade transferred = 70
Trade unsatisfied = 30
Buyer stock after = 70
Seller stock after = 20
Buyer capacity before transfer = 70
```

## Broad Revalidation

The broad chain now includes the US-10 scenario:

```txt
event modeu5_revalidate_debug.1
```

Choose:

```txt
Revalidate main operations
```

After closing EU5:

```bash
./tools/summarize_modeu5_test_logs.sh
```

Expected summary includes:

```txt
ModeU5 TEST ENTERED scenario=us10_demand_resolution
ModeU5 TEST PASS scenario=us10_demand_resolution
Missing expected scenarios: 0
Failed:  0
Blocked: 0
```

## Logs Are Source Of Truth

Review `debug.log`, `error.log`, `game.log`, and `system.log`. The compact
summary is only the first-pass index. A PR validation comment must include the
exact scenario lines and classify any remaining non-blocking noise.

## Known Limitations

- Candidate ordering is explicit in this PR: the caller provides the stock
  provider/seller. Full automatic US-10.0 candidate selection remains future
  work.
- Live vanilla Pop demand quantity is not read yet.
- Exact vanilla trade requested/actual quantity is not read yet.
- The implementation records country-market-good monthly outcomes. The
  location-good Pop bridge for US-04 remains gated behind the live Pop demand
  exposure/fallback story.

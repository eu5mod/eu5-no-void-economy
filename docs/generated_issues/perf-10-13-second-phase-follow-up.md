# PERF-10/13 - Second-Phase Performance Guardrails

Labels: performance, technical-foundation, testing

## User Story

```txt
PERF-10/13 - second-phase performance guardrails
```

As a maintainer, I want the remaining issue #89 performance tracks to be
documented, guarded, and testable without widening normal runtime work, so that
future optimization changes do not reintroduce shared-state work into generated
per-good loops.

## Scope

This PR completes the issue #89 follow-up around PERF-10 through PERF-13:

```txt
PERF-10 - per-good loop audit and preservation
PERF-11 - active-list semantics and repair
PERF-12 - market-scope value/link probes
PERF-13 - batch and metrics layer
```

## Design

### PERF-10 - Audit Legitimate Per-Good Loops

Per-good loops remain valid where the state is truly per-good:

```txt
country-market-good stock
market-good aggregate stock
add/remove/transfer/decay
US-00 production, ledger, void wealth, and penalty records
CORE-02 opening stock
US-11 dirty and active market-good validation
```

Shared storage capacity must stay good-neutral. The audit script fails if
generated per-good adapters regain old capacity refresh helpers or if gameplay
code starts using `traded_in_market:<good>` before TECH-01 confirms it.

### PERF-11 - Active-List Repair

Active lists are scheduling indexes, not stock sources. They may be
overinclusive, but capacity-only state must not mark a market-good active.

This PR adds a generated repair pass:

```txt
modeu5_repair_all_active_stock_markets
modeu5_repair_active_markets_good_<good>
```

The repair rebuilds active market lists from confirmed ModeU5 state:

```txt
market aggregate stock
country stock
US-00 produced / added / rejected / ratios / void wealth / penalty
```

It deliberately ignores shared US-02 capacity maps.

### PERF-12 - Market-Value Probe Only

The confirmed runtime gates remain:

```txt
produced_in_market:<good>
stockpile_in_market(goods:<good>)
```

`traded_in_market:<good>` is still probe-only. Runtime gameplay must not use it
until a focused test confirms the syntax, scope, and error behavior.

### PERF-13 - Metrics Without Normal Runtime Cost

The active-list repair probe records explicit counters only when invoked by
debug/test code:

```txt
goods_scanned
market_good_scans
country_source_checks
market_aggregate_hits
country_state_hits
market_goods_marked
```

Normal runtime does not capture these metrics.

## Acceptance Criteria

- [ ] `tools/audit_modeu5_per_good_loops.sh` passes.
- [ ] `tools/validate_module_packages.sh` runs the audit.
- [ ] Main revalidation includes the PERF-10/11/13 active-list repair metrics probe.
- [ ] The compact log summary expects `perf10_13_active_repair_metrics`.
- [ ] PERF-12 is available through `event modeu5_perf12_debug.1` but is not part of normal runtime or main revalidation.
- [ ] TECH-01 records `traded_in_market:<good>` as `TO_TEST`.

## Manual Test Scenario

Build and install:

```sh
./tools/generate_all.sh
./tools/validate_module_packages.sh
git diff --check
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Run broad revalidation:

```txt
event modeu5_revalidate_debug.1
Select "Revalidate main operations"
Wait for the final result event.
```

Then summarize:

```sh
./tools/summarize_modeu5_test_logs.sh
```

Expected compact result:

```txt
Failed: 0
Blocked: 0
Missing expected scenarios: 0
ModeU5 TEST PASS scenario=perf10_13_active_repair_metrics
```

Focused PERF-12 exposure probe:

```txt
event modeu5_perf12_debug.1
Select "Run market-scope value probe"
```

Expected if the candidate link is valid:

```txt
ModeU5 PERF-12 DUMP market_values good=wheat ...
ModeU5 PERF-12 RESULT market_values PASS
```

If the probe emits script errors for `traded_in_market:wheat`, do not use that
value in runtime. Update TECH-01 with the observed failure and keep the probe
as evidence.

## Known Limitations

- No EU5 runtime validation has been run yet on this commit.
- PERF-12 deliberately probes an unconfirmed value link and may fail until the
  exact syntax/scope is confirmed.
- Durable per-market country-list caches and dedicated market-change hooks
  remain blocked by TECH-01 126 and 127.
- Active-list repair is a debug/maintenance tool. It does not make active lists
  authoritative stock state.

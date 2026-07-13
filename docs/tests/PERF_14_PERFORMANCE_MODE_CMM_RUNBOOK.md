# PERF-14 Performance Mode CMM Plumbing Runbook

## Purpose

Validate the first stacked implementation under the PERF-14 / US-10-UI master
PR.

This test proves the CMM mode plumbing, the human-relevant market discovery
list, the non-detailed -> detailed eligibility edge case, the first read-only
country-market accounting decision, the explicit promotion boundary required
before Performance Mode may use detailed country-market stock mutation, and the
shared pre-mutation accounting gate. It also validates the market-level monthly
runtime gate used by US-00 and US-10: human-relevant promoted markets run
ModeU5 detailed accounting, while non-human-relevant markets are left to vanilla
fallback. It does not yet prove sparse supplier cache maintenance or US-10 UI
rendering.

## Business Rule Under Test

Performance Mode keeps the ModeU5 economic layer only where it matters for the
human player:

```txt
monthly_country_pulse
  -> every_market_center_in_country
  -> if market is human-relevant and promoted:
       run ModeU5 detailed monthly runtime for that market
     else:
       use vanilla fallback and skip ModeU5 stock-affecting runtime
```

For this PR, the gate is wired for:

- US-00 monthly production ingestion and balance/penalty bookkeeping;
- US-10 monthly consumption and inter-market transfer resolution.

Future monthly stock-affecting runtime paths, including US-03 decay and any
US-17/US-20 follow-up, must use the same market-runtime gate. US-09 static
rebalance files are package-level static data, not a monthly runtime mutation;
only future runtime balancing logic adjacent to US-09 would need this gate.

## Setup

Use a disposable campaign with the ModeU5 Core test package installed.

Recommended baseline:

```txt
Start as a human-played country that owns at least one market location.
Castile / CAS is suitable when available.
```

The event temporarily changes the current country's CMM
`cbp_no_void_economy_main` value to:

```txt
1 = Active Performance Mode
2 = Active Normal Mode
3 = Deactivated
```

For audit review, use the following map consistently:

```txt
cbp_no_void_economy_main=1 -> Active Performance
  performance=1 normal=0 deactivated=0
  Performance sparsity applies: human-relevant/promoted markets use detailed ModeU5 runtime;
  non-human-relevant markets use vanilla fallback.

cbp_no_void_economy_main=2 -> Active Normal
  performance=0 normal=1 deactivated=0
  Sparsity is disabled: detailed ModeU5 runtime is allowed without promotion.

cbp_no_void_economy_main=3 -> Deactivated
  performance=0 normal=0 deactivated=1
  ModeU5 stock-affecting runtime is blocked.
```

It restores the original CMM value before finishing.

## Console Command

```txt
event cbp_perf14_debug.1
```

Choose:

```txt
Run performance mode CMM probe
```

## Expected Result

The result event should show:

```txt
PASS - Performance Mode CMM plumbing
```

The logs should include:

```txt
ModeU5 DEBUG_LEVEL scenario=perf14_performance_mode_cmm phase=before_guarded_probe level=... normal=0 debug=1 audit=1
ModeU5 TEST ENTERED scenario=perf14_performance_mode_cmm
ModeU5 PERF-14 DUMP main_mode=...
ModeU5 PERF-14 STOCK_MUTATION_GATE detailed=1 fallback=0 blocked=0 promotion_attempted=1 promotion_succeeded=1 result=1
# Active Performance / cbp_no_void_economy_main=1 / human-relevant market -> detailed ModeU5 monthly runtime
ModeU5 PERF-14 MARKET_RUNTIME_GATE detailed=1 vanilla_fallback=0 blocked=0 human_relevant=1 promotion_attempted=1 promotion_succeeded=1 result=1
# Active Performance / cbp_no_void_economy_main=1 / non-human-relevant market -> vanilla fallback
ModeU5 PERF-14 MARKET_RUNTIME_GATE detailed=0 vanilla_fallback=1 blocked=0 human_relevant=0 promotion_attempted=0 promotion_succeeded=0 result=2
ModeU5 PERF-14 PROMOTION positive aggregate=120 ...
ModeU5 PERF-14 PROMOTION idempotent ...
ModeU5 PERF-14 PROMOTION partial aggregate=100 ...
ModeU5 PERF-14 RESULT performance_mode_cmm PASS
ModeU5 TEST PASS scenario=perf14_performance_mode_cmm
ModeU5 DEBUG_LEVEL scenario=perf14_performance_mode_cmm phase=after_guarded_probe level=...
```

`before_guarded_probe` must show `debug=1 audit=1`, which confirms the event
entered test-audit runtime mode before running the guarded PERF-14 probes. The
numeric `level` remains the configured CMM debug-message level, so the audit flag
is the authoritative check for Audit runtime.

For the Performance Mode branch, the dump should show:

```txt
main_mode=1
performance=1
normal=0
deactivated=0
detailed=1
mutation_allowed=1
fallback=0
human=1
market_human_relevant=1
current_market_human_relevant=1
promotion_result=1
```

The `main_mode=1 performance=1 normal=0 deactivated=0` tuple is the audit proof
that the positive and vanilla-fallback `MARKET_RUNTIME_GATE` lines were evaluated
under Active Performance Mode. Separate Normal and Deactivated gate probes should
be read with this same mapping: `main_mode=2` means Active Normal, and
`main_mode=3` means Deactivated.

The relevant market list is rebuilt from:

```txt
every_country limit = { is_ai = no }
  -> every_market_present_in_country
```

The test also clears the relevant-market list before the Performance Mode
decision, then expects the accounting gate to mark the current human-present
market as eligible on demand. A PASS therefore proves that a market can become
eligible for detailed diagnostics at the point where runtime accounting needs
it, not only after startup rebuild.

The probe then promotes the current market to detailed accounting and expects:

```txt
aggregate-only fixture:
  market aggregate before promotion = 120
  country stock sum after promotion = 120
  market aggregate after promotion = 120
  detailed mutation allowed = 1

idempotency:
  running promotion twice keeps country sum and market aggregate unchanged

partial-state fixture:
  existing country stock = 25
  market aggregate before promotion = 100
  country stock sum after promotion = 100
  market aggregate after promotion = 100
```

The same probe also checks negative read-only decisions:

```txt
AI country + its market in Performance Mode
  -> detailed = 0
  -> fallback = 1

Human country + a market not returned by every_market_present_in_country
  -> detailed = 0
  -> fallback = 1
  -> promotion blocked
  -> promoted marker absent
```

If the campaign bookmark cannot provide an AI-country market fixture or a
distinct non-present market fixture, the probe returns BLOCKED instead of PASS.

The same event now also validates the stock-affecting decision gate:

```txt
Active Performance / cbp_no_void_economy_main=1 + human-present unpromoted market
  -> promotion attempted
  -> promotion succeeds
  -> detailed stock mutation path allowed

Active Performance / cbp_no_void_economy_main=1 + AI market that is not human-relevant
  -> detailed mutation disabled
  -> vanilla fallback selected

Active Performance / cbp_no_void_economy_main=1 + AI country inside a human-relevant market
  -> promotion attempted
  -> promotion succeeds
  -> detailed stock mutation path allowed

Active Performance / cbp_no_void_economy_main=1 + human country in non-present market
  -> detailed mutation disabled
  -> vanilla fallback selected
  -> promotion not attempted by the stock gate

Active Performance monthly market runtime gate / cbp_no_void_economy_main=1 + human-relevant unpromoted market
  -> promotion attempted
  -> promotion succeeds
  -> detailed ModeU5 runtime selected

Active Performance monthly market runtime gate / cbp_no_void_economy_main=1 + market absent from the human-relevant list
  -> detailed ModeU5 runtime disabled
  -> vanilla fallback selected
  -> promotion not attempted

Active Normal / cbp_no_void_economy_main=2
  -> detailed stock mutation path allowed without promotion
  -> detailed monthly runtime allowed without Performance Mode promotion

Deactivated / cbp_no_void_economy_main=3
  -> detailed mutation disabled
  -> fallback disabled
  -> mutation blocked
  -> monthly runtime blocked
```

## Log Summary Helper

After running the event, use:

```txt
./tools/summarize_cbp_logs.sh
```

The helper now prints separate counts and sections for:

```txt
Debug level markers
Main mode traces
PERF-14 diagnostics

Debug level lines
Main mode trace lines
PERF-14 diagnostic lines
Scenario lines
Localization-disabled-only ModeU5 markers
```

The `Main mode trace lines` section is extracted from the runtime log line:

```txt
ModeU5 PERF-14 DUMP main_mode=... performance=... normal=... deactivated=...
```

and prints the audit map inline:

```txt
Mode map: main_mode=1 Active Performance; main_mode=2 Active Normal; main_mode=3 Deactivated.
```

`PERF-14 diagnostic lines` also includes `MARKET_RUNTIME_GATE` entries so the
summary shows both the active CMM situation and the detailed/vanilla-fallback/
blocked gate result in one place.

If the summary shows only localization-disabled copies of `ModeU5 TEST`,
`ModeU5 DEBUG_LEVEL`, or `ModeU5 PERF-14` lines, treat the runtime result as
inconclusive and inspect `debug.log` / `game.log` before posting PASS.

## Static Checks

Run:

```txt
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/normalize_cmm_value_links.sh --check
python3 ./tools/validate_cmm_configuration.py
git diff --check
```

## Known Limitations

- This PR gates US-00 monthly production ingestion and US-10 monthly demand
  resolution at market-runtime dispatch time. It does not yet route US-03,
  US-17, US-20, or other runtime stock mutations through the same gate.
- Performance Mode fallback is vanilla fallback. It deliberately does not
  implement a market-level aggregate-only ModeU5 mutation operator.
- This PR implements `cbp_promote_market_to_detailed_accounting`, but later
  stock-affecting PRs must still call/check
  `cbp_detailed_country_market_stock_mutation_allowed_trigger` before using
  detailed country-market mutation in Performance Mode.
- The sparse supplier stacked layer emits:
  `ModeU5 PERF-14 SPARSE_SUPPLIERS good=wheat present=<n> sparse=<n> candidates=<n> used=1 fallback=0`.
  A passing targeted run should show `used=1`, `fallback=0`, and
  `candidates == sparse` for the wheat fixture.
- This PR does not yet prove the foreign-building-only negative case; it uses
  the confirmed `every_market_present_in_country` iterator as the current
  human-relevant market definition.
- Market-border movement is handled by a monthly-stamped rebuild and on-demand
  eligibility marking; removing stale human-relevant markets before the next
  monthly rebuild is not required because stale over-inclusion is safe but less
  sparse.
- Durable sparse supplier cache invalidation and US-10 UI diagnostics remain
  later stacked PRs. This layer uses on-demand sparse supplier lists, not a
  persisted cache.

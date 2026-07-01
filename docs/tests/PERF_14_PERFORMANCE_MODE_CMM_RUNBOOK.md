# PERF-14 Performance Mode CMM Plumbing Runbook

## Purpose

Validate the first stacked implementation under the PERF-14 / US-10-UI master
PR.

This test proves only the CMM mode plumbing, the human-relevant market discovery
list, the non-detailed -> detailed eligibility edge case, the first read-only
country-market accounting decision, and the explicit promotion boundary required
before Performance Mode may use detailed country-market stock mutation. It does
not yet prove market-level fallback stock mutation, sparse supplier cache
maintenance, or US-10 UI rendering.

## Setup

Use a disposable campaign with the ModeU5 Core test package installed.

Recommended baseline:

```txt
Start as a human-played country that owns at least one market location.
Castile / CAS is suitable when available.
```

The event temporarily changes the current country's CMM
`nve_no_void_economy_main` value to:

```txt
1 = Performance Mode
2 = Normal Mode
3 = Deactivated
```

It restores the original CMM value before finishing.

## Console Command

```txt
event modeu5_perf14_debug.1
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
ModeU5 TEST ENTERED scenario=perf14_performance_mode_cmm
ModeU5 PERF-14 DUMP main_mode=...
ModeU5 PERF-14 PROMOTION positive aggregate=120 ...
ModeU5 PERF-14 PROMOTION idempotent ...
ModeU5 PERF-14 PROMOTION partial aggregate=100 ...
ModeU5 PERF-14 RESULT performance_mode_cmm PASS
ModeU5 TEST PASS scenario=perf14_performance_mode_cmm
```

For the Performance Mode branch, the dump should show:

```txt
main_mode=1
performance=1
detailed=1
mutation_allowed=1
fallback=0
human=1
market_human_relevant=1
current_market_human_relevant=1
promotion_result=1
```

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

- This PR does not yet route stock mutations through the accounting gate.
- This PR does not yet implement market-level aggregate fallback mutation.
- This PR implements `modeu5_promote_market_to_detailed_accounting`, but later
  stock-affecting PRs must still call/check
  `modeu5_detailed_country_market_stock_mutation_allowed_trigger` before using
  detailed country-market mutation in Performance Mode.
- This PR does not yet prove the foreign-building-only negative case; it uses
  the confirmed `every_market_present_in_country` iterator as the current
  human-relevant market definition.
- Market-border movement is handled by a monthly-stamped rebuild and on-demand
  eligibility marking; removing stale human-relevant markets before the next
  monthly rebuild is not required because stale over-inclusion is safe but less
  sparse.
- Sparse supplier lists and US-10 UI diagnostics remain later stacked PRs.

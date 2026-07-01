# PERF-14 Performance Mode CMM Plumbing Runbook

## Purpose

Validate the first stacked implementation under the PERF-14 / US-10-UI master
PR.

This test proves only the CMM mode plumbing, the human-relevant market discovery
list, and the first read-only country-market accounting decision. It does not
yet prove market-level fallback stock mutation, sparse supplier cache
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
ModeU5 PERF-14 RESULT performance_mode_cmm PASS
ModeU5 TEST PASS scenario=perf14_performance_mode_cmm
```

For the Performance Mode branch, the dump should show:

```txt
main_mode=1
performance=1
detailed=1
fallback=0
human=1
market_human_relevant=1
current_market_human_relevant=1
```

The relevant market list is rebuilt from:

```txt
every_country limit = { is_ai = no }
  -> every_market_present_in_country
```

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
- This PR does not yet prove the foreign-building-only negative case; it uses
  the confirmed `every_market_present_in_country` iterator as the current
  human-relevant market definition.
- This PR does not yet define a long-lived cache invalidation policy for moving
  market borders.
- Sparse supplier lists and US-10 UI diagnostics remain later stacked PRs.

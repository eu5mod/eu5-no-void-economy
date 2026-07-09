# Q8.0 — Post-PR126 baseline audit

## Purpose

Before implementing Q8, freeze the post-PR126 baseline. Q8 should optimise a known runtime shape, not chase stale assumptions from earlier stacked PRs.

This document defines the audit to run before any Q8 runtime change.

## Baseline to confirm

The current `main` baseline after #126 should be treated as:

```txt
monthly country pulse
  -> readiness / configuration gates
  -> country-owned preparation
  -> promoted-market local branch through current ownership workaround
  -> country trade-owner pass
  -> validation / reconciliation / reset where enabled
```

The audit must identify exactly where repeated work remains after PR126.

## Files to inspect first

```txt
in_game/common/on_action/modeu5_stock_on_actions.txt
in_game/common/scripted_effects/modeu5_stock_effects.txt
in_game/common/scripted_effects/modeu5_promoted_market_cycle_effects.txt
in_game/common/scripted_effects/modeu5_performance_effects.txt
in_game/common/scripted_effects/modeu5_capacity_effects.txt
in_game/common/scripted_effects/modeu5_stock_demand_resolver_effects.txt
tools/generate_stock_good_helpers.sh
tools/generate_pr71_active_good_dispatch_helpers.sh
tools/validate_generators.sh
tools/audit_modeu5_persistent_state.sh
```

## Audit questions

### A. Monthly ownership boundaries

```txt
1. Which helpers still run from country pulse?
2. Which helpers are logically market-local but still entered through country scope?
3. Which helpers are true country-owned work?
4. Which helpers are trade-owned and must remain country scoped because `every_trade` is confirmed there?
```

### B. Repeated market/country cache work

```txt
1. How often is `countries_present_in_market` rebuilt per monthly cycle?
2. Which callers rebuild it?
3. Is every rebuild tied to one target market?
4. Are dirty-market lists consumed before broad rebuilds?
5. Are location ownership or market topology changes explicitly dirtying affected caches?
```

### C. Capacity refresh cost

```txt
1. Which helper calculates the country-wide storage capacity pool?
2. Which helper calculates the country-market capacity record?
3. Is the country pool recalculated once per country, or once per country per promoted market?
4. Are capacity lifecycle hooks already marking enough dirty state to support Q8.3 / F1 stamping?
```

### D. US-10 gating

```txt
1. Where are same-market requests created?
2. Where are pending request maps written?
3. Does any aggregate country-market request gate already exist before per-good dispatch?
4. Are no-request country-market pairs entering generated US-10 dispatch?
5. Are sparse supplier lists used only after a good/request is selected?
```

### E. PR7.1 metrics and counters

```txt
1. Which per-good considered/processed counters are unconditional?
2. Which counters are needed for business correctness?
3. Which counters are debug/profile only?
4. Is there already a configuration/profile trigger that can guard them?
```

### F. Native/global market pass feasibility

```txt
1. Does TECH-01 confirm `every_market_in_world` from a true global/none scope?
2. Is there a safe monthly/global on_action surface to enter it exactly once?
3. Can the pass preserve PR126 ordering: country prep -> market-local -> country trade -> validation?
4. If not, keep F7 as a probe and do not implement live runtime changes.
```

## Required output of the audit

A Q8 audit PR/comment must classify each candidate as one of:

```txt
IMPLEMENT_NOW
PROBE_FIRST
DOC_ONLY
REJECT_FOR_NOW
OUT_OF_SCOPE
```

It must also record:

```txt
- files touched;
- current runtime owner;
- target runtime owner;
- expected reduction in repeated work;
- validation event/log lines to inspect;
- known safety risk.
```

## Validation commands for audit-only PRs

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_modeu5_persistent_state.sh
git diff --check
```

If runtime probes are added later, add a commit-specific PR comment with the exact debug event, installed package provenance, relevant `debug.log` / `error.log` lines, and PASS / PENDING / FAIL decision.

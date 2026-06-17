# US-00.3 — Monthly Production Penalty from Overproduction

Labels: none

## User Story

```txt
US-00.3 — Monthly Production Penalty from Overproduction
```

As a player, I want unstockable production to reduce future overproduction so the economy adapts to storage constraints.

## Functional objective

Convert effective overproduction into a capped temporary penalty applied during month N+1 to owned locations in the affected market that produce the affected good.

## Runtime position

```txt
Monthly step: apply previous penalty at step 2; calculate replacement at step 15
Depends on counters from: US-00.2
Feeds counters to: next monthly cycle, US-00-UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Effective ratio calculation/output | country × market × good | US-00.2 result using guarded `change_variable` arithmetic | CONFIRMED | 026 |
| Read keyed ratio entry | country-scoped per-good map keyed by market | <code>variable_map(name&#124;key)</code> | CONFIRMED | 007, 025 |
| Prepared N+1 penalty field | country × market × good record | logical `production_penalty` field; physical `modeu5_<good>_production_penalty_by_market` map keyed by market | CONFIRMED | 007, 025 |
| Identify affected production sources/locations | building/location/market/good | production iterators, output checks, `market` link | CONFIRMED | 003-004, 029 |
| Identify the country to penalize | country-rooted cycle → affected owned location | current country plus owned-location and market context | CONFIRMED | 003-005, 011, 081 |
| Preferred modifier | location × good | `local_<good>_output_modifier` | CONFIRMED | 027 |
| Fallback modifier | location | `local_production_efficiency` | CONFIRMED | 028 |
| Apply temporary location modifier | location | `add_location_modifier` with duration, mode, and dynamic size | CONFIRMED | 010 |

## Files expected to change

```txt
in_game/common/script_values/
in_game/common/scripted_effects/
in_game/common/on_action/
in_game/common/modifiers/
in_game/localization/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-00.2, location/production exposure, TECH-01
Blocks: applied void-economy correction
Related US: US-09, US-00-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Follow `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.
- Calculate `-min(max_penalty, effective_ratio × coefficient)`.
- Apply month N results only during month N+1 and replace the prior penalty monthly.
- Persist only the prepared N+1 penalty. Keep temporary arithmetic and affected-location discovery local to the current effect chain.
- Add the prepared value as the `production_penalty` field of the shared country × market × good record.
- Physically store it on the country in a per-good map keyed by market, with a default of zero and remove/re-add replacement.
- Use the same producing-country/source attribution established by US-00.1 when selecting penalty targets.
- Do not silently switch to location ownership if it would penalize a different country from the one credited in the ledger.
- Prefer good-specific output; use local production efficiency only as the single accepted fallback.
- If no reliable modifier exists, calculate and display a theoretical-only penalty.
- Never mutate stock or Estate tax/income values.

## US-specific boundary checks

- [ ] The penalty uses effective, not raw, overproduction.
- [ ] It targets only the relevant country, market, good, and producing locations where exposure permits.
- [ ] The country credited with rejected production is the country whose eligible production sources receive the penalty.
- [ ] Fallback and theoretical-only modes are explicit.

## Acceptance criteria

- [ ] Zero effective overproduction yields zero penalty.
- [ ] Penalty magnitude is capped and uses configurable coefficients.
- [ ] N+1 application timing is deterministic.
- [ ] The prepared penalty survives until N+1 without retaining temporary candidate/location state.
- [ ] Preferred, fallback, and theoretical-only modes are distinguishable in debug.
- [ ] A fallback affecting unrelated goods is documented.
- [ ] No direct stock or Estate-income mutation occurs.
- [ ] TECH-01, logs, and manual test evidence are updated.

## Manual test scenario

### Setup

```txt
Country A owns two iron-producing locations in Market M and one in Market N
Market M effective iron overproduction: 0.19
Coefficient/max penalty: 1.00
```

### Expected result

```txt
Calculated M/iron penalty: -0.19 for month N+1
Only eligible Market M iron locations are targeted in preferred mode
Market N is unaffected
Debug records affected count, application mode, and fallback status
```

## Known limitations

The required modifier names, producer-location discovery, country-rooted attribution, and temporary location-modifier effect are documented. A controlled local test must still verify month-to-month replacement and immediate recalculation behavior.

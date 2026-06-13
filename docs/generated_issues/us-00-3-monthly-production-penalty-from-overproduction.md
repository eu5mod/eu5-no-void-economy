# US-00.3 — Monthly Production Penalty from Overproduction

Labels: `blocked:engine-exposure`

## User Story

```txt
US-00.3 — Monthly Production Penalty from Overproduction
```

As a player, I want unstockable production to reduce future overproduction so the economy adapts to storage constraints.

## Functional objective

Convert effective overproduction into a capped temporary penalty applied during month N+1 to owned locations in the affected market that produce the affected good.

## Runtime position

```txt
Monthly step: apply previous penalty at step 1; calculate replacement at step 17
Depends on counters from: US-00.2
Feeds counters to: next monthly cycle, US-00-UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Effective ratio calculation/output | country × market × good | US-00.2 result | TO_TEST | 026 |
| Read keyed ratio entry | country × market × good | variable maps, scoped variables, or generated keys | TO_TEST | 007, 025 |
| Identify affected production sources/locations | producing country/source/location/market/good | US-00.1 country attribution + output checks | TO_TEST | 003-004, 029, 081 |
| Preferred modifier | location × good | good-specific local output | TO_TEST | 027 |
| Fallback modifier | location | local production efficiency | TO_TEST | 028 |
| Temporary location modifier | location | modifier effect | TO_TEST | 010 |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
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
Related US: US-09, US-00-UI, US-05.1
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Calculate `-min(max_penalty, effective_ratio × coefficient)`.
- Apply month N results only during month N+1 and replace the prior penalty monthly.
- Use the same producing-country/source attribution established by US-00.1 when selecting penalty targets.
- Do not silently switch to location ownership if it would penalize a different country from the one credited in the ledger.
- Prefer good-specific output; use local production efficiency only as the single accepted fallback.
- If no reliable modifier exists, calculate and display a theoretical-only penalty.
- Never mutate stock or `estate_taxable_income`.

## US-specific boundary checks

- [ ] The penalty uses effective, not raw, overproduction.
- [ ] It targets only the relevant country, market, good, and producing locations where exposure permits.
- [ ] The country credited with rejected production is the country whose eligible production sources receive the penalty.
- [ ] Fallback and theoretical-only modes are explicit.

## Acceptance criteria

- [ ] Zero effective overproduction yields zero penalty.
- [ ] Penalty magnitude is capped and uses configurable coefficients.
- [ ] N+1 application timing is deterministic.
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

Good-specific output modifiers and reliable producer-location identification are `TO_TEST`. The accepted no-exposure behavior is theoretical-only tracking, not an invented modifier.

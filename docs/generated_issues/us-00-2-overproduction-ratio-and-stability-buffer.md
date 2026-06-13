# US-00.2 — Overproduction Ratio and Stability Buffer

Labels: `blocked:engine-exposure`

## User Story

```txt
US-00.2 — Overproduction Ratio and Stability Buffer
```

As a player, I want rejected production converted into a stable ratio so negligible numerical variation does not trigger production penalties.

## Functional objective

Calculate clamped monthly overproduction and effective overproduction ratios per `country × market × good`, with a configurable default buffer of `0.01`.

## Runtime position

```txt
Monthly step: 15
Depends on counters from: US-00.1
Feeds counters to: US-00.3, US-00-UI
```

## Required scopes / values / effects

| Need | Scope | Candidate | Status | TECH-01 ID |
|---|---|---|---|---|
| Monthly produced/rejected ledger outputs | country × market × good | US-00.1 accumulated transaction totals | CONFIRMED | 024, internal |
| Read keyed ledger entries | country × market × good | variable maps, scoped variables, or generated keys | TO_TEST | 007, 025 |
| Safe division and clamp | scripted value/effect | arithmetic operators | TO_TEST | 026 |
| Configurable buffer | ModeU5 | scripted/config value | CONFIRMED | internal |

## Files expected to change

```txt
in_game/common/scripted_values/
in_game/common/scripted_effects/
in_game/common/on_actions/
in_game/events/
docs/technical/TECH-01_engine_exposure_matrix.md
docs/tests/
```

## Dependencies

```txt
Depends on: US-00.1, TECH-01
Blocks: US-00.3
Related US: EPIC US-00, US-00-UI
```

## Implementation rules

- Follow `AGENTS.md` and `CLAUDE.md`.
- Return zero when produced quantity is non-positive.
- Clamp raw ratio to `[0, 1]`.
- Calculate effective ratio as `max(0, raw_ratio - buffer)`.
- Keep the buffer configurable and visible in debug.
- Do not mutate stock or ledger source counters.

## US-specific boundary checks

- [ ] The buffer affects only effective overproduction and its penalty.
- [ ] Rejected quantity and void wealth remain fully tracked below the buffer.

## Acceptance criteria

- [ ] Zero production yields a zero ratio without division errors.
- [ ] Ratios cannot fall below zero or exceed one.
- [ ] Rejection at or below the buffer yields zero effective overproduction.
- [ ] Rejection above the buffer subtracts exactly the configured buffer.
- [ ] Results remain isolated by country, market, and good.
- [ ] Debug shows produced, rejected, raw ratio, buffer, and effective ratio.
- [ ] TECH-01 and test evidence are updated.

## Manual test scenario

### Setup

```txt
Case A: produced 100, rejected 0.5, buffer 0.01
Case B: produced 100, rejected 20, buffer 0.01
Case C: produced 0, rejected 10
```

### Expected result

```txt
Case A effective ratio: 0
Case B raw ratio: 0.20; effective ratio: 0.19
Case C raw/effective ratio: 0 with no error
```

## Known limitations

EU5 scripted arithmetic and keyed-ledger storage operations remain `TO_TEST`; the US-00.1 monthly accumulation/reset lifecycle is an internal contract. No gameplay dependency may ship until required engine primitives are confirmed or one fallback is accepted.

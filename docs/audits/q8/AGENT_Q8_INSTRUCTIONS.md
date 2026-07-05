# AGENT instructions — Q8 optimisation track

Use this document as the coding-agent prompt skeleton for the Q8 master PR stack.

## Mission

You are working after PR126 has been merged into `main`. Your job is to turn Q8 from future optimisation notes into small, stacked, reviewable, and testable PRs.

Do not start by rewriting runtime orchestration. Start by auditing current `main`, proving which optimisations are still needed, and adding debug-only probes where exposure or performance benefit is uncertain.

## Required reading order

```txt
1. AGENTS.md
2. docs/audits/q8/README.md
3. docs/audits/q8/Q8_0_POST_PR126_BASELINE_AUDIT.md
4. docs/audits/q8/Q8_IMPLEMENTATION_BACKLOG.md
5. docs/audits/pr126/Q5_flux_logique_global.md
6. docs/audits/pr126/Q5.1_current_global_flow.md
7. docs/audits/pr126/Q8_future_optimisations.md
8. docs/audits/pr126/Q8_F9_location_cache_rolling_verification.md
9. docs/audits/pr126/Q8_F9_TECH01_storage_compatibility.md
10. docs/audits/pr126/Q8_F9C_market_sliced_verifier.md
11. docs/technical/PERSISTENT_STATE_AUDIT.md
12. docs/technical/TECH-01_engine_exposure_matrix.md
```

## Work rules

```txt
1. One PR = one testable layer.
2. Prefer audit/probe PRs before live runtime changes.
3. Do not add broad monthly scans unless the PR proves they replace more expensive repeated work.
4. Do not use runtime-built map names, runtime-built helper names, nested maps, or rich map values.
5. Do not mutate stock from probes or verifiers.
6. Do not call market-local stock mutation once per country present.
7. Do not use `every_trade` outside confirmed country scope.
8. Do not rely on market-scope variables unless TECH-01 confirms support.
9. Do not fuse US-10 into the US-00 pass if that breaks the all-present-countries US-00 before any US-10 invariant.
10. Every new persistent map/list family must be documented and accepted by `tools/audit_modeu5_persistent_state.sh`.
11. Every stacked PR must include a Q1-Q5 actualisation check: update affected Q1-Q5 documents directly when the change materially changes their contract, or add an explicit note explaining why each Q1-Q5 document is not affected.
```

## Branch naming

Use short branch names that show the Q8 layer:

```txt
audit/q8-baseline
audit/q8-us10-gating
probe/q8-f9c-market-slicing
feature/q8-profile-counter-gates
feature/q8-capacity-pool-stamp
feature/q8-dirty-derived-caches
probe/q8-global-market-pass
```

## PR body template

```md
## Summary

This PR implements / audits Q8.<n>: <name>.

## Scope

- <one layer only>
- <files touched>
- <runtime behaviour changed? yes/no>

## Q1-Q5 actualisation

State which inherited PR126 audit documents are affected:

```txt
Q1 architecture/files: <updated / not affected + why>
Q2 cache system: <updated / not affected + why>
Q3 redundancy/code generation: <updated / not affected + why>
Q4 loops/performance: <updated / not affected + why>
Q5 global flow: <updated / not affected + why>
```

If a contract changes materially, update the relevant Q1-Q5 source document or add a dedicated actualisation file in the stacked PR.

## Guardrails

- No stock mutation outside central operators.
- No runtime-built map/helper names.
- No market-scope variables unless confirmed.
- No broad monthly scan unless justified.

## Validation

Commands:

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_modeu5_persistent_state.sh
git diff --check
```

Runtime scenario, if applicable:

```txt
<event command>
<expected debug.log lines>
<expected PASS/PENDING/FAIL result>
```

## Known limitation

<state any unproven exposure, performance limit, or future follow-up>
```

## Validation-comment rule

Do not edit runtime validation into the PR body after the fact. Add a PR comment for each tested commit.

Each validation comment must include:

```txt
- commit SHA tested;
- branch / package provenance;
- commands or EU5 event run;
- relevant debug.log / error.log lines;
- tolerated warnings, if any;
- PASS / PENDING / FAIL decision.
```

## Stop conditions

Stop and document instead of implementing when:

```txt
- engine exposure is unconfirmed;
- the optimisation requires a broad global scan with no measured replacement benefit;
- the implementation would introduce a second source of truth;
- the implementation requires runtime-built map names;
- the implementation changes stock without a central operator;
- the implementation changes ordering between US-00, US-10, trade, decay, validation, or reset.
```

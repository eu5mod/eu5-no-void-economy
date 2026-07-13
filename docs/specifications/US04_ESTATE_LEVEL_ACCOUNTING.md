# US-04 Estate-Level Consumption Accounting

## Status

Design specification for a PR stacked on PR #69.

This branch does not claim that the required EU5 Estate demand exposure is already confirmed. Gameplay implementation remains blocked until the engine-exposure probe defined below succeeds.

## Objective

Replace the Pop-level accounting dependency in US-04 with an Estate-level accounting contract wherever EU5 exposes actual Estate consumption or requested demand by good.

The business requirement is not intrinsically:

```txt
Pop × good demand
```

The actual requirement is:

```txt
country × market × good × paying Estate
requested quantity
satisfied quantity
payment amount
```

A direct Estate-level endpoint is preferred over iterating Pops because the Estate is the final payer and because it avoids an expensive `every_pop` aggregation.

## Required granularity

Preferred engine exposure:

```txt
location × good × estate_type
```

Acceptable alternatives:

```txt
country × market × good × estate_type
Estate × market × good
Estate × country × market × good
```

The first probe must assess the location-level surface explicitly. Pops are
located, consumption is resolved at location level, and any country-market
accounting result is an aggregation of location facts.

The exposure must represent an actual requested or consumed quantity for a specific good. The following are not sufficient substitutes:

```txt
Estate tax base
Estate wealth or treasury
Estate satisfaction
Estate power
Estate population
Estate expenditure without a good dimension
market-wide total demand without Estate attribution
```

## Accounting model

For each `country × market × good` accounting cell:

```txt
estate_requested[e] = actual requested quantity for Estate e
requested_total      = sum(estate_requested[e])
available_stock      = ModeU5 country-market-good stock
satisfied_total      = min(requested_total, available_stock)
```

Satisfied quantity is allocated proportionally:

```txt
estate_share[e] = estate_requested[e] / requested_total
estate_satisfied[e] = satisfied_total × estate_share[e]
```

The stock mutation remains centralized:

```txt
modeu5_remove_stock(
    country,
    market,
    good,
    requested_total
)
```

No Estate-specific code may mutate stock variables directly.

## Payment model

Each Estate pays only for its satisfied quantity:

```txt
estate_payment[e] = estate_satisfied[e] × effective market price
```

The exact payment effect must use the already confirmed Estate financial mutation surface. Payment must not be charged on unsatisfied demand.

The implementation must preserve the invariant:

```txt
sum(estate_satisfied[e]) = actual stock removed
```

subject only to documented numeric precision behavior.

## Local Consumption Proxy Candidate

If EU5 does not expose direct Estate requested quantity by good, the next
candidate is not to allocate a market-level demand downward. It is to estimate
location-level Estate consumption directly from local consumption pressure:

```txt
location_estate_good_consumption =
  modeu5_us04_reconciliation_coefficient(location, good)
  × proxy_estate_size_at_location
```

Then the estimated request is summed before reconciliation:

```txt
country_market_estate_good_requested =
  sum(location_estate_good_consumption for owned locations in market)
```

This is a dynamic local-consumption proxy, not a static Estate split. It is
better than assigning everything to one fallback Estate because it uses the
location's actual Estate composition and local consumption pressure. It must
remain blocked for stock or gold mutation until probes confirm:

```txt
the ModeU5 coefficient remains `modeu5_us04_reconciliation_coefficient`,
  seeded at 1.20 and updated yearly by 1.01 / 1.00 / 0.99
how to derive proxy_estate_size_at_location safely
the units/scaling between coefficient × size and requested quantity
stable aggregation across locations in the market
```

`proxy_estate_size_at_location` may be derived from summed Pops of the matching
Estate only if the relevant Pop-size read is confirmed. Pop size is not accepted
as a demand proxy by itself; here it is only the size term in the ModeU5
coefficient formula.

## Annual demand adjustment

The existing US-04 annual adjustment remains a multiplier owned by ModeU5:

```txt
next_multiplier = current_multiplier × 0.99 / 1.00 / 1.01
```

The preferred Estate design applies the multiplier at the narrowest confirmed Estate-demand endpoint:

```txt
estate × country × market × good
```

If EU5 exposes Estate demand as read-only but does not permit direct modification, this PR may implement Estate-level stock accounting and payment while leaving vanilla demand adjustment blocked. It must not falsely claim completion of the full original US-04 demand-feedback requirement.

## Engine-exposure probe

The first implementation phase is a controlled probe, not production gameplay.

Candidate surfaces must be tested for at least two goods and at least two Estate types in one market with known demand composition.

The probe must establish:

```txt
1. The scope from which Estate requested demand is readable.
2. The syntax for selecting a good.
3. Whether the value is country-specific inside a shared market.
4. Whether the value changes causally when Estate composition or demand changes.
5. Whether the quantity reconciles with market demand or consumption.
6. Whether an Estate-specific multiplier or coefficient can affect the live request.
```

Each candidate must be recorded as:

```txt
syntax | probe scenario | observed result | decision
```

No candidate may enter production code until the result is causally confirmed.

## Preferred runtime flow

```txt
monthly country accounting owner
  -> every relevant market for country
    -> every active good
      -> every owned location in that market
        -> read location Estate requested quantities
        -> aggregate to country × market × good × Estate
    -> calculate total request
    -> call centralized stock removal once
    -> allocate actual removal across Estates
    -> charge Estates for satisfied shares
    -> persist diagnostic result
```

The implementation must not add:

```txt
every_pop
every_location followed by every_pop
one stock mutation per Estate
duplicate country-market-good stock removals
```

## Persistent state

ModeU5 may persist diagnostic and adjustment state using literal generated per-good adapters where required.

Conceptual state:

```txt
country.modeu5_country_market[market].estate_demand_multiplier_<good>_<estate>
country.modeu5_country_market[market].estate_requested_<good>_<estate>
country.modeu5_country_market[market].estate_satisfied_<good>_<estate>
country.modeu5_country_market[market].estate_payment_<good>_<estate>
```

Exact storage shape must follow the repository's confirmed variable-map and generated-adapter contracts. Parameterized map identifiers are prohibited.

Requested and satisfied quantities are accounting diagnostics, not a second source of truth. Country-market-good stock remains authoritative.

## Zero and missing-state behavior

```txt
missing multiplier -> 1
requested_total <= 0 -> no stock mutation and no Estate charge
available stock <= 0 -> satisfied_total = 0 and no Estate charge
missing Estate demand exposure -> block production path
```

The implementation must not substitute a static Estate split unless explicitly approved as the single fallback.

## Compatibility with PR #69

This PR is stacked on PR #69 and reuses its confirmed components:

```txt
annual multiplier arithmetic
ModeU5 endpoint/fallback behavior
market × good observed-current diagnostics
Pop-scope probe evidence
existing US-04 test and audit conventions
```

It changes the acquisition and payer-allocation design from:

```txt
Pop × good -> classify Pop by Estate -> aggregate
```

to:

```txt
direct Estate × good requested quantity
```

PR #69 remains the historical evidence branch for rejected Pop-demand syntax. This PR must not delete that evidence.

## TECH-01 changes required

Add or update entries for:

```txt
Estate requested demand by good
Estate consumed quantity by good
Estate demand at country × market granularity
Estate-specific demand multiplier/write surface
Estate payment mutation
Estate-level accounting iterator/scope links
```

Statuses must remain `TO_TEST` or `NOT_CONFIRMED` until runtime evidence is posted.

## Debug contract

For one selected `country × market × good` cell, emit:

```txt
ModeU5 US-04 ESTATE ACCOUNTING
country=<...>
market=<...>
location=<...>
good=<...>
location_requested_total=<...>
requested_total=<...>
stock_before=<...>
stock_removed=<...>
stock_after=<...>
<estate>_requested=<...>
<estate>_satisfied=<...>
<estate>_payment=<...>
unallocated_quantity=<...>
```

Healthy result:

```txt
unallocated_quantity = 0
sum estate satisfied = stock removed
stock before - stock after = stock removed
no Estate payment for unsatisfied quantity
```

## Test plan

### Static validation

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_modeu5_persistent_state.sh
python3 ./tools/validate_ci_static_contracts.py
git diff --check
```

### Runtime exposure test

1. Use a disposable campaign with at least two Estates represented in one country-market.
2. Select two goods with visibly different Pop/Estate demand profiles.
3. Run the Estate-demand read probe.
4. Change Estate composition, population composition, or demand conditions.
5. Run the probe again and verify a causal change.
6. If a write surface exists, apply a temporary Estate-good multiplier and verify live demand changes.
7. Review `error.log`, `game.log`, `system.log`, and `debug.log`.

### Accounting integration test

After exposure confirmation:

1. Seed deterministic ModeU5 stock for one country-market-good.
2. Record Estate requests and stock before mutation.
3. Run one accounting cycle.
4. Verify centralized stock removal occurs exactly once.
5. Verify proportional Estate allocation.
6. Verify each Estate pays only for satisfied quantity.
7. Verify aggregate reconciliation invariants.

## Acceptance criteria

### Exposure phase

- [ ] At least one Estate-demand-by-good read syntax is causally confirmed.
- [ ] Country attribution inside a shared market is confirmed.
- [ ] Estate attribution is confirmed.
- [ ] Requested quantity reconciles with an observable vanilla aggregate.
- [ ] TECH-01 is updated with evidence.

### Accounting phase

- [ ] No `every_pop` dependency remains in the production accounting path.
- [ ] One centralized stock removal occurs per country-market-good cell.
- [ ] Estate satisfied quantities sum to actual removed stock.
- [ ] Estates are charged only for satisfied quantities.
- [ ] Missing or zero demand produces no mutation.
- [ ] Persistent diagnostics are not used as stock sources of truth.
- [ ] Static and runtime validation pass.

### Full US-04 completion

- [ ] An Estate-level write/multiplier surface causally affects live demand; or
- [ ] the PR explicitly declares that only accounting/payment was completed and the demand-feedback requirement remains blocked.

## Non-goals

```txt
Replacing vanilla markets
Reconstructing full Pop household budgets
Static Estate-demand assumptions
Charging the country treasury instead of Estates
Creating separate Estate-owned stock ledgers
Changing stock source-of-truth rules
Adding a second demand fallback alongside Pop and Estate paths
```

## Decision rule

```txt
Direct Estate demand confirmed
  -> implement Estate-level accounting

Estate read confirmed, Estate write unavailable
  -> implement accounting/payment only; keep annual demand feedback blocked

Estate demand unavailable
  -> keep PR draft and blocked; do not revert to an invented static split
```

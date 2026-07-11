# US-04 injection matrix runtime result — 2026-07-11

## Source / install provenance

```txt
branch: 22-us-04-annual-local-pop-demand-adjustment
commit installed: 0946cb8de315d5d2483d2502dcdb7c973b821fcb
source_dirty: no
runtime mode: debug
installed_at_utc: 2026-07-11T13:53:10Z
```

Static validation before launch:

```txt
ModeU5 US-04 explicit additive syntax matrix validation passed
```

## Confirmed still passing

### US-04 annual business rule

```txt
base_multiplier=1.2000
wheat_multiplier=1.2120
beer_multiplier=1.1880
cloth_multiplier=1.2000
tools_multiplier=1.2000
annual counters reset to 0
```

Result:

```txt
ModeU5 US-04 RESULT pop_demand_adaptation PASS
```

### Production Pop → location endpoint

```txt
seeded=1.3700
missing=1.0000
uninitialized=1.0000
disabled=1.0000
```

Result:

```txt
ModeU5 US-04 ENDPOINT RESULT pop_scope_location_map PASS
```

Conclusion: the location coefficient reader and safe multiplier-1 fallback are confirmed.

## Injection matrix result

The matrix was started twice before the first delayed run finalized:

```txt
15:59:26 ENTERED scenario=us04_pop_demand_injection_matrix
15:59:47 ENTERED scenario=us04_pop_demand_injection_matrix
```

Therefore the first finalization reported:

```txt
pass=0 fail=8
```

and the overlapping second finalization accumulated on top of it:

```txt
pass=0 fail=16
```

The doubled count is a test-protocol artifact, not 16 independent candidates.

## Candidate classification

All eight explicit static/additive candidates failed with no target response:

```txt
id=01 syntax=plain_child good=wheat                    FAIL reason=no_target_response
id=02 syntax=inner_inject good=beer                    FAIL reason=no_target_response
id=03 syntax=inner_try_inject good=cloth               FAIL reason=no_target_response
id=04 syntax=inner_inject_or_create good=tools         FAIL reason=no_target_response
id=05 syntax=outer_try_inject good=fish                FAIL reason=no_target_response
id=06 syntax=outer_inject_or_create good=wine          FAIL reason=no_target_response
id=07 syntax=direct_global good=tea                    FAIL reason=no_target_response
id=08 syntax=direct_global_value_block good=coffee     FAIL reason=no_target_response
```

Candidate 01 additionally logged:

```txt
wheat delta=0.0000
```

## Interpretation

```txt
- The candidate files loaded sufficiently for the test session to run.
- No tested additive/static database-entry-mode shape affected vanilla pop_demand output.
- Direct global variable expressions did not help.
- Static additive mutation of pop_demand should be treated as rejected for this PR.
```

This does not invalidate:

```txt
- the annual 1.20 / 1.01 / 0.99 business rule;
- the Pop -> location coefficient reader;
- the observed-current demand target architecture.
```

## Architectural decision

The PR should pivot away from upstream vanilla `pop_demand` mutation and toward the observed-current demand target architecture:

```txt
observe current engine demand
  -> initialize ModeU5 current consumption target = observed × 1.20
  -> yearly target transition = current target × 0.99 / 1.00 / 1.01
  -> feed ModeU5 stock consumption from that target
```

Known feasible reader:

```txt
goods_demand_in_market(goods:<good>)
```

Open design choice:

```txt
market × good
```

versus:

```txt
country × market × good using a distribution rule
```

## Follow-up test hygiene

The matrix launcher should either:

```txt
- be run once only and allowed to finish four in-game days later;
```

or:

```txt
- gain an in-progress guard to prevent overlapping delayed runs.
```

Because the static mutation path is rejected, the guard is lower priority than the observed-current implementation.

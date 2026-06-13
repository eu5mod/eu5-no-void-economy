# #003 — Add TECH-01 engine exposure matrix

## Objective

Create a mandatory exposure matrix for all vanilla EU5 data, scope links, triggers, values, effects, modifiers, on_actions, iterators, and static file fields required by ModeU5.

## File to create

```txt
docs/technical/TECH-01_engine_exposure_matrix.md
```

## Required status values

```txt
TO_TEST
CONFIRMED
NOT_CONFIRMED
FALLBACK_ACCEPTED
OUT_OF_SCOPE
```

## Required sources to check

```txt
https://eu5.paradoxwikis.com/Scope_link
https://eu5.paradoxwikis.com/Variable
https://eu5.paradoxwikis.com/Trigger
https://eu5.paradoxwikis.com/Effect
https://eu5.paradoxwikis.com/Modifier_types
https://eu5.paradoxwikis.com/Building_modding
https://eu5.paradoxwikis.com/Goods_modding
local vanilla files
local script_docs output
error.log after test
```

## Required matrix coverage

TECH-01 must contain initial entries for:

```txt
Core iteration and scope handling
Core variables and variable maps
Monthly and yearly on_actions
Centralized stock effects
US-00.1 production ledger
US-00.2 ratio calculation
US-00.3 production penalty modifiers
US-00.4 good price and void wealth valuation
US-01 country stock
US-02 storage capacity
US-03 decay
US-04 local Pop demand and yearly counters
US-05 total Wealth and direct Economic Base formula hook
US-07 trade building static fields
US-08 RGO/building price static fields
US-09 Production Efficiency modifier
US-10 stock resolver scoring dependencies
US-10 war / embargo / market access / subject / market-owner checks
US-10 actual/desired vanilla trade quantity
US-13 horde and age checks
```

## Acceptance criteria

- [ ] TECH-01 exists.
- [ ] TECH-01 contains status definitions.
- [ ] TECH-01 contains required source list.
- [ ] TECH-01 contains initial entries for all required coverage areas.
- [ ] US-00.1 location-production aggregation exposure is explicitly listed.
- [ ] US-05 Wealth and direct formula-hook exposure are explicitly listed.
- [ ] US-10 no-intra-market-trade dependencies are explicitly listed.
- [ ] No gameplay implementation can depend on a `TO_TEST` or `NOT_CONFIRMED` item unless fallback is approved.

## Manual review checklist

- [ ] Are critical ModeU5 dependencies listed?
- [ ] Are US-00 good-specific production modifiers listed?
- [ ] Are US-05 slider dependencies listed?
- [ ] Are US-10 scoring and exclusion dependencies listed?
- [ ] Is US-10.2 vanilla per-trade quantity exposure listed?
- [ ] Are static balance dependencies listed?
- [ ] Are fallbacks single and explicit?

## Out of scope

```txt
implementing stock effects
adding gameplay logic
creating UI
verifying exposure without local files or script_docs
```

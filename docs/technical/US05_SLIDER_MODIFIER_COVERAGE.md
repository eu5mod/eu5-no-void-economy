# US-05 slider modifier coverage

## Per-expense architecture

Each expense family owns an independent target base and modifier:

```txt
expense_modifier = (expense_target_base / vanilla_denominator) - 1
```

The current shared vanilla denominator is:

```txt
Tax Base + Trade Income
```

The target base is not globally fixed. It may differ by expense family.

## Implemented first slice

| Expense family | Modifier type | Target base | Status |
|---|---|---|---|
| Court spending | `court_spending_cost_modifier` | `Wealth + Trade Income` | IMPLEMENTED / RUNTIME TO VERIFY |
| Diplomatic upkeep | `diplomatic_upkeep_modifier` | `Wealth + Trade Income` | IMPLEMENTED / RUNTIME TO VERIFY |

Although both formulas are currently identical, Court and Diplomatic use separate
script values, separate country modifiers, separate runtime sizes, and separate
diagnostics. Either target can therefore be tuned independently later.

## Example future expense-specific base

Food spending may use a different target base, for example:

```txt
food_target_base = population / 1000
food_modifier = (food_target_base / food_vanilla_denominator) - 1
```

This is an architectural example only. It is not implemented until all of the
following are confirmed:

```txt
country population endpoint and scale
food-spending modifier type
actual vanilla food denominator
modifier semantics and causal runtime behavior
```

Do not automatically reuse `Tax Base + Trade Income` as the denominator for Food
unless the vanilla cost formula is proven to use that base.

## Not implemented: visible candidate but unsafe until causal test

| Expense family | Candidate | Status | Missing proof |
|---|---|---|---|
| Stability investment | `stability_cost` | UNSAFE / NOT IMPLEMENTED | Must prove it scales the intended Stability Investment cost with compatible multiplicative semantics. |
| Diplomatic expected spending | `diplomatic_spending_cost` | UNSAFE / NOT IMPLEMENTED | Must isolate its relationship with `diplomatic_upkeep_modifier` to avoid double scaling. |

## Not implemented: missing suitable cost endpoint

No sufficiently specific, causally confirmed cost modifier and vanilla denominator
pair has yet been selected for:

```txt
Culture investment / cultural maintenance
Prestige investment or prestige-producing spending
Military spending
Fort spending
Subsidies
Minting
Food spending
Other economy sliders
```

Related modifiers such as `monthly_prestige`, `prestige_decay`,
`has_cultural_maintenance`, or AI target modifiers are not cost modifiers and
must not be used as substitutes.

## Promotion rule

A missing expense may be added only after a controlled test records:

```txt
candidate modifier type
vanilla denominator
proposed target base
baseline expense
known test modifier
expected expense
observed expense
unrelated expense controls
error.log result
```

The implementation must add one target-base endpoint and one reconciliation
modifier endpoint for that expense. Do not route new expenses through a global
shared ratio merely because another expense currently uses the same formula.

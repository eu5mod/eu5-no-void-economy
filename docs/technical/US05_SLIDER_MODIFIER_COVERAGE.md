# US-05 slider modifier coverage

## Implemented first slice

The monthly reconciliation ratio is applied only through these two approved
country modifier types:

| Expense family | Modifier type | Status | Reason |
|---|---|---|---|
| Court spending | `court_spending_cost_modifier` | IMPLEMENTED / RUNTIME TO VERIFY | Explicit cost modifier selected for the first safe implementation slice. |
| Diplomatic upkeep | `diplomatic_upkeep_modifier` | IMPLEMENTED / RUNTIME TO VERIFY | Documented country-level multiplicative upkeep modifier. |

Both receive exactly the same runtime size:

```txt
((Wealth + Trade Income) / (Tax Base + Trade Income)) - 1
```

## Not implemented: visible candidate but unsafe until causal test

| Expense family | Candidate | Status | Missing proof |
|---|---|---|---|
| Stability investment | `stability_cost` | UNSAFE / NOT IMPLEMENTED | The modifier exists, but the PR still needs proof that it scales the same Economic Base cost with the same `cost * (1 + modifier)` semantics and does not alter another Stability subsystem. |
| Diplomatic expected spending | `diplomatic_spending_cost` | UNSAFE / NOT IMPLEMENTED | The relationship between this value and `diplomatic_upkeep_modifier` must be isolated before applying both and risking double scaling. |

## Not implemented: missing suitable cost endpoint

No sufficiently specific, causally confirmed Economic-Base cost modifier has yet
been selected for:

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

A missing slider may be added only after a controlled test records:

```txt
candidate modifier type
baseline slider cost
known test modifier
expected cost
observed cost
unrelated expense controls
error.log result
```

Do not infer a cost endpoint from a similarly named outcome, availability, AI,
or monthly-change modifier.

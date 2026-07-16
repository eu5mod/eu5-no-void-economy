# US-00 production penalty market-saturation gate

## Objective

Apply the country production penalty only when the relevant good's total market stock is saturated.

This prevents the edge case where one country's production is rejected because its own country-market storage is full while the market as a whole still has free storage capacity and remains undersupplied.

## Required rule

For each `country × market × good` record:

```txt
market_stock = sum(country stock in market for good)
market_capacity = sum(country-market stock capacity for every country present in market)
market_saturated = market_capacity > 0 && market_stock >= market_capacity
```

The next-cycle production penalty may be negative only when:

```txt
effective_overproduction_ratio > 0
AND market_saturated = yes
```

Otherwise:

```txt
production_penalty = 0
```

## Integration point

The gate belongs immediately before or inside:

```txt
cbp_calculate_production_penalty_good_<good>
```

The implementation should reuse:

- the generated market aggregate for the good;
- `cbp_countries_present_in_market`;
- each country's `cbp_stock_cap_by_market` value for the current market.

The saturation comparison should tolerate only the project's existing numeric epsilon. It must not use one country's rejected production as a proxy for whole-market saturation.

## Acceptance scenarios

1. Country A is full, Country B has spare capacity, and total market stock is below total capacity: penalty `0`.
2. Country A rejected production and total market stock equals total market capacity: existing penalty formula applies.
3. Market capacity is zero or missing: fail closed with penalty `0`.
4. A previously stored penalty is cleared when the market is no longer saturated.
5. Existing overproduction, void-wealth, stock consistency, and monthly modifier lifecycle tests remain valid.

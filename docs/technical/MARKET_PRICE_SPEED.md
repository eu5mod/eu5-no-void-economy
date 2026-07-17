# Market price adjustment speed

The Rebalance Economy package doubles the monthly adjustment speed of market
goods prices:

```txt
NMarket.MONTHLY_PRICE_CHANGE = 0.10
Vanilla = 0.05
```

The engine interprets this define as the fraction of the remaining difference
between the current price and target price closed each month. CBP therefore
closes 10% of that gap instead of Vanilla's 5%; it does not multiply the price
itself by two.

This rule shares the package-owned `cbp_market_resource_balance_defines.txt`
file with `NMarket.FOOD_PRICE`, but the two values remain independent.
`NMarket.FOOD_PRICE_IMPACT_ON_PRICES` remains unchanged.

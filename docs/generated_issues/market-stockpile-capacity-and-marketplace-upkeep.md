# Market stockpile capacity and marketplace upkeep normalization

## Functional changes

- Disable `market_warehouse` through generated `country_potential = { always = no }`.
- Keep `Marketplace`, `Merchants Quarters`, and `Grand Marketplace` maintenance equal to the generated base Marketplace maintenance quantities.
- Apply vanilla `maximum_stockpile_capacity` at each market-center location (`market.location`).
- Size the location modifier from the sum of authoritative ModeU5 country x market capacity records for the selected market.

## Static generation contract

Building files under `packages/cbp_economy_rebalance/in_game/common/building_types` remain generated exact-path overrides. Do not hand-edit them. The shared Python transformer owns warehouse disabling and marketplace-chain maintenance normalization so regeneration preserves both changes.

## Runtime modifier contract

`modeu5_market_stockpile_capacity` is a location static modifier with a unit value:

```txt
maximum_stockpile_capacity = 1
```

`modeu5_refresh_market_center_stockpile_capacity` rebuilds the current market's country work list, sums each country's persisted `cbp_stock_cap_by_market` entry for that market, and applies the modifier to `scope:modeu5_market.location` with dynamic `size` equal to that sum.

The effect must be called after all country x market capacity records for the promoted market have been refreshed. It must be wired into the existing promoted-market capacity path rather than a second monthly dispatcher.

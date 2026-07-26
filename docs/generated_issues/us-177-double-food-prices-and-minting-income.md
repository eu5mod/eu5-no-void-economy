# US-177 — Double food prices and minting income

GitHub issue: #177

Package: `packages/cbp_economy_rebalance`

## Functional objective

When the Rebalance Economy package is loaded:

```txt
food valuation input = configured NMarket.FOOD_PRICE (default 0.3)
food supplied per unit of a food good = vanilla food field / configured divisor (default 3)
minting gross income = vanilla gross minting income * 2
```

When the package is absent, neither rule is loaded.

## Food-price endpoint and food-good set

Vanilla goods define food contribution through the numeric `food` field in
`in_game/common/goods/*.txt`. The authoritative US-177 food-good set is:

```txt
every vanilla good whose food field is greater than zero
```

The supported source fingerprint currently resolves to 14 goods:

```txt
beeswax
fish
fruit
fur
legumes
livestock
maize
millet
olives
potato
rice
wheat
wild_game
wool
```

The deterministic source manifest is generated at:

```txt
packages/cbp_economy_rebalance/cbp_generated/us177_food_goods_manifest.json
```

It records each food good, its vanilla `food` value, source file, source line,
source fingerprint, configured food price, production divisor, and generated
override hashes. Goods with no `food` field or `food = 0` are not food for this
feature. The generator creates exact-path goods overrides such as
`in_game/common/goods/03_food.txt` and divides only positive `food` fields.
It does not change `default_market_price` or other goods properties.

The price endpoint is the shared market define:

```txt
NMarket.FOOD_PRICE = 0.3
```

independently from the default food-production divisor `3`. Against vanilla
`FOOD_PRICE = 0.05`, the configured default is therefore x6 while each unit of
a food good contributes one third of its vanilla food quantity. US-177 does not alter
`default_market_price` on individual goods and does not alter non-food prices.

Local configuration:

```txt
MODEU5_US177_FOOD_PRICE=0.3
MODEU5_US177_FOOD_PRODUCTION_DIVISOR=3
```

## Exact minting-income rule

`minting_income_factor` is additive. A universal `+1.0` alone would not double
countries that already receive minting modifiers from laws, advances, reforms,
privileges, buildings, aspects, events, or static modifiers.

Vanilla gross factor:

```txt
1 + sum(vanilla minting_income_factor sources)
```

US-177 composes both of the following:

```txt
1. universal minting_income_factor = 1.0
2. every numeric vanilla minting_income_factor source * 2
```

Therefore:

```txt
1 + 1 + 2 * sum(vanilla sources)
= 2 * (1 + sum(vanilla sources))
```

This is an exact gross-income doubling, including negative vanilla sources.
Inflation fields, inflation thresholds, and unrelated monetary modifiers are not
scaled.

The legacy source audit currently records:

```txt
19 non-building source files / 26 minting assignments
1 composed building source / 2 minting assignments
20 source files / 28 minting assignments total
```

## Generation model

Generate the authoritative food-good manifest:

```bash
python3 tools/generate_us177_food_goods_manifest.py \
  --game-root "<EU5_INSTALL_DIR>/game" \
  --package-root packages/cbp_economy_rebalance \
  --food-price 0.3 \
  --food-production-divisor 3
```

Generate non-building minting overrides:

```bash
python3 tools/generate_us177_minting_overrides.py \
  --game-root "<EU5_INSTALL_DIR>/game" \
  --package-root packages/cbp_economy_rebalance \
  --multiplier 2
```

This legacy compiler scans Vanilla common data, events, static modifiers, and
auto modifiers. CBG consumes its change plan and:

- emits CBP-prefixed complete `REPLACE:<object>` entries for common databases
  and exact-path overrides only for event databases;
- preserves comments, BOM state, unrelated definitions, and numeric precision;
- fails on dynamic expressions, unsupported syntax, or ambiguous assignments;
- writes source hashes, object paths, old values, and new values to
  `cbp_generated/us177_minting_income_manifest.json`.

Building definitions are already owned by the composed US-07/US-09 building
adapter. Its legacy reference is handled by:

```bash
python3 tools/postprocess_us177_minting_building_overrides.py \
  --common-dir "<EU5_INSTALL_DIR>/game/in_game/common" \
  --package-common-dir packages/cbp_economy_rebalance/in_game/common \
  --multiplier 2
```

This prevents US-177 from replacing or discarding existing building output,
trade-capacity, estate-power, or maintenance changes.

## Validation

Run against the local supported EU5 installation:

```bash
python3 tools/validate_us177_food_minting_overrides.py \
  --game-root "<EU5_INSTALL_DIR>/game" \
  --package-root packages/cbp_economy_rebalance
```

The validator proves:

- package `FOOD_PRICE` equals the independently configured value and no other
  numeric market define is present in the US-177 file;
- the food-good manifest exactly matches every vanilla good with `food > 0`;
- generated `REPLACE:<good>` objects divide every positive Vanilla `food`
  value by the configured divisor without changing unrelated fields in those
  goods or redeclaring unrelated goods;
- the universal minting base is exactly `minting_income_factor = 1.0`;
- every supported vanilla numeric minting source is present once and doubled;
- building minting sources remain composed with the shared building generator;
- unsupported or dynamic minting expressions fail closed;
- inflation assignments are absent from the US-177 baseline.

The permanent CI fixture covers positive, negative, inline, commented, building,
and static-modifier minting sources. It also proves that `food = 0`, non-food
prices, unrelated modifiers, and inflation fields remain unchanged.

Engine exposure records 153–155 are documented in
`docs/technical/TECH-01_us177_engine_exposures.md` for later consolidation into
the main TECH-01 matrix when the stacked branch is flattened.

## Runtime validation still required

In a controlled campaign, compare the same country with and without Rebalance
Economy:

1. confirm the effective food valuation uses `0.3` rather than `0.05`;
2. confirm representative food goods provide one third of their vanilla food quantity;
3. compare gross minting income at the same minting input and confirm exact `2x`;
4. repeat with a country having a positive vanilla minting bonus;
5. repeat with a negative vanilla minting source;
6. verify inflation behavior is unchanged apart from any indirect consequence of
   the larger gross income;
7. inspect `error.log` for duplicate keys, unsupported tokens, or missing objects.

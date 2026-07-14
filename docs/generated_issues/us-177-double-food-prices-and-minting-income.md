# US-177 — Double food prices and minting income

GitHub issue: #177

Package: `packages/cbp_economy_rebalance`

## Functional objective

When the Rebalance Economy package is loaded:

```txt
food valuation input = vanilla NMarket.FOOD_PRICE * 2
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
and source fingerprint. Goods with no `food` field or `food = 0` are not food
for this feature. The list is generated rather than hand-maintained so a vanilla
patch changes the manifest and fails source validation.

The price endpoint is the shared market define:

```txt
NMarket.FOOD_PRICE = 0.1
```

against the supported vanilla value `0.05`. US-177 does not alter
`default_market_price` on individual goods and does not alter non-food prices.

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

The supported source audit currently contains:

```txt
19 non-building exact-path files / 26 minting assignments
1 composed building file / 2 minting assignments
20 exact-path files / 28 minting assignments total
```

## Generation model

Generate the authoritative food-good manifest:

```bash
python3 tools/generate_us177_food_goods_manifest.py \
  --game-root "<EU5_INSTALL_DIR>/game" \
  --package-root packages/cbp_economy_rebalance
```

Generate non-building minting overrides:

```bash
python3 tools/generate_us177_minting_overrides.py \
  --game-root "<EU5_INSTALL_DIR>/game" \
  --package-root packages/cbp_economy_rebalance \
  --multiplier 2
```

This generator scans vanilla common data, events, static modifiers, and auto
modifiers. It:

- creates only exact-path overrides for files containing numeric
  `minting_income_factor` assignments;
- preserves comments, BOM state, unrelated definitions, and numeric precision;
- fails on dynamic expressions, unsupported syntax, or ambiguous assignments;
- writes source hashes, object paths, old values, and new values to
  `cbp_generated/us177_minting_income_manifest.json`.

Building definitions are already owned by the composed US-07/US-09 exact-path
generator. They are handled by:

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

- package `FOOD_PRICE` is exactly `2 *` vanilla and no other numeric market define
  is present in the US-177 file;
- the food-good manifest exactly matches every vanilla good with `food > 0`;
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

1. confirm the effective food valuation uses `0.1` rather than `0.05`;
2. compare gross minting income at the same minting input and confirm exact `2x`;
3. repeat with a country having a positive vanilla minting bonus;
4. repeat with a negative vanilla minting source;
5. verify inflation behavior is unchanged apart from any indirect consequence of
   the larger gross income;
6. inspect `error.log` for duplicate keys, unsupported tokens, or missing objects.

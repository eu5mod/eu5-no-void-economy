# TECH-01 — US-177 engine exposure records

These records supplement `TECH-01_engine_exposure_matrix.md` for issue #177 and
use the next available identifiers after row 152.

| ID | US | Need | Scope | Confirmed candidate | Surface | Evidence | Status | Fallback / implementation | Notes |
|---:|---|---|---|---|---|---|---|---|---|
| 153 | US-177 | Set the shared food valuation input independently | loading-screen define database | configurable `NMarket.FOOD_PRICE`, default `0.3`, against supported vanilla `0.05` | static define | Local vanilla `loading_screen/common/defines/00_defines.txt`; issue #177 | CONFIRMED | Package-owned generated static override | The Rebalance Economy package changes only `FOOD_PRICE`; non-food market defines remain untouched. This value is independent from the food-production divisor. |
| 154 | US-177 | Identify food goods and reduce their food contribution independently | goods database object | numeric `food` field in `in_game/common/goods`; food good iff `food > 0`; generated value = vanilla / configured divisor, default `3` | static field / generated `REPLACE:<good>` object and manifest | Local vanilla `goods/readme.txt`; supported vanilla goods files; `us177_food_goods_manifest.json` | CONFIRMED_STATIC / TO_TEST_RUNTIME | Generate CBP-prefixed complete good replacements from Vanilla | The supported reference contains the positive-food goods in `03_food.txt`. The generator changes only positive `food` assignments, preserves each changed good definition, and leaves unrelated goods to Vanilla. |
| 155 | US-177 | Double total gross minting income despite additive bonuses | country modifier stack plus transformed Vanilla sources | universal `minting_income_factor = 1.0` plus every vanilla numeric `minting_income_factor` source multiplied by `2` | additive modifier / generated object or event overrides | Modifier docs; supported Vanilla source audit; US-177 manifests and CI fixture | FALLBACK_ACCEPTED | Exact algebraic composition: `1 + 1 + 2S = 2(1 + S)` | No multiplicative total-minting endpoint was confirmed. CBG emits complete CBP-prefixed `REPLACE:<object>` entries for common databases, retains exact-path output only for event databases, delegates building sources to the composed building family, and does not alter inflation fields. |

## Consolidation rule

When the stacked branch is consolidated into the main TECH-01 document, preserve
IDs 153–155 and remove this supplementary file rather than renumbering the
exposures.

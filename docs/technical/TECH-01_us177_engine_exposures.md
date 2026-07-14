# TECH-01 — US-177 engine exposure records

These records supplement `TECH-01_engine_exposure_matrix.md` for issue #177 and
use the next available identifiers after row 152.

| ID | US | Need | Scope | Confirmed candidate | Surface | Evidence | Status | Fallback / implementation | Notes |
|---:|---|---|---|---|---|---|---|---|---|
| 153 | US-177 | Set the shared food valuation input to exactly twice vanilla | loading-screen define database | `NMarket.FOOD_PRICE = 0.1` against supported vanilla `0.05` | static define | Local vanilla `loading_screen/common/defines/00_defines.txt`; issue #177 | CONFIRMED | Package-owned static override | The Rebalance Economy package changes only `FOOD_PRICE`; non-food market defines remain untouched. Local source comparison fails when the supported vanilla value changes. |
| 154 | US-177 | Identify the definitive set of goods treated as food | goods database object | numeric `food` field in `in_game/common/goods`; food good iff `food > 0` | static field / generated manifest | Local vanilla `goods/readme.txt`; supported vanilla goods files; `us177_food_goods_manifest.json` | CONFIRMED | Generate the list from vanilla rather than hard-code it | The supported reference contains 14 food goods. The manifest records every source file, line, value, and source fingerprint and must be regenerated after an EU5 patch. |
| 155 | US-177 | Double total gross minting income despite additive bonuses | country modifier stack plus exact-path static sources | universal `minting_income_factor = 1.0` plus every vanilla numeric `minting_income_factor` source multiplied by `2` | additive modifier / generated exact-path overrides | Modifier docs; supported vanilla source audit; US-177 manifests and CI fixture | FALLBACK_ACCEPTED | Exact algebraic composition: `1 + 1 + 2S = 2(1 + S)` | No multiplicative total-minting endpoint or base define was confirmed. The accepted fallback scales positive and negative vanilla sources, fails on dynamic expressions, composes building files with US-07/US-09, and does not alter inflation fields. |

## Consolidation rule

When the stacked branch is consolidated into the main TECH-01 document, preserve
IDs 153–155 and remove this supplementary file rather than renumbering the
exposures.

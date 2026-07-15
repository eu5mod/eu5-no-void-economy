# CBG Vanilla-Derived Generation Matrix

This matrix is the migration contract for files derived from installed Vanilla
sources during `generate_all.sh`. A family moves to CBG only after exact output
parity and ownership adoption are validated.

| Family | Runtime outputs | Edge-case authority | Materializer | Status |
|---|---|---|---|---|
| Central political values and profit margins | `main_menu/common/script_values/default_values.txt` | `centralizable_script_values()` from #188 | CBG #189 | Migrated |
| US-177 food production | Vanilla food-good source files, currently `in_game/common/goods/03_food.txt` | US-177 food classification and source-line discovery | CBG #189 | Migrated |
| Location static modifiers | `main_menu/common/static_modifiers/cbp_location.txt` | Dedicated block extraction; intentionally not an exact-path Vanilla copy | #188 | Planned adapter |
| US-09/US-08 buildings | 41 `in_game/common/building_types/*.txt` files | Building inheritance, maintenance categories, marketplace exceptions, stockpile comments | #188 | Planned composed migration |
| RGO prices and Pop promotion | `prices/00_hardcoded.txt`, `pop_types/00_default.txt` | Duplicate-key-safe exact paths and version-dependent promotion fields | #188 | Planned |
| US-177 minting | 23 exact-path files | Numeric-only matching, ordinal composition into building outputs | #188 | Planned composed migration |
| Political rewards outside central values | 177 event/common/main-menu overrides | Shared symbolic values, Honor exclusion, blocks, inline effects, parliament outcomes | #188 | Planned final migration |
| Dedicated FOOD_PRICE define | `loading_screen/common/defines/cbp_us177_food_price_defines.txt` | Dedicated CBP file, not a Vanilla copy | #188 renderer | Out of exact-copy migration |
| Dedicated CBP economic defines | `loading_screen/common/defines/cbp_economic_defines.txt` | Hand-owned dedicated override | Hand-authored | Out of migration |

The broad `cbp_pr188_balance.generated.json` remains experimental. Migration is
family-by-family; it must not publish `location.txt` or a complete
`00_defines.txt` merely because those files exist in Vanilla.

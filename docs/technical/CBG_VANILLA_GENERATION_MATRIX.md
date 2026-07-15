# CBG Vanilla-Derived Generation Matrix

This matrix is the migration contract for files derived from installed Vanilla
sources during `generate_all.sh`. A family moves to CBG only after exact output
parity and ownership adoption are validated.

All runtime families derived from Vanilla in `generate_all.sh` are now
materialized by CBG. Legacy #188 code may compile discovery manifests or staged
policy decisions, but it must not publish those runtime files to the package.

| Family | Runtime outputs | Edge-case authority | Materializer | Status |
|---|---|---|---|---|
| Central political values and profit margins | `main_menu/common/script_values/default_values.txt` | `centralizable_script_values()` from #188 | CBG #189 | Migrated |
| US-177 food production | Vanilla food-good source files, currently `in_game/common/goods/03_food.txt` | US-177 food classification and source-line discovery | CBG #189 | Migrated |
| Location static modifiers | `main_menu/common/static_modifiers/cbp_location.txt` | Dedicated block extraction; intentionally not an exact-path Vanilla copy | CBG #189 | Migrated |
| US-09/US-08 buildings | 41 `in_game/common/building_types/*.txt` files | #188 building-plan compiler: inheritance, maintenance categories, marketplace exceptions, stockpile comments | CBG #189 | Migrated; exact 41-file byte parity |
| RGO prices | `prices/00_hardcoded.txt` partial object override | Duplicate-key-safe selected-object output | CBG #189 | Migrated |
| Pop promotion | `pop_types/00_default.txt` | Version-dependent promotion-field discovery | CBG #189 | Migrated |
| US-177 minting | 23 exact-path files; 11 composed with political outputs and building occurrences delegated to buildings | #188 numeric-only discovery and unsupported-syntax guard | CBG #189 combined political/minting family | Migrated; exact byte parity |
| Political rewards outside central values | 177 event/common overrides; composed with minting into 189 unique outputs | #188 policy compiler: shared symbolic values, Honor exclusion, blocks, inline effects, parliament outcomes | CBG #189 | Migrated; exact 189-file byte parity |
| Dedicated FOOD_PRICE define | `loading_screen/common/defines/cbp_us177_food_price_defines.txt` | Dedicated CBP file, not a Vanilla copy | #188 renderer | Out of exact-copy migration |
| Dedicated CBP economic defines | `loading_screen/common/defines/cbp_economic_defines.txt` | Hand-owned dedicated override | Hand-authored | Out of migration |

The broad `cbp_pr188_balance.generated.json` remains experimental. Migration is
family-by-family; it must not publish `location.txt` or a complete
`00_defines.txt` merely because those files exist in Vanilla.

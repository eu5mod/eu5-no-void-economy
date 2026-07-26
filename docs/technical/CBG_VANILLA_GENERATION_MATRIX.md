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
| US-177 food production | `in_game/common/goods/cbp_03_food.txt` with selected complete `REPLACE:<good>` objects | US-177 food classification and source-line discovery | CBG #189 | Migrated; unrelated goods are not redeclared |
| Location static modifiers | Dedicated `main_menu/common/static_modifiers/cbp_location.txt` with selected `REPLACE:` objects | Dedicated field policy preserving each changed object while leaving unrelated Vanilla objects untouched | CBG #189 plus CBP database-entry adapter | Migrated; explicit replacement prevents duplicate static-modifier registration |
| US-09/US-08 buildings | Complete exact-path Vanilla source files for structural or nested production-method changes; sparse `cbp_inject_*.txt` files only for additive modifier deltas | #188 building-plan compiler: inheritance, maintenance categories, marketplace exceptions, stockpile cancellation | CBG #189 plus CBP building adapter | Migrated statically; clean runtime confirmation pending after complete `REPLACE:<building>` objects proved unsafe for reused nested method keys |
| RGO prices | `prices/cbp_00_hardcoded.txt` with selected `REPLACE:` objects | Duplicate-key-safe selected-object output that preserves the rest of the Vanilla price registry | CBG #189 | Migrated |
| Pop promotion | `pop_types/cbp_00_default.txt` with complete `REPLACE:<pop_type>` objects | Version-dependent promotion-field discovery | CBG #189 | Migrated |
| US-177 minting | CBP-prefixed complete `REPLACE:<object>` entries for flat common databases; exact-path files for event databases and common objects containing nested global registries; building occurrences delegated to the building family | #188 numeric-only discovery and unsupported-syntax guard | CBG #189 combined political/minting family | Migrated; object parity for flat registries, exact-source parity for nested registries, and byte parity for events |
| Political rewards outside central values | Complete `REPLACE:<object>` entries for flat common databases, exact-path nested-registry and event overrides, composed with minting into 189 outputs | #188 policy compiler: shared symbolic values, Honor exclusion, blocks, inline effects, parliament outcomes | CBG #189 | Migrated; gods use exact-path ownership because replacing a god did not purge Vanilla omen keys |
| Market/resource defines | `loading_screen/common/defines/cbp_market_resource_balance_defines.txt` | Dedicated CBP file, not a Vanilla copy | #188 renderer | FOOD_PRICE and monthly price speed share one generated owner |
| Dedicated CBP economic defines | `loading_screen/common/defines/cbp_economic_defines.txt` | Hand-owned dedicated override | Hand-authored | Out of migration |

The broad `cbp_pr188_balance.generated.json` remains experimental. Migration is
family-by-family. Location modifiers use explicit selected-object replacement;
a complete `00_defines.txt` must not be published merely because it exists in
Vanilla.

## Execution-role inventory

CBG ownership does not mean that every pre-CBG script is obsolete. The current
pipeline deliberately separates policy discovery from runtime publication:

| Tool family | Invoked by | Role | Publishes migrated runtime files? |
|---|---|---|---|
| `tools/cbg/community_balance_generator.py` | `generate_all.sh` and focused parity validators | Runtime materializer from Vanilla plus a CBG specification | Yes |
| `tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh` | `generate_all.sh` with all publication skip flags | Adapter helper compiling building discovery plans/manifests, inheritance, maintenance exceptions, and stockpile-comment policy | No |
| `generate_political_reward_overrides.py` | Political/minting adapter and validators | Discovers political targets and encodes exclusions/centralization | No |
| `generate_us177_food_goods_manifest.py` | `generate_all.sh` | Discovers the Vanilla food-good set and records US-177 policy | No food runtime output |
| `generate_us177_minting_overrides.py` | Political/minting adapter and validators | Discovers numeric minting targets and rejects unsupported syntax | No |
| `generate_cbp_location_overrides.sh` | Focused parity/fixture validation | Legacy reference renderer proving CBG byte parity | No live publication |
| `generate_cbp_defines_override.sh` | Fixture validation only | Complete-defines probe/reference renderer | No live publication; dedicated define files remain hand-owned |
| `postprocess_us177_minting_building_overrides.py` | Fixture/validator paths | Legacy composed-output oracle | No live publication |

Deletion requires proving that no adapter, parity validator, fixture, or policy
manifest consumes the tool. Low reference count or a legacy filename is not
sufficient evidence.

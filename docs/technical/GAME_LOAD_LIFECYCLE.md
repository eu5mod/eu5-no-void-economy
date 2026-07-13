# Game-Load Lifecycle Contract

ModeU5 uses startup markers to distinguish a new campaign from an existing save. These markers are written on `on_game_start` and repaired on `on_game_load` when they are missing.

The repair path is deliberately conservative: it makes the same loaded package state usable after loading a save, but it does not support arbitrary package-set changes mid-campaign.

## Scope

`on_game_start` remains responsible for new-campaign defaults:

- core package presence and version markers;
- generated local runtime mode defaults;
- CMM-backed ModeU5 main mode defaults;
- accounting persistence defaults;
- delayed CORE-02 stock initialization;
- CORE-04 location market-memory snapshot;
- optional companion package presence/version markers.

`on_game_load` is a repair surface:

- fill missing package/configuration markers;
- fill missing runtime/debug/default-mode markers;
- initialize stock only when the stock schema has not started;
- repair legacy/current-schema saves where `cbp_stock_schema_version` is current
  but `cbp_initialization_state` is missing or non-standard;
- repair the legacy current-schema failure code `21`, which was produced by an
  earlier dispatcher when only the readiness marker was missing;
- leave ready stock state untouched;
- leave other failed or incompatible stock states fail-closed;
- refresh CORE-04 location market memory only after stock runtime readiness;
- rewrite optional package markers for packages that are currently loaded.

`on_game_load` must not reset an already initialized campaign, force a fresh stock split, or clean up state from packages that were removed from the playset.

## Markers

| Area | Marker | Meaning |
|---|---|---|
| Core package | `cbp_core_package_loaded` | Core package is present in the current loaded mod set. |
| Core package | `cbp_core_package_version` | Core package schema/version marker. |
| Configuration repair | `cbp_configuration_load_repair_version` | Load-time configuration repair ran at least once. |
| Stock schema | `cbp_stock_schema_version` | Durable stock schema version. |
| Stock schema | `cbp_initialization_state` | Stock initialization state: ready, failed, in-progress, or missing. |
| Stock repair | `cbp_stock_load_repair_version` | Load-time stock lifecycle repair ran at least once. |
| US-04 | `cbp_us04_multiplier_initialization_version` | US-04 multiplier baseline has been seeded. |
| CORE-04 | `cbp_core04_market_memory_snapshot_version` | Location market-memory snapshot has been refreshed after runtime readiness. |
| Rebalance Economy | `cbp_economy_rebalance_loaded` | Rebalance Economy package is present. |
| Rebalance Economy | `cbp_economy_package_version` | Rebalance Economy package version marker. |
| Rebalance Trade | `cbp_trade_rebalance_loaded` | Rebalance Trade package is present. |
| Rebalance Trade | `cbp_trade_package_version` | Rebalance Trade package version marker. |
| Rebalance War | `cbp_war_rebalance_loaded` | Rebalance War package is present. |
| Rebalance War | `cbp_war_package_version` | Rebalance War package version marker. |

## Rules

1. Every persistent `on_game_start` marker needs a matching `on_game_load` repair path unless it is test-only.
2. Load repair must be idempotent.
3. Load repair may set missing defaults, but must not overwrite a valid player/runtime state.
4. Stock load repair delegates to `cbp_start_game_stock_initialization_dispatcher`; it must not call fresh opening-stock initialization directly.
5. If `cbp_stock_schema_version` already matches the current schema and the
   state is neither failed nor in-progress, load repair may restore
   `cbp_initialization_state = 2` without touching stock maps.
6. If the state is failed only because of legacy failure code `21`, load repair
   may clear that failure marker and restore `cbp_initialization_state = 2`
   without touching stock maps.
7. CORE-04 location market memory is refreshed only when `cbp_stock_runtime_ready_trigger = yes`.
8. Optional package load hooks repair package presence/version markers only for packages actually loaded in the current playset.

## Unsupported Case

Changing the package set after a campaign has started remains unsupported. If a package is added to or removed from an existing save, its static definitions and persistent markers may no longer describe the same world state. A future migration story may change that contract, but this load-repair layer is not that migration.

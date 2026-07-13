# Development Summary

## Table of Contents

- [Installation](#installation)
  - [`EU5_GAME_COMMON_DIR`](#eu5_game_common_dir)
  - [`MODEU5_MOD_DIR`](#cbp_mod_dir)
  - [`MODEU5_ENABLE_DEBUG_RUNTIME`](#cbp_enable_debug_runtime)
  - [US-09 Static Override Options](#us-09-static-override-options)
- [Deployments](#deployments)
- [Pre-test Command](#pre-test-command)
- [Testing Tools](#testing-tools)
  - [Summarize Tests](#summarize-tests)
  - [Focus on a Fresh Time Window](#focus-on-a-fresh-time-window)
  - [Focused Probe](#focused-probe)
- [Testing Events](#testing-events)
  - [Full Deterministic Revalidation](#full-deterministic-revalidation)
- [Current Flow Map](#current-flow-map)

---

## Installation

Clone the repository wherever you want to develop. The repository does not need to live inside the EU5 mod directory.

```bash
git clone https://github.com/eu5mod/eu5-no-void-economy.git
cd eu5-no-void-economy
```

Create your local environment file:

```bash
cp .cbp.local.env.template .cbp.local.env
```

Edit `.cbp.local.env` for your machine.

Minimal example:

```bash
# Path to the vanilla EU5 game common directory.
EU5_GAME_COMMON_DIR="/path/to/Europa Universalis V/game/in_game/common"

# Keep false for normal performance comparisons.
MODEU5_ENABLE_DEBUG_RUNTIME=false

# Optional local mod install target. If omitted, tools use the default Paradox user mod directory.
MODEU5_MOD_DIR="$HOME/Documents/Paradox Interactive/Europa Universalis V/mod"
```

Never commit `.cbp.local.env`. It can contain local install paths and developer-only runtime preferences.


### `EU5_GAME_COMMON_DIR`

Points to the vanilla EU5 `game/in_game/common` directory.

Use it when generators need to read vanilla static files, for example goods, prices, or building definitions.

Example:

```bash
EU5_GAME_COMMON_DIR="/Users/<you>/Library/Application Support/Steam/steamapps/common/Europa Universalis V/game/in_game/common"
```

If this path is missing, generators that need vanilla source data should either use safe defaults or skip the optional output. Do not hard-code personal paths in scripts or generated files.

### `MODEU5_MOD_DIR`

Optional install target for the local ModeU5 package set. Use it when the development repository is outside the EU5 user mod directory.

Example:
```bash
MODEU5_MOD_DIR="$HOME/Documents/Paradox Interactive/Europa Universalis V/mod"
```

### `MODEU5_ENABLE_DEBUG_RUNTIME`

Allow you to generate a **verbodse audit trail** during your game. It overrite the CMM logging option. **⚠️ increase your monthly thick by 5 seconds**.

### US-09 static override options

Overide default production methods. You should not have to touch it.

## Deployments

Regenerate every local generated artifact:

```bash
./tools/generate_all.sh
```

## Pre-test command (recommanded)
```
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
./tools/audit_cbp_persistent_state.sh
git diff --check
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Testing tools 

### Summarize tests

```bash
./tools/summarize_test_cbp_logs.sh
```

### Focus on a fresh time window:

```bash
./tools/summarize_test_cbp_logs.sh --since 16:15:00
```

### For a focused probe

```bash
./tools/summarize_test_cbp_logs.sh --expected none
```

⚠️ PR validation comments should include the exact commit SHA, the commands run, the console events run, and the relevant PASS/FAIL log markers.

## Testing events

### Full deterministic revalidation:

```txt
event cbp_revalidate_debug.1
```

## Current flow map

```mermaid
flowchart TD
    subgraph LOOP_COUNTRY["Loop: monthly_country_pulse / current country"]
        A["monthly_country_pulse"] --> B["cbp_run_monthly_stock_cycle"]
        B --> P0["performance / relevance preparation"]
        P0 --> P1["current-country capacity refresh"]
        P1 --> P2["monthly market seen registry"]
        P2 --> L0["cbp_run_monthly_promoted_market_local_cycle"]

        subgraph LOOP_MARKET_CENTER["Loop: every_market_center_in_country"]
            L0 --> L1["prepare market runtime accounting mode"]
            L1 --> L2{"market runtime mode"}
            L2 -->|detailed| L3["cbp_run_promoted_market_live_local_branch_market_all_goods"]

            subgraph LOOP_MARKET_LOC["Loop: every_location_in_market"]
                L3 --> M0["rebuild countries_present_in_market"]
            end

            subgraph LOOP_COUNTRIES_CAP_US00["Loop: countries_present_in_market / fused capacity + US-00"]
                M0 --> D1["refresh country-market capacity"]
                D1 --> U1["cbp_pr71_process_us00_monthly_market_active_goods"]
                U1 --> U2["generated per-good US-00 active-good guard"]
                U2 --> U3{"produced or previous US-00 state?"}
                U3 -->|yes| U4["heavy US-00 helper"]
                U3 -. no .-> U5["skip heavy US-00 helper"]
            end

            subgraph LOOP_COUNTRIES_US10["Loop: countries_present_in_market / US-10 pass"]
                U4 --> S0["cbp_pr71_process_us10_monthly_market_pending_goods"]
                U5 --> S0
                S0 --> S1["generated per-good US-10 pending wrapper"]
                S1 --> S2{"pending same-market request?"}
                S2 -->|yes| S3["heavy US-10 helper"]
                S2 -. no .-> S4["skip heavy US-10 helper"]
            end

            S3 --> LEND["record local market processed"]
            S4 --> LEND
            L2 -->|vanilla fallback| F1["record fallback / no ModeU5 mutation"]
            L2 -->|blocked| F2["record blocked"]
        end

        LEND --> T0["cbp_run_monthly_country_trade_owner_cycle"]
        F1 --> T0
        F2 --> T0
        T0 --> T1["country-scope every_trade / inter-market only"]
        T1 --> R0["optional audit reconciliation"]
    end

    subgraph DIRTY_CACHE["Q8.5 dirty market-country cache scheduling"]
        D0["topology / lifecycle producer"] --> D2["cbp_mark_market_country_cache_dirty"]
        D2 --> D3["cbp_market_country_cache_dirty_markets"]
        D3 --> D4["cbp_repair_dirty_market_country_caches_if_needed"]
        D4 --> D5["cbp_rebuild_countries_present_in_market for dirty markets"]
    end

    subgraph Q86["Q8.6 debug/audit market-sliced verifier"]
        V0["cbp_run_market_sliced_verifier_candidates"] --> V1["build candidate market slice"]
        D3 -. copy only .-> V1
        P2 -. promoted/current-cycle markets .-> V1
        V1 --> V2["cbp_market_sliced_verifier_candidate_markets"]
        V2 --> V3["for each candidate market"]
        V3 --> V4["cbp_rebuild_countries_present_in_market"]
        V4 --> V5["record pass/fail counters"]
    end
```


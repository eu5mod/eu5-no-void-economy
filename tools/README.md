# Tools

## Community balance generation

[`cbg/`](cbg/) is the standalone, reusable Community Balance Generator.
`cbg/community_balance_generator.py` composes declarative balance specifications
from multiple mods into one audited exact-path compatibility mod. See
`docs/technical/COMMUNITY_BALANCE_GENERATOR.md` and
`tools/cbg/examples/community_balance_spec.example.json`.

## Local configuration

Copy the local configuration template once:

```bash
cp .cbp.local.env.template .cbp.local.env
```

Then edit `.cbp.local.env` with your local EU5 install path and local runtime preferences:

```bash
EU5_GAME_COMMON_DIR="<EU5_INSTALL_DIR>/game/in_game/common"
MODEU5_ENABLE_DEBUG_RUNTIME=false
MODEU5_US09_BONUS_PERCENT=5
```

The real `.cbp.local.env` file is ignored by Git. Do not commit personal
install paths.

`generate_all.sh` derives the vanilla location-static-modifier source from
`EU5_GAME_COMMON_DIR`. `EU5_GAME_LOCATION_STATIC_MODIFIERS_FILE` may override
that path. `generate_cbp_location_overrides.sh` copies only changed Vanilla
objects into the dedicated `cbp_location.txt` output and marks them `REPLACE:`,
so unrelated Vanilla balance changes remain untouched.

`MODEU5_ENABLE_DEBUG_RUNTIME` controls ModeU5 debug behaviour independently from
the EU5 engine `--debug_mode` launch argument:

```txt
false = generated local runtime config enters cbp_runtime_mode_normal
true  = generated local runtime config enters cbp_runtime_mode_debug
```

Use `false` when comparing performance with normal users. Use `true` only when
you want ModeU5 debug captures and PR7.1 metrics during local testing.

## Generated stock adapters

## Generator and validator conventions

ModeU5 generators follow the shared model documented in:

```txt
docs/technical/GENERATOR_AND_VALIDATOR_MODEL.md
```

Short version:

- `tools/cbp_goods.sh` is the single good registry.
- per-good generators load it through `tools/cbp_tool_lib.sh`;
- repeated generated blocks should live in `tools/templates/`;
- `tools/validate_generators.sh` enforces the convention and is called by
  `tools/validate_module_packages.sh`.

Do not add a new private `goods=(...)` list to a generator. Do not hand-build a
large repeated EU5 block in shell when a small template would make the shape
reviewable.

Regenerate every local generated artifact:

```bash
./tools/generate_all.sh
```

The aggregate generator currently regenerates the local runtime config, the
literal per-good EU5 persistence adapters, and optional generated-balance
scaffolds when their script exists on the current branch and the required
vanilla source path is configured.

Generated local runtime config is written to:

```txt
in_game/common/scripted_effects/cbp_local_runtime_config_generated.txt
```

It is ignored by Git and generated from `.cbp.local.env`. Do not edit it
manually.

Any new generated text artifact should follow the `cbp_*_generated.txt` or
`cbp_*_generated_l_english.yml` naming convention so it is ignored by Git and
caught by the generated-file validation guard.

Regenerate only the local runtime config:

```bash
bash ./tools/generate_local_runtime_config.sh
```

Regenerate only the stock adapters:

```bash
./tools/generate_stock_good_helpers.sh
```

The shell only expands
`tools/templates/cbp_stock_good_adapter.template.txt`. Map access remains EU5
script in that template; shared validation and arithmetic remain in
`cbp_stock_effects.txt`.

The generated adapters also contain the literal per-good US-11 dirty-list
names and dispatch glue. Dirty-record policy, cycle guards, reconciliation
counters, and repair behavior remain in shared EU5 scripted effects. The shell
contains enumeration only, not stock or reconciliation business rules.

Generate static good transport-cost helpers:

```bash
./tools/generate_good_transport_helpers.sh
```

`./tools/generate_all.sh` runs this generator automatically. When
`EU5_GAME_COMMON_DIR` points to vanilla `game/in_game/common`, the generator
reads `common/goods/*` and emits one helper per good into:

```txt
in_game/common/scripted_effects/cbp_transport_cost_generated.txt
```

The helpers convert a known trade-capacity-like volume into an estimated goods
quantity:

```txt
cbp_computed_goods_quantity = capacity_volume / static transport_cost
```

This is a diagnostic capacity-to-quantity conversion, not exact vanilla trade
quantity. If the vanilla source path is unavailable, safe default helpers are
generated with `transport_cost = 1` so runtime references fail closed instead
of calling missing effects.

Do not edit
`in_game/common/scripted_effects/cbp_stock_goods_generated.txt` manually.
The generated output is ignored by Git and must not be committed. The same rule
applies to `cbp_transport_cost_generated.txt` and
`cbp_local_runtime_config_generated.txt`. After changing the template,
goods registry, local-runtime generator, or transport-cost generator, run
`./tools/generate_all.sh` and then `./tools/validate_module_packages.sh`;
generation must be idempotent and no physical map identifier may retain `$`.

Audit the intentional generated per-good loops:

```bash
./tools/audit_cbp_per_good_loops.sh
```

This audit documents the remaining legitimate per-good stock, US-00, CORE-02,
US-10, and US-11 helpers while failing if shared US-02 capacity refresh helpers
return to generated per-good adapters. It allows `traded_in_market:<good>` only
inside the generated US-10 monthly trade-signal guard.

Audit the structured persistent state surface:

```bash
./tools/audit_cbp_persistent_state.sh
```

This audit classifies ModeU5 persistent variable maps and variable lists. It
fails when a new map/list family appears without an entry in
`docs/technical/PERSISTENT_STATE_AUDIT.md`, and it blocks accidental UI shadow
maps until a UI story explicitly approves them.

Normalize and validate CMM value-link quoting:

```bash
./tools/normalize_cmm_value_links.sh --write
./tools/normalize_cmm_value_links.sh --check
```

CMM setting reads such as `variable_map(cmm|flag:<setting>)` must be quoted
when used as value links:

```txt
"variable_map(cmm|flag:<setting>)"
```

The unquoted form is easy to reintroduce in generated or generated-adjacent
CMM files and can be parsed by EU5 as a bad trigger instead of a value
expression. The generated-file workflow runs the check mode in CI.

Validate scripted-test assertion safety:

```bash
./tools/validate_cbp_script_safety.sh
```

This check fails on direct variable-to-variable comparisons such as
`var:foo > var:bar`. For deterministic tests, initialize the metric first,
snapshot it into a temporary `scope:` value, and compare the `scope:` values.
The package validator runs this check automatically so the PR126-style
unset-variable assertion regression is caught before EU5 emits script-system
errors.

The same generator also writes the US-00 per-good production-penalty static
modifiers to:

```txt
main_menu/common/static_modifiers/cbp_us00_modifiers_generated.txt
main_menu/localization/english/cbp_us00_static_modifiers_generated_l_english.yml
```

Those static modifiers are unit-sized location modifiers. Runtime code applies
the calculated penalty through `add_location_modifier size = <penalty>`, so the
static file must define `game_data.category = location` and must not hard-code a
fixed penalty value. The matching generated localization prevents EU5 from
printing placeholder `STATIC MODIFIER NAME ...` lines in `error.log`.

## US-09 / US-08 composed Economy static overrides

Generate the Economy package static overrides:

```bash
./tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh 5
```

The generator reads vanilla `game/in_game/common/building_types` and
`game/in_game/common/prices/00_hardcoded.txt`, then writes composed generated
output under:

```txt
tools/generated/us09_economy_overrides/common/building_types/
tools/generated/us09_economy_overrides/common/prices/
```

When run through `./tools/generate_all.sh`, CBG writes tracked, CBP-prefixed
Rebalance Economy overrides under:

```txt
packages/cbp_economy_rebalance/in_game/common/building_types/cbp_*.txt
packages/cbp_economy_rebalance/in_game/common/prices/
```

Structural building changes use complete `REPLACE:<building>` objects.
Modifier-only changes use sparse `cbp_inject_*.txt` files whose additive values
are calculated as `target - Vanilla`. Unchanged Vanilla buildings are not
copied into the mod.

The building override generator composes the approved static changes that share
the same vanilla files:

- US-09 output and trade-capacity compensation;
- US-09 trade-capacity compensation can use an independent
  `MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT`; if unset, it defaults to `15`;
- US-07 `trade_buildings.txt` `local_burghers_estate_power x 0.5`;
- US-08/US-05.3 building maintenance quantities multiplied by `0.7`;
- US-08/US-05.3 marketplace and other `trade_category` building maintenance
  quantities multiplied by `0.5`.

Pass the desired compensation percentage explicitly. Example:

```bash
./tools/cbg/adapters/cbp/helpers/compile_us09_economy_policy.sh 7.5 --common-dir "<EU5_INSTALL_DIR>/game/in_game/common"
MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT=15 ./tools/generate_all.sh
```

If `.cbp.local.env` defines `EU5_GAME_COMMON_DIR`, `--common-dir` is not
needed.

Do not reintroduce generated `zzzz_cbp_us09_*.txt` or other non-vanilla
filenames for loaded static overrides. They create duplicate keys instead of
replacing vanilla definitions. Do not edit generated package building files
manually, and do not edit installed vanilla files in place.

If no percentage is passed and the shell is interactive, the generator prompts
for one.

Generated US-09 files record only placeholder source labels such as
`<EU5_GAME_COMMON_DIR>/building_types/production_tools.txt`; never commit a
personal install path from the local machine.

When `EU5_GAME_COMMON_DIR` is configured, validate the maintenance composition
against the local vanilla source:

```bash
python3 tools/validate_us08_building_maintenance_overrides.py \
  --common-dir "$EU5_GAME_COMMON_DIR" \
  --package-common-dir packages/cbp_economy_rebalance/in_game/common \
  --trade-capacity-percent "${MODEU5_US09_TRADE_CAPACITY_BONUS_PERCENT:-15}" \
  --maintenance-multiplier 0.7 \
  --trade-building-maintenance-multiplier 0.5
```

## Recommended local deployment pipeline

Use the canonical developer command to generate, prove idempotence, validate,
install, verify, clear logs, and print the in-game test events:

```bash
./tools/dev_prepare_game.sh
```

Use `--target PATH` for a non-default local mod directory, `--keep-logs` when
preserving the current logs is intentional, or `--skip-idempotence` for a
faster explicitly non-canonical iteration. The script does not launch EU5 or
modify Git state.

Installation is a clean publication, not an incremental copy. Before copying
the first package, `install_local_packages.sh` removes and recreates every
managed `cbp_*` package directory and removes the known legacy `eu5voideco`
deployment. Its final mirror check fails if the deployed tree contains a stale
file that is absent from the source payload. It never removes the parent EU5
`mod` directory or unrelated mods.

To install an already generated and validated checkout without regenerating:

```bash
./tools/install_local_packages.sh --skip-generate
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Compact test-log summary

After running the broad in-game revalidation event:

```txt
event cbp_revalidate_debug.1
```

choose:

```txt
Revalidate main operations
```

The event chain runs the main deterministic scenarios with two in-game days
between each step and writes compact markers to `debug.log`:

```txt
ModeU5 TEST ENTERED scenario=<name>
ModeU5 TEST PASS scenario=<name>
ModeU5 TEST FAIL scenario=<name>
ModeU5 TEST BLOCKED scenario=<name> reason=<reason>
```

The broad chain includes the PERF-10/11/13 active-list repair metrics probe.
The PERF-12 market-value probe remains useful when retesting
`traded_in_market:<good>` exposure directly:

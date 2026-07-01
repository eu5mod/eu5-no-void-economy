# Tools

## Local configuration

Copy the local configuration template once:

```bash
cp .modeu5.local.env.template .modeu5.local.env
```

Then edit `.modeu5.local.env` with your local EU5 install path:

```bash
EU5_GAME_COMMON_DIR="<EU5_INSTALL_DIR>/game/in_game/common"
MODEU5_US09_BONUS_PERCENT=5
```

The real `.modeu5.local.env` file is ignored by Git. Do not commit personal
install paths.

## Generated stock adapters

Regenerate every local generated artifact:

```bash
./tools/generate_all.sh
```

The aggregate generator currently regenerates the literal per-good EU5
persistence adapters and will also run optional generated-balance scaffolds when
their script exists on the current branch and the required vanilla source path
is configured.

Any new generated text artifact should follow the `modeu5_*_generated.txt` or
`modeu5_*_generated_l_english.yml` naming convention so it is ignored by Git and
caught by the generated-file validation guard.

Regenerate only the stock adapters:

```bash
./tools/generate_stock_good_helpers.sh
```

The shell only expands
`tools/templates/modeu5_stock_good_adapter.template.txt`. Map access remains EU5
script in that template; shared validation and arithmetic remain in
`modeu5_stock_effects.txt`.

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
in_game/common/scripted_effects/modeu5_transport_cost_generated.txt
```

The helpers convert a known trade-capacity-like volume into an estimated goods
quantity:

```txt
modeu5_computed_goods_quantity = capacity_volume / static transport_cost
```

This is a diagnostic capacity-to-quantity conversion, not exact vanilla trade
quantity. If the vanilla source path is unavailable, safe default helpers are
generated with `transport_cost = 1` so runtime references fail closed instead
of calling missing effects.

Do not edit
`in_game/common/scripted_effects/modeu5_stock_goods_generated.txt` manually.
The generated output is ignored by Git and must not be committed. The same rule
applies to `modeu5_transport_cost_generated.txt`. After changing the template,
goods registry, or transport-cost generator, run `./tools/generate_all.sh` and then
`./tools/validate_module_packages.sh`; generation must be idempotent and no
physical map identifier may retain `$`.

Audit the intentional generated per-good loops:

```bash
./tools/audit_modeu5_per_good_loops.sh
```

This audit documents the remaining legitimate per-good stock, US-00, CORE-02,
US-10, and US-11 helpers while failing if shared US-02 capacity refresh helpers
return to generated per-good adapters. It allows `traded_in_market:<good>` only
inside the generated US-10 monthly trade-signal guard.

Audit the structured persistent state surface:

```bash
./tools/audit_modeu5_persistent_state.sh
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

The same generator also writes the US-00 per-good production-penalty static
modifiers to:

```txt
main_menu/common/static_modifiers/modeu5_us00_modifiers_generated.txt
main_menu/localization/english/modeu5_us00_static_modifiers_generated_l_english.yml
```

Those static modifiers are unit-sized location modifiers. Runtime code applies
the calculated penalty through `add_location_modifier size = <penalty>`, so the
static file must define `game_data.category = location` and must not hard-code a
fixed penalty value. The matching generated localization prevents EU5 from
printing placeholder `STATIC MODIFIER NAME ...` lines in `error.log`.

## US-09 economy override probe

Generate the US-09 static-override probe output:

```bash
./tools/generate_us09_economy_overrides.sh 5
```

The generator reads vanilla `game/in_game/common/building_types` and
`game/in_game/common/prices/00_hardcoded.txt`, then writes offline probe
output under:

```txt
tools/generated/us09_economy_overrides/common/building_types/
tools/generated/us09_economy_overrides/common/prices/
```

Pass the desired compensation percentage explicitly. Example:

```bash
./tools/generate_us09_economy_overrides.sh 7.5 --common-dir "<EU5_INSTALL_DIR>/game/in_game/common"
```

If `.modeu5.local.env` defines `EU5_GAME_COMMON_DIR`, `--common-dir` is not
needed.

Do not copy these files into the loaded Economy package as an implementation
until duplicate-key static override loading has a clean runtime proof. The
current engine log showed package-local duplicate `building_types` and `prices`
entries are not applied cleanly and create load noise.

For a local probe only, you can deliberately target the loaded package:

```bash
MODEU5_ENABLE_UNVERIFIED_US09_STATIC_OVERRIDES=1 ./tools/generate_all.sh
```

Do not edit generated `zzzz_modeu5_us09_*.txt` files manually. Do not edit
installed vanilla files in place.

If no percentage is passed and the shell is interactive, the generator prompts
for one.

Generated US-09 files record only placeholder source labels such as
`<EU5_GAME_COMMON_DIR>/building_types/production_tools.txt`; never commit a
personal install path from the local machine.

## Recommended local deployment pipeline

When you want to refresh the local mod install before testing:

```bash
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

## Compact test-log summary

After running the broad in-game revalidation event:

```txt
event modeu5_revalidate_debug.1
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

```txt
event modeu5_perf12_debug.1
```

Close EU5 and summarize only those lines:

```bash
./tools/summarize_modeu5_test_logs.sh
```

Use `--logs-dir PATH` or `MODEU5_LOG_DIR` when EU5 stores logs elsewhere. This
summary is the first-pass review artifact; inspect full logs only when the
summary reports `FAIL`, `BLOCKED`, or missing scenarios.

## Module packages

Validate the source package roots, including the testing-only package:

```bash
./tools/validate_module_packages.sh
```

Publish Core, the three optional gameplay companions, and the testing-only package as sibling local mods:

```bash
./tools/install_local_packages.sh
```

The installer runs `./tools/generate_all.sh` before publishing so ignored
generated artifacts are present in the installed local mod.

The installer also normalizes installed EU5-loaded `.txt`, `.yml`, and `.gui`
files to UTF-8 BOM. Keep source files readable in Git; use the installer and
`--check` to validate the package EU5 actually loads.

The installer writes `MODEU5_SOURCE.txt` into every installed package so the
branch and commit loaded by EU5 can be checked without guessing:

```bash
./tools/install_local_packages.sh --check
```

Use `--target PATH` when EU5 reads local mods from a different directory.
After installation, refresh the launcher and enable the four gameplay ModeU5 entries in
the recommended full-suite playset. Enable `No Void Economy Tests` only in a dedicated validation playset. If two `No Void Economy` entries appear,
disable the older single-package entry backed by the `eu5voideco` path to avoid
loading Core twice.

Also remove or disable any stale real installation directory that can shadow
the installed `modeu5_core`. `--check` and each package's
`MODEU5_SOURCE.txt` are the source of truth for the branch and commit EU5 will
load.

See `docs/technical/LOG_NOISE_HYGIENE.md` for the distinction between blocking
errors, removable ModeU5 load noise, and tolerated test-only dump assertions.

## Local logs

Close EU5, then truncate only `error.log` and `game.log` before a controlled
test:

```bash
./tools/clear_eu5_logs.sh
```

Preview the targeted files without changing them:

```bash
./tools/clear_eu5_logs.sh --dry-run
```

Use `--logs-dir PATH` or the `MODEU5_LOG_DIR` environment variable when EU5
stores logs elsewhere.

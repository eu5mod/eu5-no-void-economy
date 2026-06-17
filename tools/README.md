# Tools

## Generated stock adapters

Regenerate every local generated artifact:

```bash
./tools/generate_all.sh
```

The aggregate generator currently regenerates the literal per-good EU5
persistence adapters and will also run optional generated-balance scaffolds when
their script exists on the current branch.

Any new generated text artifact should follow the `modeu5_*_generated.txt`
naming convention so it is ignored by Git and caught by the generated-file
validation guard.

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

Do not edit
`in_game/common/scripted_effects/modeu5_stock_goods_generated.txt` manually.
The generated output is ignored by Git and must not be committed. After changing
the template or goods registry, run `./tools/generate_all.sh` and then
`./tools/validate_module_packages.sh`; generation must be idempotent and no
physical map identifier may retain `$`.

## US-09 economy overrides

Regenerate the Rebalance Economy static overrides for US-09:

```bash
./tools/generate_us09_economy_overrides.sh 5
```

The generator reads vanilla `game/in_game/common/building_types` and
`game/in_game/common/prices/00_hardcoded.txt`, then writes package-local
overrides under:

```txt
packages/modeu5_economy_rebalance/in_game/common/building_types/
packages/modeu5_economy_rebalance/in_game/common/prices/
```

Pass the desired compensation percentage explicitly. Example:

```bash
./tools/generate_us09_economy_overrides.sh 7.5
```

Do not edit generated `zzzz_modeu5_us09_*.txt` files manually. Do not edit
installed vanilla files in place.

If no percentage is passed and the shell is interactive, the generator prompts
for one.

## Recommended local deployment pipeline

When you want to refresh the local mod install before testing:

```bash
./tools/generate_stock_good_helpers.sh
./tools/generate_us09_economy_overrides.sh 5
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

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

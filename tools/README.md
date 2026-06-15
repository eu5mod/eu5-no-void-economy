# Tools

## Generated stock adapters

Regenerate the literal per-good EU5 persistence adapters:

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
After changing the template or goods registry, regenerate and run
`./tools/validate_module_packages.sh`; generation must be idempotent and no
physical map identifier may retain `$`.

## Module packages

Validate the four source package roots:

```bash
./tools/validate_module_packages.sh
```

Publish Core and the three optional companions as sibling local mods:

```bash
./tools/install_local_packages.sh
```

The installer writes `MODEU5_SOURCE.txt` into every installed package so the
branch and commit loaded by EU5 can be checked without guessing:

```bash
./tools/install_local_packages.sh --check
```

Use `--target PATH` when EU5 reads local mods from a different directory.
After installation, refresh the launcher and enable the four ModeU5 entries in
the recommended full-suite playset. If two `No Void Economy` entries appear,
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

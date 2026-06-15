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

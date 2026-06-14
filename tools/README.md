# Tools

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

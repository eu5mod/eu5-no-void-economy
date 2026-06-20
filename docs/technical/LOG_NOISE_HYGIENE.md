# ModeU5 Log Noise Hygiene

ModeU5 log review separates three categories:

```txt
blocking: script errors that change behavior or make a test result ambiguous
non-blocking mod noise: ModeU5 warnings/assertions that make review harder
vanilla/external noise: unrelated base-game or launcher messages
```

Non-blocking ModeU5 noise should be removed when it can be removed without
weakening deterministic tests. If a warning is intentionally tolerated, the PR
validation comment must name it explicitly and explain why it does not invalidate
the scenario.

## Encoding

EU5 warns when loaded script files are not UTF-8 BOM encoded. Source files in
this repository may remain plain UTF-8, but installed package files are
normalized by:

```bash
./tools/install_local_packages.sh
```

The installer prepends a UTF-8 BOM to installed `.txt`, `.yml`, and `.gui` files
that EU5 can load, excluding descriptors, metadata, and provenance files. The
check command fails if installed ModeU5 package files are still missing the BOM:

```bash
./tools/install_local_packages.sh --check
```

Do not manually add BOMs to every source file just to satisfy a local install.
Use the installer as the source of truth for the loaded package.

## Generated Static Modifier Localization

Generated US-00 production-penalty static modifiers must have generated
localization in the same generation pass. The generator writes:

```txt
main_menu/common/static_modifiers/modeu5_us00_modifiers_generated.txt
main_menu/localization/english/modeu5_us00_static_modifiers_generated_l_english.yml
```

The localization file defines `STATIC_MODIFIER_NAME_modeu5_<good>_production_penalty_modifier`
for every generated modifier. This prevents EU5 from emitting placeholder
`STATIC MODIFIER NAME ...` lines during load.

Both generated files are ignored by Git and regenerated locally through:

```bash
./tools/generate_all.sh
```

`./tools/validate_module_packages.sh` verifies that the generated modifier file
and its generated localization are present, synchronized, and untracked.

## Metadata

All loaded ModeU5 packages must have `.metadata/metadata.json` with an `id`.
Current packages use these IDs:

```txt
modeu5_core
modeu5_economy_rebalance
modeu5_trade_rebalance
modeu5_war_rebalance
modeu5_core_tests
```

If `error.log` contains a metadata read error mentioning the old bootstrap name
`ModeU5 Country Stocks Within Markets`, the likely cause is a stale launcher
entry or an old local install path still visible to EU5. Run:

```bash
./tools/install_local_packages.sh --check
```

Then remove or disable any stale local ModeU5 directory reported by the check or
visible in the launcher playset.

## Test Dumps

Logs are the source of truth for deterministic test results. Some test dumps use
dynamic values inside `debug_log` strings so the log records the actual values
read by the engine. Current EU5 builds can emit a non-blocking
`Tried to localize with localization disabled` assertion for those dynamic dump
strings while still writing the expected dump line.

Do not remove numeric dump lines solely to eliminate that assertion. Prefer to
keep the dump, classify the assertion as tolerated test-only noise in the PR
validation comment, and revisit only when a cleaner numeric logging primitive is
confirmed.

## Deprecated Helper Noise

Avoid wrappers that exist only to set temporary default scopes for generated
per-good dispatchers. EU5's static analyzer may report those saved scopes as
unset even if the runtime wrapper would set them. Prefer explicit calls to the
centralized operator with all required scopes and values.

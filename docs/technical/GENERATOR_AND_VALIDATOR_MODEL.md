# ModeU5 Generator And Validator Model

ModeU5 uses generated files because EU5 script requires literal identifiers for
many per-good effects, maps, modifiers, and GUI bindings. Generation is a
delivery mechanism, not a place to hide business rules.

## Source Of Truth

The canonical ModeU5 good registry is:

```txt
tools/modeu5_goods.sh
```

Per-good generators must load that registry through:

```bash
source "$repo_root/tools/modeu5_tool_lib.sh"
modeu5_load_goods_registry
goods=("${modeu5_goods[@]}")
```

Generators must not carry their own literal good arrays. If the ModeU5 good
surface changes, update `tools/modeu5_goods.sh` once and regenerate.

Static good metadata may be read from vanilla files when a local
`EU5_GAME_COMMON_DIR` is configured. If a vanilla source is unavailable,
generators must fail closed or emit safe defaults that are clearly marked in
the generated output. They must not invent runtime exposure that TECH-01 has
not confirmed.

## Template Rule

Generated EU5 script should come from explicit templates under:

```txt
tools/templates/
```

Use templates for repeated generated blocks, especially per-good blocks. The
generator may still contain orchestration, vanilla parsing, and file assembly,
but the generated script shape should be reviewable as a template.

Current template surface:

```txt
tools/templates/modeu5_stock_good_adapter.template.txt
tools/templates/modeu5_good_transport_helper.template.txt
tools/templates/modeu5_us10_stock_table_row.template.gui
tools/templates/modeu5_us10_market_production_good.template.txt
```

Templates use static placeholders:

```txt
__GOOD__
__STOCK_MAP__
__TRANSPORT_COST__
```

Render templates through:

```bash
modeu5_render_template_to_stdout "$template" "GOOD=$good"
```

The shared renderer fails if an unresolved `__TOKEN__` remains. This keeps
broken generated identifiers from silently reaching runtime.

## Shared Tooling

Common generator and validator helpers live in:

```txt
tools/modeu5_tool_lib.sh
```

This file owns:

- repository root discovery;
- local `.modeu5.local.env` loading;
- canonical good registry loading;
- template rendering;
- common file and pattern validation helpers.

Feature-specific scripts still own feature-specific parsing and policy. For
example, the US-09 offline override probe reads vanilla building files directly
because it is not a per-good stock generator and because duplicate-key loading
is still not confirmed.

## Validation Rule

Every generated artifact must be reproducible from source scripts and
templates. Validation must compare generated output against a fresh temporary
render, not rely on manual inspection.

The main package validator runs:

```bash
./tools/validate_generators.sh
```

That validator enforces:

- required templates exist;
- main generators use `tools/modeu5_tool_lib.sh`;
- per-good generators load `tools/modeu5_goods.sh`;
- no generator carries a private literal good list.

`./tools/validate_module_packages.sh` then regenerates temporary artifacts and
compares them with the local generated files used for packaging. If a generator
or template changes, run:

```bash
./tools/generate_all.sh
./tools/validate_module_packages.sh
```

## Design Intent

The goal is boring, auditable generation:

```txt
one good registry
one shared rendering helper
small templates for repeated blocks
feature scripts for feature-specific parsing
validators that enforce the convention
```

This avoids generator spaghetti while preserving the practical need for
literal per-good EU5 identifiers.

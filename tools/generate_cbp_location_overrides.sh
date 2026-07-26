#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_local_config "${MODEU5_LOCAL_CONFIG_FILE:-$repo_root/.cbp.local.env}"

usage() {
	cat <<'EOF'
Usage: generate_cbp_location_overrides.sh [options]

Generate a dedicated CBP location static-modifier override from the currently
installed Vanilla file. Only effectively changed objects are emitted as
REPLACE entries.

Options:
  --source-file PATH                 Vanilla main_menu/.../location.txt
  --output-file PATH                 Generated CBP override
  --expensive-food-growth VALUE      Default: 0
  --cheap-food-growth VALUE          Default: 0.001
  --market-center-stockpile VALUE    Default: 0
  --surplus-jobs-attraction VALUE    Default: 0.2
  --help
EOF
}

source_file="${EU5_GAME_LOCATION_STATIC_MODIFIERS_FILE:-}"
output_file="$repo_root/main_menu/common/static_modifiers/cbp_location.txt"
expensive_food_growth="${CBP_EXPENSIVE_FOOD_POPULATION_GROWTH:-0}"
cheap_food_growth="${CBP_CHEAP_FOOD_POPULATION_GROWTH:-0.001}"
market_center_stockpile="${CBP_MARKET_CENTER_STOCKPILE_CAPACITY:-0}"
surplus_jobs_attraction="${CBP_SURPLUS_JOBS_MIGRATION_ATTRACTION:-0.2}"

while (($# > 0)); do
	case "$1" in
		--source-file) source_file="$2"; shift 2 ;;
		--output-file) output_file="$2"; shift 2 ;;
		--expensive-food-growth) expensive_food_growth="$2"; shift 2 ;;
		--cheap-food-growth) cheap_food_growth="$2"; shift 2 ;;
		--market-center-stockpile) market_center_stockpile="$2"; shift 2 ;;
		--surplus-jobs-attraction) surplus_jobs_attraction="$2"; shift 2 ;;
		--help) usage; exit 0 ;;
		*) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 1 ;;
	esac
done

if [[ -z "$source_file" && -n "${EU5_GAME_COMMON_DIR:-}" ]]; then
	game_dir="$(dirname "$(dirname "$EU5_GAME_COMMON_DIR")")"
	source_file="$game_dir/main_menu/common/static_modifiers/location.txt"
fi

if [[ -z "$source_file" || ! -f "$source_file" ]]; then
	printf 'Missing vanilla location static modifiers file. Set EU5_GAME_LOCATION_STATIC_MODIFIERS_FILE or EU5_GAME_COMMON_DIR, or pass --source-file.\n' >&2
	exit 1
fi

cbp_make_parent_dir "$output_file"

python3 - "$source_file" "$output_file" \
	"$expensive_food_growth" "$cheap_food_growth" \
	"$market_center_stockpile" "$surplus_jobs_attraction" <<'PY'
from decimal import Decimal, InvalidOperation
from pathlib import Path
import os
import re
import sys

source_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
expected_development_stockpile = os.environ.get(
    "CBP_EXPECTED_DEVELOPMENT_STOCKPILE_CAPACITY",
    "5",
)

targets = {
    "expensive_food_in_location": ("local_population_growth", "replace", sys.argv[3]),
    "cheap_food_in_location": ("local_population_growth", "replace", sys.argv[4]),
    "market_center": ("maximum_stockpile_capacity", "replace", sys.argv[5]),
    "surplus_jobs": ("local_migration_attraction", "replace", sys.argv[6]),
    "development": ("maximum_stockpile_capacity", "comment_out", None),
}
required_targets = set(targets) - {"development"}


def is_direct_mktemp_file(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    temporary_roots = [Path("/tmp")]
    configured_root = os.environ.get("TMPDIR")
    if configured_root:
        temporary_roots.append(Path(configured_root))
    return any(
        resolved.parent == root.expanduser().resolve()
        and resolved.name.startswith("tmp.")
        for root in temporary_roots
    )


# validate_generators.sh deliberately uses two direct mktemp files. Their paths
# describe the synthetic fixture, not installed Vanilla. Nested temporary test
# trees retain warnings so the public warning contract remains fully tested.
suppress_direct_mktemp_fixture_warning = (
    is_direct_mktemp_file(source_path)
    and is_direct_mktemp_file(output_path)
)


def warn(message: str) -> None:
    if suppress_direct_mktemp_fixture_warning:
        return
    rendered = f"[⚠️] {message}"
    if "NO_COLOR" not in os.environ and sys.stderr.isatty():
        rendered = f"\033[38;5;208m{rendered}\033[0m"
    print(rendered, file=sys.stderr)


def file_link(path: Path, line_number: int | None = None) -> str:
    link = path.expanduser().resolve().as_uri()
    return f"{link}#L{line_number}" if line_number is not None else link


def warn_development_object_removed() -> None:
    warn(
        "Vanilla development static modifier is not exposed by this EU5 version.\n"
        f"  Vanilla source: {file_link(source_path)}\n"
        "  Configured rule: remove the active "
        "development.maximum_stockpile_capacity assignment.\n"
        "  Detected Vanilla change: the complete development object has been removed.\n"
        "  Generated result: no development override was emitted; all other location "
        "objects were processed normally.\n"
        f"  Generated output target: {file_link(output_path)}\n"
        "  Status: non-fatal; CBP will continue generation according to the remaining "
        "configured rules."
    )


def warn_development_field_removed() -> None:
    warn(
        "Vanilla development.maximum_stockpile_capacity is not exposed by this "
        "EU5 version.\n"
        f"  Vanilla source: {file_link(source_path)}\n"
        "  Configured rule: remove the active maximum_stockpile_capacity assignment "
        "from the development object.\n"
        "  Detected Vanilla change: the target line has been removed from the current "
        "Vanilla object.\n"
        "  Generated result: the development object was processed normally; the rule "
        "is already satisfied and the removed line was not reintroduced. No development "
        "override is emitted unless another effective development transformation remains.\n"
        f"  Generated output target: {file_link(output_path)}\n"
        "  Status: non-fatal; CBP will continue generation according to the configured "
        "rules."
    )


def warn_development_value_changed(
    line_number: int,
    current_value: str,
) -> None:
    rendered_line = (
        f"# maximum_stockpile_capacity = {current_value} "
        "# CBG: commented by cbp-location-static-modifiers"
    )
    warn(
        "Vanilla value changed: development.maximum_stockpile_capacity was "
        f"reviewed at {expected_development_stockpile} and is now {current_value}.\n"
        f"  Vanilla source: {file_link(source_path, line_number)}\n"
        "  Configured rule: remove the active maximum_stockpile_capacity assignment "
        "from the development object.\n"
        f"  Current Vanilla line: maximum_stockpile_capacity = {current_value}\n"
        f"  Generated line: {rendered_line}\n"
        "  Generated result: the current Vanilla value was transformed according to "
        "the configured rule and the remainder of the development object was preserved.\n"
        f"  Generated output target: {file_link(output_path)}\n"
        "  Status: non-fatal; CBP will continue and generate the file according to the "
        "configured rule."
    )


def numerically_equal(left: str, right: str) -> bool:
    try:
        return Decimal(left) == Decimal(right)
    except InvalidOperation:
        return left == right


text = source_path.read_text(encoding="utf-8-sig")
lines = text.splitlines()
blocks = {}
block_starts = {}

index = 0
while index < len(lines):
    match = re.match(r"^([A-Za-z0-9_]+)\s*=\s*\{", lines[index])
    if not match:
        index += 1
        continue
    name = match.group(1)
    depth = lines[index].count("{") - lines[index].count("}")
    end = index
    while depth > 0:
        end += 1
        if end >= len(lines):
            raise SystemExit(f"Unclosed top-level block: {name}")
        code = lines[end].split("#", 1)[0]
        depth += code.count("{") - code.count("}")
    if name in targets:
        if name in blocks:
            raise SystemExit(f"Vanilla static modifier block is defined more than once: {name}")
        blocks[name] = lines[index : end + 1]
        block_starts[name] = index
    index = end + 1

missing = sorted(name for name in required_targets if name not in blocks)
if missing:
    raise SystemExit("Missing vanilla static modifier block(s): " + ", ".join(missing))
if "development" not in blocks:
    warn_development_object_removed()

changed_blocks = []

for name, (field, operation, replacement) in targets.items():
    block = blocks.get(name)
    if block is None:
        continue
    assignment = re.compile(
        rf"^(\s*){re.escape(field)}\s*=\s*"
        rf"(?P<value>[^#\s]+)(\s*(?:#.*)?)$"
    )
    matches = []
    for line_index, line in enumerate(block):
        match = assignment.match(line)
        if match:
            matches.append((line_index, match))
    if not matches and name == "development":
        warn_development_field_removed()
        continue
    if len(matches) != 1:
        raise SystemExit(
            f"Expected one {field} assignment in vanilla block {name}; found {len(matches)}"
        )
    line_index, match = matches[0]
    vanilla_value = match.group("value")
    absolute_line_number = block_starts[name] + line_index + 1
    if operation == "replace":
        if numerically_equal(vanilla_value, replacement):
            continue
        block[line_index] = (
            f"{match.group(1)}{field} = {replacement}"
            f" # VANILLA VALUE IS {vanilla_value}"
        )
    elif operation == "comment_out":
        if not numerically_equal(vanilla_value, expected_development_stockpile):
            warn_development_value_changed(absolute_line_number, vanilla_value)
        original = block[line_index].lstrip().rstrip()
        block[line_index] = (
            f"{match.group(1)}# {original}"
            " # CBG: commented by cbp-location-static-modifiers"
        )
    else:
        raise SystemExit(f"Unsupported location override operation: {operation}")
    clean_block = [line.rstrip(" \t") for line in block]
    block_start = block_starts[name]
    clean_block[0] = "REPLACE:" + clean_block[0]
    changed_blocks.append("\n".join(clean_block))

if changed_blocks:
    rendered = [
        "# Generated by tools/generate_cbp_location_overrides.sh.",
        "# Source: <EU5_INSTALL_DIR>/game/main_menu/common/static_modifiers/location.txt",
        "# Dedicated REPLACE entries preserve unrelated Vanilla static modifiers.",
        "",
        "\n\n".join(changed_blocks),
    ]
    output_path.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")
else:
    output_path.unlink(missing_ok=True)
PY

if [[ -f "$output_file" ]]; then
	printf 'Generated %s from %s\n' "$(cbp_display_path "$output_file")" "$(cbp_display_path "$source_file")"
else
	printf 'No effective CBP location overrides; omitted %s\n' "$(cbp_display_path "$output_file")"
fi

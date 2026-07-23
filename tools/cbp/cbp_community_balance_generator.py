#!/usr/bin/env python3
"""Run CBG with CBP database-entry output modes.

The generic CBG engine remains responsible for mutation discovery, effective
change detection, ownership and manifests. This runner adds one CBP packaging
mode: ``replace_objects``. That mode renders only effectively changed top-level
objects, writes them to a dedicated ``cbp_``-prefixed file, and marks each
object with Europa Universalis V's ``REPLACE:`` database entry mode.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.cbg import community_balance_generator as cbg


REPLACE_OBJECTS = "replace_objects"
UNSUPPORTED_COMMON_DATABASES = {"defines", "on_actions"}
ENTRY_LINE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<name>[A-Za-z0-9_.:-]+)"
    r"(?P<tail>[ \t]*=[ \t]*\{.*)$"
)


def cbp_prefixed_path(relative: PurePosixPath) -> PurePosixPath:
    name = relative.name
    if not name.startswith("cbp_"):
        name = f"cbp_{name}"
    return relative.with_name(name)


def supports_replace_entries(relative: PurePosixPath) -> bool:
    parts = relative.parts
    try:
        common_index = parts.index("common")
    except ValueError:
        return False
    if common_index + 1 >= len(parts):
        return False
    return parts[common_index + 1] not in UNSUPPORTED_COMMON_DATABASES


def safe_relative(raw: str, label: str) -> PurePosixPath:
    relative = PurePosixPath(raw)
    if raw.startswith("/") or ".." in relative.parts:
        raise ValueError(f"{label} must be a safe relative path")
    return relative


def prepare_spec(
    payload: dict[str, Any],
    source: Path,
) -> tuple[
    dict[str, Any],
    set[PurePosixPath],
    dict[PurePosixPath, PurePosixPath],
]:
    prepared = dict(payload)
    transformations: list[dict[str, Any]] = []
    replace_outputs: set[PurePosixPath] = set()
    replace_sources: dict[PurePosixPath, PurePosixPath] = {}

    for original in payload.get("transformations", []):
        rule = dict(original)
        if rule.get("render_mode", "full") != REPLACE_OBJECTS:
            transformations.append(rule)
            continue

        selector = rule.get("file")
        if not isinstance(selector, str) or any(token in selector for token in "*?["):
            raise ValueError(
                f"{source}: replace_objects requires one exact source file per rule"
            )
        source_relative = safe_relative(selector, f"{source}: file")
        if not supports_replace_entries(source_relative):
            raise ValueError(
                f"{source}: replace_objects is not supported for {source_relative}"
            )

        object_name = rule.get("object")
        if (
            not isinstance(object_name, str)
            or not object_name
            or object_name == "**"
            or "/" in object_name
        ):
            raise ValueError(
                f"{source}: replace_objects requires one exact top-level object"
            )
        if rule.get("operation") == "replace_file":
            raise ValueError(f"{source}: replace_file cannot use replace_objects")

        output_raw = rule.get("output_file")
        output_relative = (
            safe_relative(output_raw, f"{source}: output_file")
            if isinstance(output_raw, str)
            else cbp_prefixed_path(source_relative)
        )
        if output_relative.parent != source_relative.parent:
            raise ValueError(
                f"{source}: replace_objects output must remain beside its source file"
            )
        if not output_relative.name.startswith("cbp_"):
            raise ValueError(
                f"{source}: replace_objects output filename must start with 'cbp_'"
            )

        previous_source = replace_sources.get(output_relative)
        if previous_source is not None and previous_source != source_relative:
            raise ValueError(
                f"{source}: replace_objects output {output_relative} cannot combine "
                f"multiple Vanilla source files"
            )
        replace_sources[output_relative] = source_relative

        rule["output_file"] = output_relative.as_posix()
        rule["render_mode"] = "selected_objects"
        transformations.append(rule)
        replace_outputs.add(output_relative)

    prepared["transformations"] = transformations
    return prepared, replace_outputs, replace_sources


def preserve_object_boundary_whitespace(
    lines: list[str],
    objects: list[cbg.LocatedObject],
    source_path: Path,
) -> None:
    """Restore horizontal whitespace stripped only at selected-object boundaries."""
    source_lines = source_path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    source_objects = {
        obj.path[0]: obj
        for obj in cbg.scan_objects(source_lines)
        if len(obj.path) == 1
    }

    for obj in objects:
        source_obj = source_objects.get(obj.path[0])
        if source_obj is None:
            raise ValueError(
                f"replace_objects source lacks top-level object {obj.path[0]!r}: "
                f"{source_path}"
            )

        source_end = source_lines[source_obj.end].rstrip("\r\n")
        source_trailing = source_end[len(source_end.rstrip(" \t")) :]

        rendered_line = lines[obj.end]
        newline = "\n" if rendered_line.endswith("\n") else ""
        rendered_body = rendered_line.rstrip("\r\n").rstrip(" \t")
        lines[obj.end] = f"{rendered_body}{source_trailing}{newline}"


def add_replace_entry_modes(
    path: Path,
    manifest_entry: dict[str, Any],
    source_path: Path,
) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    objects = [obj for obj in cbg.scan_objects(lines) if len(obj.path) == 1]
    if not objects:
        raise ValueError(f"replace_objects output contains no top-level objects: {path}")

    audited = {
        entry.get("object")
        for entry in manifest_entry.get("transformations", [])
        if entry.get("object")
    }
    rendered = {obj.path[0] for obj in objects}
    if audited != rendered:
        raise ValueError(
            f"replace_objects audit/render mismatch for {path}: "
            f"audit={sorted(audited)!r}, rendered={sorted(rendered)!r}"
        )

    preserve_object_boundary_whitespace(lines, objects, source_path)

    for obj in objects:
        line = lines[obj.start]
        newline = "\n" if line.endswith("\n") else ""
        body = line.rstrip("\r\n")
        match = ENTRY_LINE.match(body)
        if match is None or match.group("name") != obj.path[0]:
            raise ValueError(f"Cannot mark database entry as REPLACE at {path}:{obj.start + 1}")
        lines[obj.start] = (
            f"{match.group('indent')}REPLACE:{match.group('name')}"
            f"{match.group('tail')}{newline}"
        )

    generated = "".join(lines).encode("utf-8")
    path.write_bytes(generated)
    manifest_entry["generated_sha256"] = cbg.sha256(generated)
    manifest_entry["database_entry_mode"] = "REPLACE"


def snapshot_owned_outputs(output_root: Path, manifest_path: Path) -> dict[PurePosixPath, bytes]:
    if not manifest_path.is_file():
        return {}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshots: dict[PurePosixPath, bytes] = {}
    for entry in payload.get("files", []):
        relative = PurePosixPath(entry["path"])
        path = output_root / Path(relative)
        if path.is_file():
            snapshots[relative] = path.read_bytes()
    return snapshots


def restore_snapshot(output_root: Path, snapshot: dict[PurePosixPath, bytes], created: set[PurePosixPath]) -> None:
    for relative in created - set(snapshot):
        path = output_root / Path(relative)
        if path.is_file():
            path.unlink()
    for relative, content in snapshot.items():
        path = output_root / Path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, action="append", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--adopt-identical-output", action="store_true")
    parser.add_argument("--adopt-marked-output-tree", type=PurePosixPath)
    parser.add_argument("--adopt-output-marker")
    args = parser.parse_args()

    game_root = args.game_root.resolve()
    output_root = args.output_root.resolve()
    manifest_path = (args.manifest or output_root / "cbg_manifest.json").resolve()
    snapshot = snapshot_owned_outputs(output_root, manifest_path)
    replace_outputs: set[PurePosixPath] = set()
    replace_sources: dict[PurePosixPath, PurePosixPath] = {}

    try:
        with tempfile.TemporaryDirectory(prefix="cbp-cbg-specs-") as temporary:
            prepared_specs: list[Path] = []
            for index, spec_path in enumerate(args.spec):
                payload = json.loads(spec_path.read_text(encoding="utf-8"))
                prepared, outputs, sources = prepare_spec(payload, spec_path)
                replace_outputs.update(outputs)
                for output_relative, source_relative in sources.items():
                    previous_source = replace_sources.get(output_relative)
                    if previous_source is not None and previous_source != source_relative:
                        raise ValueError(
                            f"replace_objects output {output_relative} cannot combine "
                            "multiple Vanilla source files across specifications"
                        )
                    replace_sources[output_relative] = source_relative
                prepared_path = Path(temporary) / f"{index:03d}-{spec_path.name}"
                prepared_path.write_text(
                    json.dumps(prepared, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                prepared_specs.append(prepared_path)

            intents, _custom_fields = cbg.load_intents(prepared_specs, game_root)
            business_rules = cbg.load_business_rules(prepared_specs)
            manifest = cbg.generate(
                game_root,
                output_root,
                intents,
                manifest_path,
                adopt_identical=args.adopt_identical_output,
                adopt_marked_tree=args.adopt_marked_output_tree,
                adopt_marker=(
                    args.adopt_output_marker.encode("utf-8")
                    if args.adopt_output_marker
                    else None
                ),
            )

            entries = {PurePosixPath(entry["path"]): entry for entry in manifest["files"]}
            for relative in sorted(replace_outputs, key=lambda item: item.as_posix()):
                entry = entries.get(relative)
                if entry is None:
                    continue
                add_replace_entry_modes(
                    output_root / Path(relative),
                    entry,
                    game_root / Path(replace_sources[relative]),
                )

            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            cbg.print_generation_summary(
                manifest,
                len(intents),
                manifest_path,
                business_rules,
            )
            return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        restore_snapshot(output_root, snapshot, replace_outputs)
        enabled = cbg.color_enabled(sys.stderr)
        cue = cbg.styled("[FAILED]", "1;31", enabled)
        message = cbg.styled("CBP Community Balance Generator", "1;31", enabled)
        print(f"\n{cbg.styled('━' * 72, '1;31', enabled)}", file=sys.stderr)
        print(f"{cue} {message}", file=sys.stderr)
        print(f"  {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

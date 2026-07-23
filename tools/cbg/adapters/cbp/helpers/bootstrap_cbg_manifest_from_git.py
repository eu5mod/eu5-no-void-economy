#!/usr/bin/env python3
"""Bootstrap or reconcile CBG ownership with clean generated outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath


REPLACE_OBJECTS = "replace_objects"
GLOB_TOKENS = "*?["


def display_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return f"./{resolved.relative_to(repo_root).as_posix()}"
    except ValueError:
        return str(path)


def git_bytes(repo_root: Path, relative: Path) -> bytes:
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative.as_posix()}"],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise ValueError(f"output is not tracked at HEAD: {relative}")
    return result.stdout


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def prefixed_output(source: str) -> str:
    relative = PurePosixPath(source)
    name = relative.name
    if not name.startswith("cbp_"):
        name = f"cbp_{name}"
    return relative.with_name(name).as_posix()


def output_for(item: dict[str, object]) -> str:
    output = item.get("output_file")
    if isinstance(output, str):
        return output
    source = item["file"]
    if not isinstance(source, str):
        raise ValueError("manifest bootstrap requires exact source paths")
    if item.get("render_mode") == REPLACE_OBJECTS:
        return prefixed_output(source)
    return source


def output_markers(spec: dict[str, object]) -> dict[str, set[str]]:
    """Return exact generated-header markers declared for each output."""
    markers: dict[str, set[str]] = {}
    for item in spec.get("transformations", []):
        if not isinstance(item, dict):
            continue
        header = item.get("header")
        if not isinstance(header, list) or not header or not isinstance(header[0], str):
            continue
        markers.setdefault(output_for(item), set()).add(header[0])
    return markers


def legacy_outputs_for_replace_rules(spec: dict[str, object]) -> set[str]:
    """Derive obsolete exact-path outputs replaced by cbp_-prefixed files.

    This deliberately derives migration inputs from the current business-rule
    specification. It therefore works on a clean checkout where the ignored CBG
    manifest does not exist yet.
    """
    legacy: set[str] = set()
    for item in spec.get("transformations", []):
        if not isinstance(item, dict) or item.get("render_mode") != REPLACE_OBJECTS:
            continue
        source = item.get("file")
        if not isinstance(source, str) or any(token in source for token in GLOB_TOKENS):
            raise ValueError("replace_objects manifest migration requires exact source paths")
        if source != output_for(item):
            legacy.add(source)
    return legacy


def first_line(content: bytes) -> str:
    lines = content.splitlines()
    return lines[0].decode("utf-8", errors="replace") if lines else ""


def signed_by_explicit_marker(
    destination: Path,
    current: bytes,
    output_root: Path,
    adoption_tree: Path | None,
    adoption_marker: str | None,
) -> bool:
    if adoption_tree is None or adoption_marker is None:
        return False
    tree = (output_root / adoption_tree).resolve()
    return destination.resolve().is_relative_to(tree) and first_line(current) == adoption_marker


def ownership_entry(path: str, content: bytes, bootstrap: str) -> dict[str, object]:
    return {
        "path": path,
        "vanilla_sha256": None,
        "generated_sha256": sha256(content),
        "transformations": [{"bootstrap": bootstrap}],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--adopt-marked-output-tree", type=Path)
    parser.add_argument("--adopt-output-marker")
    args = parser.parse_args()

    manifest = args.manifest.resolve()
    repo_result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    repo_root = Path(repo_result.stdout.strip()).resolve()
    output_root = args.output_root.resolve()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    outputs = sorted({output_for(item) for item in spec.get("transformations", [])})
    current_outputs = set(outputs)
    legacy_outputs = legacy_outputs_for_replace_rules(spec) - current_outputs
    spec_markers = output_markers(spec)

    existing_files: dict[str, dict[str, object]] = {}
    if manifest.is_file():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("generator") != "community_balance_generator":
            raise ValueError(f"refusing foreign manifest ownership: {manifest}")
        existing_files = {entry["path"]: entry for entry in payload.get("files", [])}

    files: list[dict[str, object]] = []
    claimed_paths: set[str] = set()

    for output in outputs:
        relative_output = Path(output)
        destination = output_root / relative_output
        if not destination.is_file():
            continue
        repo_relative = destination.relative_to(repo_root)
        current = destination.read_bytes()
        try:
            tracked = git_bytes(repo_root, repo_relative)
        except ValueError:
            tracked = None
        existing = existing_files.get(relative_output.as_posix())
        if tracked is not None and current == tracked:
            files.append(ownership_entry(output, current, "clean_git_tracked_output"))
            claimed_paths.add(output)
            continue
        if existing and existing.get("generated_sha256") == sha256(current):
            files.append(existing)
            claimed_paths.add(output)
            continue

        declared_markers = spec_markers.get(relative_output.as_posix(), set())
        if tracked is None and first_line(current) in declared_markers:
            files.append(ownership_entry(output, current, "spec_signed_untracked_output"))
            claimed_paths.add(output)
            continue

        if signed_by_explicit_marker(
            destination,
            current,
            output_root,
            args.adopt_marked_output_tree,
            args.adopt_output_marker,
        ):
            files.append(ownership_entry(output, current, "signed_legacy_output"))
            claimed_paths.add(output)
            continue
        if tracked is None:
            raise ValueError(
                f"refusing untracked output not owned by the existing manifest: {repo_relative}"
            )
        raise ValueError(
            f"refusing to reconcile ownership from a locally modified output: {repo_relative}"
        )

    # A replace_objects migration moves ownership from the old exact-path file to
    # a cbp_-prefixed file. Discover and claim the old path from the current spec
    # even when no previous (ignored) manifest exists. The following CBG run then
    # deletes the old file through its normal stale-output ownership contract.
    for output in sorted(legacy_outputs):
        destination = output_root / output
        if not destination.is_file():
            continue
        repo_relative = destination.relative_to(repo_root)
        current = destination.read_bytes()
        existing = existing_files.get(output)
        if existing and existing.get("generated_sha256") == sha256(current):
            files.append(existing)
            claimed_paths.add(output)
            continue
        try:
            tracked = git_bytes(repo_root, repo_relative)
        except ValueError:
            tracked = None
        if tracked is not None and current == tracked:
            files.append(ownership_entry(output, current, "clean_git_tracked_legacy_output"))
            claimed_paths.add(output)
            continue
        if signed_by_explicit_marker(
            destination,
            current,
            output_root,
            args.adopt_marked_output_tree,
            args.adopt_output_marker,
        ):
            files.append(ownership_entry(output, current, "signed_legacy_output"))
            claimed_paths.add(output)
            continue
        if tracked is None:
            raise ValueError(
                f"refusing untracked legacy output not signed for migration: {repo_relative}"
            )
        raise ValueError(
            f"refusing to migrate locally modified legacy output: {repo_relative}"
        )

    # Preserve correctly owned outputs that became stale for reasons other than a
    # currently declared replace_objects migration. The following CBG run deletes
    # them through its normal stale-output ownership contract.
    for output, existing in sorted(existing_files.items()):
        if output in current_outputs or output in claimed_paths:
            continue
        destination = output_root / output
        if not destination.is_file():
            continue
        current = destination.read_bytes()
        if existing.get("generated_sha256") != sha256(current):
            raise ValueError(
                f"refusing to migrate locally modified stale output: {destination.relative_to(repo_root)}"
            )
        files.append(existing)
        claimed_paths.add(output)

    files.sort(key=lambda entry: str(entry["path"]))
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "schema_version": 1,
        "generator": "community_balance_generator",
        "files": files,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Reconciled {display_path(manifest, repo_root)} with {len(files)} owned output(s).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"CBG manifest bootstrap failed: {exc}") from exc

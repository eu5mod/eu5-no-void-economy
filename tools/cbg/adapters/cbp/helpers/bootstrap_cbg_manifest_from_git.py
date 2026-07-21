#!/usr/bin/env python3
"""Bootstrap or reconcile CBG ownership with clean Git-tracked outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath


REPLACE_OBJECTS = "replace_objects"


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


def first_line(content: bytes) -> str:
    lines = content.splitlines()
    return lines[0].decode("utf-8", errors="replace") if lines else ""


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
    spec_markers = output_markers(spec)

    existing_files = {}
    if manifest.is_file():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("generator") != "community_balance_generator":
            raise ValueError(f"refusing foreign manifest ownership: {manifest}")
        existing_files = {entry["path"]: entry for entry in payload.get("files", [])}

    files = []
    current_outputs = set(outputs)
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
            files.append({
                "path": relative_output.as_posix(),
                "vanilla_sha256": None,
                "generated_sha256": sha256(current),
                "transformations": [{"bootstrap": "clean_git_tracked_output"}],
            })
            continue
        if existing and existing.get("generated_sha256") == sha256(current):
            files.append(existing)
            continue

        declared_markers = spec_markers.get(relative_output.as_posix(), set())
        if tracked is None and first_line(current) in declared_markers:
            files.append({
                "path": relative_output.as_posix(),
                "vanilla_sha256": None,
                "generated_sha256": sha256(current),
                "transformations": [{"bootstrap": "spec_signed_untracked_output"}],
            })
            continue

        if args.adopt_marked_output_tree and args.adopt_output_marker:
            adoption_tree = (output_root / args.adopt_marked_output_tree).resolve()
            if (
                destination.resolve().is_relative_to(adoption_tree)
                and first_line(current) == args.adopt_output_marker
            ):
                files.append({
                    "path": relative_output.as_posix(),
                    "vanilla_sha256": None,
                    "generated_sha256": sha256(current),
                    "transformations": [{"bootstrap": "signed_legacy_output"}],
                })
                continue
        if tracked is None:
            raise ValueError(
                f"refusing untracked output not owned by the existing manifest: {repo_relative}"
            )
        raise ValueError(
            f"refusing to reconcile ownership from a locally modified output: {repo_relative}"
        )

    # Preserve correctly owned outputs that became stale because the specification
    # migrated to a new path (for example, Vanilla filename -> cbp_ filename).
    # The following CBG run will delete these entries through its normal stale-output
    # ownership contract. Dropping them here would leave old full-file overrides behind.
    for output, existing in sorted(existing_files.items()):
        if output in current_outputs:
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

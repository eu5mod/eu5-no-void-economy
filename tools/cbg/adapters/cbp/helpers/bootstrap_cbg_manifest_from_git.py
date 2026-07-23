#!/usr/bin/env python3
"""Bootstrap or reconcile CBG ownership with clean Git-tracked outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


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
    outputs = sorted({
        item.get("output_file", item["file"])
        for item in spec.get("transformations", [])
    })

    existing_files = {}
    if manifest.is_file():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("generator") != "community_balance_generator":
            raise ValueError(f"refusing foreign manifest ownership: {manifest}")
        existing_files = {entry["path"]: entry for entry in payload.get("files", [])}

    files = []
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
        if args.adopt_marked_output_tree and args.adopt_output_marker:
            adoption_tree = (output_root / args.adopt_marked_output_tree).resolve()
            first_line = current.splitlines()[0].decode("utf-8", errors="replace") if current.splitlines() else ""
            if destination.resolve().is_relative_to(adoption_tree) and first_line == args.adopt_output_marker:
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

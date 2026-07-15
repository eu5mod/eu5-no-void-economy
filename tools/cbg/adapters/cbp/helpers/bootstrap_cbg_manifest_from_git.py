#!/usr/bin/env python3
"""Bootstrap a missing CBG ownership manifest from clean, Git-tracked outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


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
    args = parser.parse_args()

    manifest = args.manifest.resolve()
    if manifest.is_file():
        return 0

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

    files = []
    for output in outputs:
        relative_output = Path(output)
        destination = output_root / relative_output
        if not destination.is_file():
            continue
        repo_relative = destination.relative_to(repo_root)
        current = destination.read_bytes()
        tracked = git_bytes(repo_root, repo_relative)
        if current != tracked:
            raise ValueError(
                f"refusing to bootstrap ownership from a locally modified output: {repo_relative}"
            )
        files.append({
            "path": relative_output.as_posix(),
            "vanilla_sha256": None,
            "generated_sha256": sha256(current),
            "transformations": [{"bootstrap": "clean_git_tracked_output"}],
        })

    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "schema_version": 1,
        "generator": "community_balance_generator",
        "files": files,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Bootstrapped {manifest} from {len(files)} clean Git-tracked output(s).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"CBG manifest bootstrap failed: {exc}") from exc

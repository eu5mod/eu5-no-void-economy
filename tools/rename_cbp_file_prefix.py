#!/usr/bin/env python3
"""Rename tracked repository files from the ``cbp_`` prefix to ``cbp_``.

The script changes file names only. It does not modify file contents, identifiers,
localization keys, or directory names.

Examples:
    python3 tools/rename_cbp_file_prefix.py
    python3 tools/rename_cbp_file_prefix.py --check
    python3 tools/rename_cbp_file_prefix.py --apply
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SOURCE_PREFIX = "zzz_modeu5_"
TARGET_PREFIX = "zzz_cbp_"
ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Rename:
    source: Path
    target: Path


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def repository_root(start: Path) -> Path:
    result = git(start, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"not inside a Git repository: {error or start}")
    return Path(result.stdout.decode("utf-8").strip()).resolve()


def tracked_files(root: Path) -> list[Path]:
    result = git(root, "ls-files", "-z")
    return [
        root / entry.decode("utf-8", errors="surrogateescape")
        for entry in result.stdout.split(b"\0")
        if entry
    ]


def plan_renames(root: Path) -> list[Rename]:
    renames: list[Rename] = []
    for source in tracked_files(root):
        if not source.name.startswith(SOURCE_PREFIX):
            continue
        target_name = TARGET_PREFIX + source.name[len(SOURCE_PREFIX):]
        renames.append(Rename(source=source, target=source.with_name(target_name)))
    return sorted(renames, key=lambda item: item.source.relative_to(root).as_posix())


def validate_plan(root: Path, renames: list[Rename]) -> None:
    sources = {item.source for item in renames}
    targets: dict[str, Path] = {}
    errors: list[str] = []

    for item in renames:
        relative_target = item.target.relative_to(root).as_posix()
        collision_key = relative_target.casefold()
        previous = targets.get(collision_key)
        if previous is not None and previous != item.source:
            errors.append(
                f"multiple sources would map to {relative_target}: "
                f"{previous.relative_to(root)} and {item.source.relative_to(root)}"
            )
        targets[collision_key] = item.source

        if item.target.exists() and item.target not in sources:
            errors.append(f"target already exists: {relative_target}")

    if errors:
        raise RuntimeError("rename plan is unsafe:\n- " + "\n- ".join(errors))


def print_plan(root: Path, renames: list[Rename]) -> None:
    if not renames:
        print(f"No tracked files start with {SOURCE_PREFIX!r}.")
        return
    for item in renames:
        source = item.source.relative_to(root).as_posix()
        target = item.target.relative_to(root).as_posix()
        print(f"{source} -> {target}")
    print(f"\n{len(renames)} file(s) would be renamed.")


def apply_plan(root: Path, renames: list[Rename]) -> None:
    completed: list[Rename] = []
    try:
        for item in renames:
            source = item.source.relative_to(root).as_posix()
            target = item.target.relative_to(root).as_posix()
            result = git(root, "mv", "--", source, target, check=False)
            if result.returncode != 0:
                error = result.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"git mv failed for {source}: {error}")
            completed.append(item)
    except Exception:
        for item in reversed(completed):
            source = item.source.relative_to(root).as_posix()
            target = item.target.relative_to(root).as_posix()
            git(root, "mv", "--", target, source, check=False)
        raise

    print(f"Renamed {len(renames)} tracked file(s) from {SOURCE_PREFIX} to {TARGET_PREFIX}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--apply",
        action="store_true",
        help="perform the renames with git mv (default: print a dry run)",
    )
    action.add_argument(
        "--check",
        action="store_true",
        help="exit with status 1 when files still require renaming",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="path inside the target Git repository (default: this repository)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = repository_root(args.root.resolve())
        renames = plan_renames(root)
        validate_plan(root, renames)
        if args.apply:
            apply_plan(root, renames)
        else:
            print_plan(root, renames)
        return 1 if args.check and renames else 0
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reject legacy exact-path package files whose Vanilla source disappeared."""

from __future__ import annotations

import argparse
from pathlib import Path


def is_cbp_owned_name(path: Path) -> bool:
    return path.name.startswith(("cbp_", "zz_cbp_"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=Path("packages/cbp_economy_rebalance"),
    )
    args = parser.parse_args()

    game_root = args.game_root.resolve()
    package_root = args.package_root.resolve()
    failures: list[str] = []

    for surface in ("in_game", "main_menu", "loading_screen"):
        package_surface = package_root / surface
        if not package_surface.is_dir():
            continue
        for output in sorted(package_surface.rglob("*.txt")):
            relative = output.relative_to(package_root)
            if is_cbp_owned_name(output):
                continue
            if not (game_root / relative).is_file():
                failures.append(relative.as_posix())

    if failures:
        print("Vanilla-derived output validation failed:")
        print(
            "The following exact-path files have no source in the installed "
            "Vanilla version and are likely stale migration artifacts:"
        )
        for relative in failures:
            print(f"- {relative}")
        return 1

    print(
        "Vanilla-derived output validation passed: every non-CBP exact-path "
        "text file still has an installed Vanilla source."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

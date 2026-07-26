#!/usr/bin/env python3
"""Validate append-only CBP building production-method injections."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from transform_cbp_economy_building_overrides import (
    ASSIGNMENT,
    find_named_blocks,
)


ENTRY_MODE = re.compile(
    r"^(?P<indent>[ \t]*)(?:INJECT:)(?P<name>[A-Za-z0-9_.:-]+)"
    r"(?P<tail>[ \t]*=[ \t]*\{.*)$"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--building-dir",
        type=Path,
        default=Path(
            "packages/cbp_economy_rebalance/in_game/common/building_types"
        ),
    )
    args = parser.parse_args()

    failures: list[str] = []
    generated_methods: dict[str, str] = {}
    for path in sorted(
        args.building_dir.glob("cbp_us09_production_methods_*.txt")
    ):
        original_lines = path.read_text(encoding="utf-8-sig").splitlines()
        lines = []
        for line in original_lines:
            match = ENTRY_MODE.match(line)
            if match:
                line = (
                    f"{match.group('indent')}{match.group('name')}"
                    f"{match.group('tail')}"
                )
            lines.append(line)

        blocks = find_named_blocks(lines)
        containers = [
            block
            for block in blocks
            if block.depth == 1 and block.key == "unique_production_methods"
        ]
        for container in containers:
            methods = [
                block
                for block in blocks
                if block.depth == 2
                and container.start < block.start
                and block.end < container.end
            ]
            for method in methods:
                location = f"{path}:{method.start + 1}"
                if not method.key.startswith("cbp_us09_"):
                    failures.append(
                        f"{location}: injected production method must use "
                        "the cbp_us09_ prefix"
                    )
                previous = generated_methods.get(method.key)
                if previous is not None:
                    failures.append(
                        f"{location}: duplicate generated method {method.key}; "
                        f"first declared at {previous}"
                    )
                generated_methods[method.key] = location

                fields = {
                    match.group(2)
                    for line in lines[method.start : method.end + 1]
                    if (match := ASSIGNMENT.match(line)) is not None
                }
                for required in ("output",):
                    if required not in fields:
                        failures.append(
                            f"{location}: {method.key} is missing {required}"
                        )

    if failures:
        print("CBP building injection validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    if not generated_methods:
        print("CBP building injection validation passed: no production alternatives.")
        return 0

    package_root = args.building_dir.parents[2]
    localization = (
        package_root
        / "main_menu/localization/english/cbp_us09_production_methods_l_english.yml"
    )
    if not localization.is_file():
        print("CBP building injection validation failed:")
        print(f"- missing generated localization: {localization}")
        return 1
    localization_text = localization.read_text(encoding="utf-8-sig")
    localized = set(
        re.findall(
            r"^\s*(cbp_us09_[A-Za-z0-9_]+):\d+\s+",
            localization_text,
            re.MULTILINE,
        )
    )
    if localized != set(generated_methods):
        print("CBP building injection validation failed:")
        print(
            "- production-method localization coverage mismatch: "
            f"methods={len(generated_methods)} localizations={len(localized)}"
        )
        return 1

    advance_dir = package_root / "in_game/common/advances"
    unlock_targets: list[str] = []
    for path in sorted(advance_dir.glob("cbp_inject_us09_*.txt")):
        text = path.read_text(encoding="utf-8-sig")
        if re.search(
            r"^\s*(?:REPLACE|TRY_INJECT):",
            text,
            re.MULTILINE,
        ):
            failures.append(f"{path}: US-09 unlock output must contain only INJECT")
        unlock_targets.extend(
            re.findall(
                r"^\s*unlock_production_method\s*=\s*([A-Za-z0-9_.:-]+)",
                text,
                re.MULTILINE,
            )
        )
    invalid_unlocks = sorted(
        target
        for target in unlock_targets
        if target not in generated_methods
    )
    if invalid_unlocks:
        failures.append(
            "advance injections reference unknown CBP production methods: "
            + ", ".join(invalid_unlocks)
        )
    if failures:
        print("CBP building injection validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "CBP building injection validation passed: "
        f"{len(generated_methods)} unique and localized cbp_us09_ "
        f"production alternatives; {len(unlock_targets)} Vanilla unlocks mirrored."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

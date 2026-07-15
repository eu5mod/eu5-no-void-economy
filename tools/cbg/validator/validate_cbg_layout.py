#!/usr/bin/env python3
"""Validate that the shareable CBG tree remains independent from its host mod."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = {
    "README.md",
    "REFERENCE.md",
    "LICENSE.md",
    "community_balance_generator.py",
    "adapters/README.md",
    "adapters/cbp/README.md",
    "examples/community_balance_spec.example.json",
    "tests/test_community_balance_generator.py",
    "legacy/README.md",
    "validator/README.md",
    "validator/validate_cbg_layout.py",
    "validator/cbp/README.md",
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".sh"}
HOST_POLICY = re.compile(r"\b(?:" + "c" + r"bp|modeu5|us-\d+)\b", re.IGNORECASE)
HOST_IMPORT = re.compile(r"(?:from|import)\s+tools\.(?!cbg(?:\.|\b))")


def main() -> int:
    failures: list[str] = []
    present = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
    }
    for missing in sorted(REQUIRED - present):
        failures.append(f"missing shareable CBG file: tools/cbg/{missing}")

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if relative.startswith(("adapters/", "validator/cbp/")):
            continue
        if relative != "validator/validate_cbg_layout.py" and HOST_POLICY.search(text):
            failures.append(f"host-mod policy name leaked into tools/cbg/{relative}")
        if HOST_IMPORT.search(text):
            failures.append(f"host-mod import leaked into tools/cbg/{relative}")

    if failures:
        print("CBG shareable-layout validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("CBG shareable-layout validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

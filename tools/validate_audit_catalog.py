#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    audits_root = repo_root / "docs" / "audits"
    catalog = audits_root / "README.md"

    expected = {
        path.relative_to(audits_root).as_posix()
        for path in audits_root.rglob("*.md")
        if path != catalog
    }
    links = re.findall(r"\[[^]]+\]\(\./([^)]+\.md)\)", catalog.read_text(encoding="utf-8"))
    counts = Counter(links)
    actual = set(links)

    errors: list[str] = []
    for path in sorted(expected - actual):
        errors.append(f"uncatalogued audit document: {path}")
    for path in sorted(actual - expected):
        errors.append(f"catalog link does not resolve to an audit document: {path}")
    for path, count in sorted(counts.items()):
        if count != 1:
            errors.append(f"audit document must be catalogued exactly once: {path} ({count} links)")

    if errors:
        print("CBP audit catalog validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"CBP audit catalog validation passed: {len(expected)} documents catalogued.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

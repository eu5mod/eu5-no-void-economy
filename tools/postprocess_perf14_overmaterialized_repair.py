#!/usr/bin/env python3
"""Temporarily disable PERF-14 overmaterialized generated-code repair.

Stability boundary:
- `modeu5_stock_goods_generated.txt` is generated locally and is not a tracked
  repository file.
- During the PR #107 stability pass, this postprocessor must not inject custom
  generated script into the stock-good adapter.
- PERF-14 promotion repair and US-10 candidate scan changes should be moved into
  their owning templates/generators in a later, explicit change.

This script intentionally accepts the historical arguments used by
`tools/generate_all.sh`, but leaves all files unchanged.
"""

from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) not in {2, 3, 4}:
        print(
            "usage: postprocess_perf14_overmaterialized_repair.py <modeu5_stock_goods_generated.txt> [legacy_perf14_guarded_test_effects.txt] [legacy_perf14_test_effects.txt]",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

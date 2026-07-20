#!/usr/bin/env python3
"""Compatibility helpers for Vanilla fields that may disappear between EU5 versions."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable, TextIO


PROFIT_MARGIN_FIELDS = (
    "rural_profit_margin",
    "guild_profit_margin",
    "workshop_profit_margin",
    "manufactory_profit_margin",
    "mills_profit_margin",
)

ROOT_ASSIGNMENT = re.compile(
    r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>[^#\r\n]+?)\s*(?:#.*)?$"
)
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def _warning_prefix(stream: TextIO) -> str:
    text = "[⚠️]"
    if "NO_COLOR" not in os.environ and bool(getattr(stream, "isatty", lambda: False)()):
        return f"\033[1;33m{text}\033[0m"
    return text


def discover_optional_root_numeric_fields(
    source: Path,
    expected_fields: Iterable[str],
    *,
    policy_name: str,
    warning_stream: TextIO = sys.stderr,
) -> tuple[str, ...]:
    """Return supported root numeric fields and warn when Vanilla removed optional ones.

    A missing optional field is a compatible Vanilla schema change and is skipped.
    Duplicate definitions or a present non-numeric definition remain hard failures,
    because silently choosing an interpretation would make the generated balance
    override unsafe.
    """

    expected = tuple(dict.fromkeys(expected_fields))
    expected_set = set(expected)
    matches: dict[str, list[str]] = {name: [] for name in expected}

    for raw_line in source.read_text(encoding="utf-8-sig").splitlines():
        match = ROOT_ASSIGNMENT.match(raw_line)
        if not match or match.group("name") not in expected_set:
            continue
        matches[match.group("name")].append(match.group("value").strip())

    duplicate = sorted(name for name, values in matches.items() if len(values) > 1)
    if duplicate:
        raise ValueError(
            f"Ambiguous Vanilla {policy_name} fields with multiple definitions: {duplicate}"
        )

    unsupported = sorted(
        name
        for name, values in matches.items()
        if values and not NUMBER.fullmatch(values[0])
    )
    if unsupported:
        raise ValueError(
            f"Unsupported non-numeric Vanilla {policy_name} fields: {unsupported}"
        )

    available = tuple(name for name in expected if matches[name])
    missing = tuple(name for name in expected if not matches[name])
    if missing:
        print(
            f"{_warning_prefix(warning_stream)} Vanilla {policy_name} field(s) not exposed "
            f"by this EU5 version; skipping: {', '.join(missing)}",
            file=warning_stream,
        )

    return available

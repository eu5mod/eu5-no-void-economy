#!/usr/bin/env python3
"""Validate the offline contract of the tracked CBP CBG master specification."""

from __future__ import annotations

import json
from pathlib import Path

from generate_cbp_community_balance_spec import EVENT_FIELDS, MONTHLY_FIELDS


SPEC = Path("tools/specs/cbp_pr188_balance.generated.json")


def expected_rules() -> set[tuple[str, str, float]]:
    return {
        *(("in_game/events/**/*.txt", field, 0.5) for field in EVENT_FIELDS),
        *(("in_game/common/**/*.txt", field, 0.5) for field in EVENT_FIELDS),
        *(("in_game/common/**/*.txt", field, 0.75) for field in MONTHLY_FIELDS),
    }


def main() -> int:
    payload = json.loads(SPEC.read_text(encoding="utf-8"))
    political_fields = set(EVENT_FIELDS) | set(MONTHLY_FIELDS)
    discovered: set[tuple[str, str, float]] = set()
    failures: list[str] = []

    for rule in payload.get("transformations", []):
        field = rule.get("field")
        if field not in political_fields:
            continue
        selector = rule.get("file")
        if isinstance(selector, list):
            failures.append(f"{field}: political master rule must not enumerate files")
            continue
        if rule.get("object") != "**":
            failures.append(f"{field}: political rule must use object '**'")
        if rule.get("operation") != "multiply":
            failures.append(f"{field}: political rule must multiply")
        if rule.get("occurrences") != "all" or rule.get("on_missing") != "skip":
            failures.append(f"{field}: political rule must discover all optional occurrences")
        try:
            discovered.add((selector, field, float(rule["value"])))
        except (KeyError, TypeError, ValueError):
            failures.append(f"{field}: invalid selector or multiplier")

        exclusions = set(rule.get("exclude_files", []))
        if selector == "in_game/events/**/*.txt" and "in_game/events/debug/**/*.txt" not in exclusions:
            failures.append(f"{field}: event rule must exclude the debug tree")
        if (
            selector == "in_game/common/**/*.txt"
            and field in EVENT_FIELDS
            and "in_game/common/effect_localization/**/*.txt" not in exclusions
        ):
            failures.append(f"{field}: common instant-effect rule must exclude effect localization")

    missing = expected_rules() - discovered
    unexpected = discovered - expected_rules()
    if missing:
        failures.append(f"missing master rules: {sorted(missing)}")
    if unexpected:
        failures.append(f"unexpected political rules: {sorted(unexpected)}")

    if failures:
        print("CBG master specification validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"CBG master specification validation passed: {len(discovered)} discovery rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

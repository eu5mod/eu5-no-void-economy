#!/usr/bin/env python3
"""Validate the offline contract of the tracked CBP CBG master specification."""

from __future__ import annotations

import json
from pathlib import Path

from generate_cbp_community_balance_spec import EVENT_FIELDS, MONTHLY_FIELDS, canonical_goods


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

    rules = payload.get("transformations", [])

    def matching(**expected):
        return [rule for rule in rules if all(rule.get(key) == value for key, value in expected.items())]

    bulk_contracts = (
        ("output", "multiply"),
        ("local_merchant_capacity", "multiply"),
        ("merchant_capacity_from_building", "multiply"),
        ("maximum_stockpile_capacity", "comment_out"),
    )
    for field, operation in bulk_contracts:
        matches = matching(
            file="in_game/common/building_types/*.txt", object="**",
            field=field, operation=operation, occurrences="all", on_missing="skip",
        )
        if len(matches) != 1:
            failures.append(f"{field}: expected one building master rule, found {len(matches)}")

    for selector in ("in_game/common/**/*.txt", "main_menu/common/static_modifiers/**/*.txt"):
        if len(matching(file=selector, object="**", field="minting_income_factor", operation="multiply")) != 1:
            failures.append(f"minting_income_factor: missing master rule for {selector}")

    goods = set(canonical_goods())
    maintenance = [
        rule for rule in rules
        if rule.get("file") == "in_game/common/building_types/*.txt"
        and rule.get("object") == "**"
        and rule.get("field") in goods
        and rule.get("operation") == "multiply"
        and {"category": "building_maintenance"} in rule.get("where", {}).get("inside", [])
    ]
    if len(maintenance) != len(goods) * 2:
        failures.append(
            f"building maintenance: expected {len(goods) * 2} good/policy rules, found {len(maintenance)}"
        )
    for rule in maintenance:
        inside = rule.get("where", {}).get("inside", [])
        not_inside = rule.get("where", {}).get("not_inside", [])
        is_trade = {"category": "trade_category"} in inside
        is_non_trade = {"category": "trade_category"} in not_inside
        if is_trade == is_non_trade:
            failures.append(f"{rule.get('field')}: maintenance rule must select trade xor non-trade")
        if set(rule.get("exclude_objects", [])) != {"marketplace", "merchants_quarters", "grand_marketplace"}:
            failures.append(f"{rule.get('field')}: maintenance rule has unsafe marketplace exclusions")

    for field in ("location_potential", "country_potential"):
        matches = matching(
            file="in_game/common/building_types/market_buildings.txt",
            object="market_warehouse", field=field, operation="upsert_block",
        )
        if len(matches) != 1 or matches[0].get("value") != {"always": "no"}:
            failures.append(f"market_warehouse/{field}: missing always=no block upsert")

    if payload.get("parity_contract", {}).get("known_structural_gaps"):
        failures.append("tracked primary-candidate spec must not declare structural gaps")

    if failures:
        print("CBG master specification validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "CBG master specification validation passed: "
        f"{len(discovered)} political and {len(maintenance)} maintenance discovery rules."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

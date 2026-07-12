#!/usr/bin/env python3
"""Validate the ModeU5 country wealth endpoint static contract."""

from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
VALUES_FILE = REPO_ROOT / "in_game/common/script_values/modeu5_wealth_values.txt"
EFFECTS_FILE = REPO_ROOT / "in_game/common/scripted_effects/modeu5_core04_market_entry_effects.txt"


def extract_effect(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\{{", text)
    if match is None:
        raise ValueError(f"Missing effect: {name}")

    start = match.start()
    depth = 0
    opened = False
    for index in range(match.start(), len(text)):
        char = text[index]
        if char == "{":
            depth += 1
            opened = True
        elif char == "}":
            depth -= 1
            if opened and depth == 0:
                return text[start : index + 1]

    raise ValueError(f"Unclosed effect block: {name}")


def require(pattern: str, text: str, message: str, errors: list[str]) -> None:
    if re.search(pattern, text, flags=re.MULTILINE) is None:
        errors.append(message)


def main() -> int:
    errors: list[str] = []

    if not VALUES_FILE.is_file():
        errors.append(f"Missing wealth script-value file: {VALUES_FILE.relative_to(REPO_ROOT)}")
        values_text = ""
    else:
        values_text = VALUES_FILE.read_text(encoding="utf-8")

    if not EFFECTS_FILE.is_file():
        errors.append(f"Missing CORE-04 effects file: {EFFECTS_FILE.relative_to(REPO_ROOT)}")
        effects_text = ""
    else:
        effects_text = EFFECTS_FILE.read_text(encoding="utf-8")

    require(
        r"^modeu5_location_wealth_endpoint\s*=\s*\{",
        values_text,
        "Missing modeu5_location_wealth_endpoint scripted value.",
        errors,
    )
    require(
        r"limit\s*=\s*\{\s*local_control\s*>\s*0\s*\}",
        values_text,
        "Wealth endpoint must guard division with local_control > 0.",
        errors,
    )
    require(
        r"value\s*=\s*tax_base",
        values_text,
        "Wealth endpoint must start from location tax_base.",
        errors,
    )
    require(
        r"divide\s*=\s*local_control",
        values_text,
        "Wealth endpoint must divide tax_base by local_control.",
        errors,
    )

    try:
        monthly_effect = extract_effect(
            effects_text,
            "modeu5_core04_refresh_current_country_location_market_memory",
        )
    except ValueError as exc:
        errors.append(str(exc))
        monthly_effect = ""

    owned_location_loops = len(re.findall(r"(?m)^\s*every_owned_location\s*=\s*\{", monthly_effect))
    if owned_location_loops != 1:
        errors.append(
            "Monthly CORE-04 memory/wealth effect must contain exactly one "
            f"every_owned_location loop; found {owned_location_loops}."
        )

    for variable_name in (
        "cbp_location_wealth_endpoint",
        "cbp_location_wealth_endpoint_stamp",
        "cbp_country_wealth_endpoint",
        "cbp_country_wealth_endpoint_stamp",
        "cbp_country_wealth_unresolved_location_count",
    ):
        require(
            rf"name\s*=\s*{re.escape(variable_name)}",
            monthly_effect,
            f"Monthly endpoint is missing {variable_name}.",
            errors,
        )

    require(
        r"change_local_variable\s*=\s*\{\s*"
        r"name\s*=\s*cbp_country_wealth_endpoint_accumulator\s*"
        r"add\s*=\s*scope:cbp_location_wealth_endpoint_value",
        monthly_effect,
        "Country wealth must accumulate the calculated location endpoint inside the existing loop.",
        errors,
    )
    require(
        r"else\s*=\s*\{.*?"
        r"name\s*=\s*cbp_country_wealth_unresolved_location_count\s*"
        r"add\s*=\s*1",
        monthly_effect,
        "Zero-control locations must increment the unresolved-location counter.",
        errors,
    )

    if re.search(
        r"set_global_variable\s*=\s*(?:\{[^}]*name\s*=\s*)?"
        r"cbp_(?:country|location)_wealth_endpoint",
        effects_text,
        flags=re.MULTILINE | re.DOTALL,
    ):
        errors.append(
            "Wealth endpoints must remain country/location-owned variables, not global singletons."
        )

    if errors:
        print("Wealth endpoint static contract failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Wealth endpoint static contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

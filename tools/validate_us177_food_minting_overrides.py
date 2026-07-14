#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


NUMERIC_ASSIGNMENT = re.compile(
    r"^\s*([A-Za-z0-9_]+)\s*=\s*(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\s*(?:#.*)?$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the US-177 food classification and minting generator contracts."
    )
    parser.add_argument("--game-root", type=Path, default=None)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=Path("packages/cbp_economy_rebalance"),
    )
    parser.add_argument("--food-price", default="0.3")
    parser.add_argument("--food-production-divisor", default="3")
    parser.add_argument("--minting-multiplier", default="2")
    return parser.parse_args()


def resolve_game_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    install_dir = os.environ.get("EU5_INSTALL_DIR")
    if install_dir:
        install = Path(install_dir).expanduser().resolve()
        for candidate in (install / "game", install):
            if (candidate / "in_game/common").is_dir():
                return candidate
    common_dir = os.environ.get("EU5_GAME_COMMON_DIR")
    if common_dir:
        common = Path(common_dir).expanduser().resolve()
        if common.name == "common" and common.parent.name == "in_game":
            return common.parent.parent
    raise SystemExit("Pass --game-root or configure EU5_INSTALL_DIR / EU5_GAME_COMMON_DIR.")


def decimal(raw: str, label: str) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise SystemExit(f"{label} must be numeric; got {raw!r}.") from exc
    if not value.is_finite():
        raise SystemExit(f"{label} must be finite; got {raw!r}.")
    return value


def numeric_values(path: Path, key: str) -> list[Decimal]:
    values: list[Decimal] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = NUMERIC_ASSIGNMENT.match(line)
        if match and match.group(1) == key:
            values.append(decimal(match.group(2), f"{path}:{key}"))
    return values


def run_checked(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode)
    if completed.stdout:
        print(completed.stdout.rstrip())


def validate_minting_baseline(package_root: Path) -> None:
    baseline = (
        package_root
        / "in_game/common/auto_modifiers/cbp_us177_minting_income_auto_modifiers.txt"
    )
    if not baseline.is_file():
        raise SystemExit(f"Missing US-177 minting baseline auto modifier: {baseline}")
    values = numeric_values(baseline, "minting_income_factor")
    if values != [Decimal("1.0")]:
        raise SystemExit(
            "US-177 baseline must contain exactly minting_income_factor = 1.0; "
            f"found {values}."
        )
    lowered = baseline.read_text(encoding="utf-8-sig").lower()
    if re.search(r"^\s*[^#\r\n]*inflation[^=\r\n]*=", lowered, flags=re.MULTILINE):
        raise SystemExit("US-177 baseline must not modify inflation-related fields.")
    print("US-177 minting baseline validated: additive +1.0.")


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    game_root = resolve_game_root(args.game_root)
    package_root = args.package_root.resolve()
    minting_multiplier = decimal(args.minting_multiplier, "minting multiplier")
    food_price = decimal(args.food_price, "food price")
    food_production_divisor = decimal(
        args.food_production_divisor, "food production divisor"
    )

    validate_minting_baseline(package_root)

    run_checked(
        [
            sys.executable,
            str(repo_root / "tools/generate_us177_food_goods_manifest.py"),
            "--game-root",
            str(game_root),
            "--package-root",
            str(package_root),
            "--check",
            "--food-price",
            str(food_price),
            "--food-production-divisor",
            str(food_production_divisor),
        ]
    )
    run_checked(
        [
            sys.executable,
            str(repo_root / "tools/generate_us177_minting_overrides.py"),
            "--game-root",
            str(game_root),
            "--package-root",
            str(package_root),
            "--multiplier",
            str(minting_multiplier),
            "--check",
        ]
    )
    run_checked(
        [
            sys.executable,
            str(repo_root / "tools/postprocess_us177_minting_building_overrides.py"),
            "--common-dir",
            str(game_root / "in_game/common"),
            "--package-common-dir",
            str(package_root / "in_game/common"),
            "--multiplier",
            str(minting_multiplier),
            "--check",
        ]
    )

    print(
        "US-177 validation passed: authoritative food-good classification and exact "
        "minting identity 1 + 1 + 2*sum(vanilla modifiers) = "
        "2*(1 + sum(vanilla modifiers)). FOOD_PRICE and the food-production "
        "divisor are independently validated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

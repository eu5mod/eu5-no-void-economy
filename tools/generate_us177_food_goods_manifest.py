#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


BLOCK_START = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{")
FOOD_ASSIGNMENT = re.compile(
    r"^\s*food\s*=\s*(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\s*(?:#.*)?$"
)
FOOD_TOKEN = re.compile(r"\bfood\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the authoritative US-177 list of vanilla goods with food > 0."
    )
    parser.add_argument("--game-root", type=Path, default=None)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=Path("packages/cbp_economy_rebalance"),
    )
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def resolve_game_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    install_dir = os.environ.get("EU5_INSTALL_DIR")
    if install_dir:
        install = Path(install_dir).expanduser().resolve()
        for candidate in (install / "game", install):
            if (candidate / "in_game/common/goods").is_dir():
                return candidate
    common_dir = os.environ.get("EU5_GAME_COMMON_DIR")
    if common_dir:
        common = Path(common_dir).expanduser().resolve()
        if common.name == "common" and common.parent.name == "in_game":
            return common.parent.parent
    raise SystemExit("Pass --game-root or configure EU5_INSTALL_DIR / EU5_GAME_COMMON_DIR.")


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def decimal(raw: str, label: str) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise SystemExit(f"Invalid numeric {label}: {raw!r}") from exc
    if not value.is_finite():
        raise SystemExit(f"Non-finite numeric {label}: {raw!r}")
    return value


def format_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value.normalize(), "f")
    if "." not in text:
        return f"{text}.0"
    return text.rstrip("0").rstrip(".")


def strip_comment(line: str) -> str:
    return line.split("#", 1)[0]


def parse_goods_file(path: Path, relative_path: str) -> list[dict[str, object]]:
    source = path.read_text(encoding="utf-8-sig")
    goods: list[dict[str, object]] = []
    current_good: str | None = None
    current_start_line = 0
    current_depth = 0
    current_food: tuple[int, Decimal] | None = None

    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        code = strip_comment(raw_line)
        if current_good is None:
            match = BLOCK_START.match(code)
            if not match:
                continue
            current_good = match.group(1)
            current_start_line = line_number
            current_depth = code.count("{") - code.count("}")
            current_food = None
            if current_depth <= 0:
                current_good = None
            continue

        token_count = len(FOOD_TOKEN.findall(code))
        match = FOOD_ASSIGNMENT.match(code)
        if token_count:
            if match is None or token_count != 1:
                raise SystemExit(
                    f"Unsupported food-field syntax in {relative_path}:{line_number}: "
                    f"{raw_line.strip()}"
                )
            if current_food is not None:
                raise SystemExit(
                    f"Duplicate food field in good {current_good} at {relative_path}:{line_number}."
                )
            current_food = (line_number, decimal(match.group(1), f"food in {current_good}"))

        current_depth += code.count("{") - code.count("}")
        if current_depth > 0:
            continue

        if current_food is not None and current_food[1] > 0:
            goods.append(
                {
                    "good": current_good,
                    "food_value": format_decimal(current_food[1]),
                    "source_path": relative_path,
                    "object_start_line": current_start_line,
                    "food_line": current_food[0],
                }
            )
        current_good = None
        current_start_line = 0
        current_depth = 0
        current_food = None

    if current_good is not None:
        raise SystemExit(f"Unclosed good block {current_good} in {relative_path}.")
    return goods


def build_manifest(game_root: Path) -> bytes:
    goods_dir = game_root / "in_game/common/goods"
    if not goods_dir.is_dir():
        raise SystemExit(f"Missing vanilla goods directory: {goods_dir}")

    source_files: list[dict[str, str]] = []
    food_goods: list[dict[str, object]] = []
    for path in sorted(goods_dir.glob("*.txt")):
        if path.name.lower() == "readme.txt":
            continue
        relative_path = path.relative_to(game_root).as_posix()
        source_files.append(
            {
                "path": relative_path,
                "sha256": sha256(path.read_bytes()),
            }
        )
        food_goods.extend(parse_goods_file(path, relative_path))

    if not food_goods:
        raise SystemExit("No vanilla goods with food > 0 were found; refusing an empty manifest.")

    names = [str(item["good"]) for item in food_goods]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise SystemExit("Duplicate food-good definitions: " + ", ".join(duplicates))

    fingerprint_input = "\n".join(
        f"{item['path']}:{item['sha256']}" for item in source_files
    ).encode("utf-8")
    payload = {
        "schema_version": 1,
        "source_root": "<EU5_GAME_ROOT>/in_game/common/goods",
        "classification_rule": "food > 0",
        "food_price_endpoint": "NMarket.FOOD_PRICE",
        "source_fingerprint_sha256": sha256(fingerprint_input),
        "source_files": source_files,
        "food_good_count": len(food_goods),
        "food_goods": sorted(food_goods, key=lambda item: str(item["good"])),
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    args = parse_args()
    game_root = resolve_game_root(args.game_root)
    package_root = args.package_root.resolve()
    output = package_root / "cbp_generated/us177_food_goods_manifest.json"
    expected = build_manifest(game_root)

    if args.check:
        if not output.is_file():
            raise SystemExit(f"Missing US-177 food-goods manifest: {output}")
        if output.read_bytes() != expected:
            raise SystemExit(
                "US-177 food-goods manifest is stale. Run "
                "python3 tools/generate_us177_food_goods_manifest.py."
            )
        payload = json.loads(expected)
        print(f"US-177 food-goods manifest is current: {payload['food_good_count']} goods.")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(expected)
    payload = json.loads(expected)
    print(f"Generated US-177 food-goods manifest: {payload['food_good_count']} goods.")
    print(f"Manifest: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

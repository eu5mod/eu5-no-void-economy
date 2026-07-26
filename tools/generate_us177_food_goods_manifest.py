#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.cbg.community_balance_generator import display_path


BLOCK_START = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{")
FOOD_ASSIGNMENT = re.compile(
    r"^\s*food\s*=\s*(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\s*(?:#.*)?$"
)
FOOD_TOKEN = re.compile(r"\bfood\b")
FOOD_ASSIGNMENT_CAPTURE = re.compile(
    r"^(?P<prefix>\s*food\s*=\s*)"
    r"(?P<value>-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))"
    r"(?P<suffix>\s*(?:#.*)?)$"
)
DEFAULT_FOOD_PRICE = Decimal("0.3")
DEFAULT_FOOD_PRODUCTION_DIVISOR = Decimal("3")


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
    parser.add_argument(
        "--food-price",
        default=os.environ.get("MODEU5_US177_FOOD_PRICE", str(DEFAULT_FOOD_PRICE)),
    )
    parser.add_argument(
        "--food-production-divisor",
        default=os.environ.get(
            "MODEU5_US177_FOOD_PRODUCTION_DIVISOR",
            str(DEFAULT_FOOD_PRODUCTION_DIVISOR),
        ),
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--skip-food-overrides",
        action="store_true",
        help="Delegate Vanilla-derived food override materialization to CBG.",
    )
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


def format_generated_decimal(value: Decimal) -> str:
    # EU5's goods database accepts at most five fractional digits. Keeping the
    # generator at the same precision as Vanilla avoids malformed fixed-point
    # tokens for recurring fractions such as 3.5 / 3.
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format_decimal(rounded)


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


def build_manifest_payload(game_root: Path) -> dict[str, object]:
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
    return {
        "schema_version": 1,
        "source_root": "<EU5_GAME_ROOT>/in_game/common/goods",
        "classification_rule": "food > 0",
        "food_price_endpoint": "NMarket.FOOD_PRICE",
        "source_fingerprint_sha256": sha256(fingerprint_input),
        "source_files": source_files,
        "food_good_count": len(food_goods),
        "food_goods": sorted(food_goods, key=lambda item: str(item["good"])),
    }


def transform_food_source(
    source_path: Path,
    entries: list[dict[str, object]],
    divisor: Decimal,
) -> bytes:
    source_bytes = source_path.read_bytes()
    had_bom = source_bytes.startswith(b"\xef\xbb\xbf")
    text = source_bytes.decode("utf-8-sig")
    lines = text.splitlines(keepends=True)

    for entry in entries:
        line_index = int(entry["food_line"]) - 1
        raw_line = lines[line_index]
        newline = ""
        if raw_line.endswith("\r\n"):
            raw_line, newline = raw_line[:-2], "\r\n"
        elif raw_line.endswith("\n"):
            raw_line, newline = raw_line[:-1], "\n"
        match = FOOD_ASSIGNMENT_CAPTURE.match(raw_line)
        if not match:
            raise SystemExit(
                f"Could not rewrite food field at {source_path}:{line_index + 1}."
            )
        reduced = decimal(match.group("value"), "food production") / divisor
        lines[line_index] = (
            f"{match.group('prefix')}{format_generated_decimal(reduced)}"
            f"{match.group('suffix')}{newline}"
        )

    generated = "".join(lines).encode("utf-8")
    return (b"\xef\xbb\xbf" + generated) if had_bom else generated


def render_food_price_define(food_price: Decimal) -> bytes:
    return (
        "# Generated by tools/generate_us177_food_goods_manifest.py.\n"
        "# Market and resource balance values remain independent from food production.\n"
        "NMarket = {\n"
        f"\tFOOD_PRICE = {format_generated_decimal(food_price)}\n"
        "\n"
        "\t# VANILLA = 0.05. Prices close twice as much of the target-price gap each month.\n"
        "\tMONTHLY_PRICE_CHANGE = 0.10\n"
        "}\n"
        "\n"
        "NLocation = {\n"
        "\tSUBSISTENCE_AGRICULTURE = 1.0\n"
        "}\n"
    ).encode("utf-8")


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    temporary.replace(path)


def previous_generated_override_paths(manifest_path: Path) -> set[str]:
    if not manifest_path.is_file():
        return set()
    try:
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"Could not read previous US-177 food manifest: {manifest_path}") from exc
    return {
        str(item["path"])
        for item in previous.get("generated_food_overrides", [])
        if isinstance(item, dict) and "path" in item
    }


def main() -> int:
    args = parse_args()
    game_root = resolve_game_root(args.game_root)
    package_root = args.package_root.resolve()
    food_price = decimal(args.food_price, "food price")
    divisor = decimal(args.food_production_divisor, "food production divisor")
    if food_price <= 0:
        raise SystemExit("food price must be greater than zero")
    if divisor <= 0:
        raise SystemExit("food production divisor must be greater than zero")

    output = package_root / "cbp_generated/us177_food_goods_manifest.json"
    previous_override_paths = previous_generated_override_paths(output)
    payload = build_manifest_payload(game_root)
    grouped_entries: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry in payload["food_goods"]:
        grouped_entries[str(entry["source_path"])].append(entry)

    generated_overrides: dict[str, bytes] = {}
    override_records: list[dict[str, object]] = []
    for relative_path, entries in sorted(grouped_entries.items()):
        generated = transform_food_source(game_root / relative_path, entries, divisor)
        generated_overrides[relative_path] = generated
        override_records.append(
            {
                "path": relative_path,
                "generated_sha256": sha256(generated),
                "food_assignment_count": len(entries),
            }
        )

    payload["configured_food_price"] = format_generated_decimal(food_price)
    payload["food_production_divisor"] = format_generated_decimal(divisor)
    payload["generated_food_overrides"] = override_records
    payload["food_override_materializer"] = (
        "community_balance_generator"
        if args.skip_food_overrides
        else "generate_us177_food_goods_manifest"
    )
    expected = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    define_path = (
        package_root
        / "loading_screen/common/defines/cbp_market_resource_balance_defines.txt"
    )
    expected_define = render_food_price_define(food_price)

    if args.check:
        if not output.is_file():
            raise SystemExit(f"Missing US-177 food-goods manifest: {output}")
        if output.read_bytes() != expected:
            raise SystemExit(
                "US-177 food-goods manifest is stale. Run "
                "python3 tools/generate_us177_food_goods_manifest.py."
            )
        if not define_path.is_file() or define_path.read_bytes() != expected_define:
            raise SystemExit("US-177 FOOD_PRICE define is missing or stale.")
        for relative_path, generated in generated_overrides.items():
            generated_path = package_root / relative_path
            if not generated_path.is_file() or generated_path.read_bytes() != generated:
                raise SystemExit(f"US-177 food production override is stale: {relative_path}")
        payload = json.loads(expected)
        print(
            f"US-177 food configuration is current: {payload['food_good_count']} goods, "
            f"FOOD_PRICE={payload['configured_food_price']}, "
            f"production divisor={payload['food_production_divisor']}."
        )
        return 0

    write_atomic(output, expected)
    write_atomic(define_path, expected_define)
    if not args.skip_food_overrides:
        current_override_paths = set(generated_overrides)
        for stale_path in sorted(previous_override_paths - current_override_paths):
            candidate = package_root / stale_path
            if candidate.is_file():
                candidate.unlink()
        for relative_path, generated in generated_overrides.items():
            generated_path = package_root / relative_path
            if generated_path.exists() and relative_path not in previous_override_paths:
                raise SystemExit(
                    "Refusing to overwrite a package file not owned by the US-177 food "
                    f"manifest: {relative_path}"
                )
            write_atomic(generated_path, generated)
    payload = json.loads(expected)
    print(
        f"Generated US-177 food configuration: {payload['food_good_count']} goods, "
        f"FOOD_PRICE={payload['configured_food_price']}, "
        f"production divisor={payload['food_production_divisor']}."
    )
    print(f"Manifest: {display_path(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.cbg.community_balance_generator import display_path


MODIFIER = "minting_income_factor"
DEFAULT_MULTIPLIER = Decimal("2")
MANIFEST_SCHEMA = 1
SCAN_ROOTS = (
    PurePosixPath("in_game/common"),
    PurePosixPath("in_game/events"),
    PurePosixPath("main_menu/common/static_modifiers"),
    PurePosixPath("main_menu/common/auto_modifiers"),
)
# Building definitions are already owned by the composed US-07/US-09 exact-path
# generator. That generator scales minting_income_factor in the same output file.
DELEGATED_PREFIXES = (PurePosixPath("in_game/common/building_types"),)
TOKEN = re.compile(rf"\b{re.escape(MODIFIER)}\b")
NUMERIC_ASSIGNMENT = re.compile(
    rf"(?<![A-Za-z0-9_])({re.escape(MODIFIER)}[ \t]*=[ \t]*)"
    r"(-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))"
    r"(?=$|[ \t}\r\n])"
)
BLOCK_START = re.compile(r"^\s*([A-Za-z0-9_.:-]+)\s*=\s*\{")


@dataclass(frozen=True)
class Occurrence:
    line: int
    object_path: str
    old: str
    new: str


@dataclass(frozen=True)
class GeneratedFile:
    relative_path: PurePosixPath
    source_sha256: str
    generated_bytes: bytes
    occurrences: tuple[Occurrence, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate exact-path Rebalance Economy overrides that multiply every "
            "numeric vanilla minting_income_factor source."
        )
    )
    parser.add_argument(
        "--game-root",
        type=Path,
        default=None,
        help="EU5 game root containing in_game/, main_menu/, and loading_screen/.",
    )
    parser.add_argument(
        "--package-root",
        type=Path,
        default=Path("packages/cbp_economy_rebalance"),
    )
    parser.add_argument("--multiplier", default=str(DEFAULT_MULTIPLIER))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Manifest path; defaults below the package root.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated files or the manifest are missing or stale.",
    )
    return parser.parse_args()


def resolve_game_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()

    install_dir = os.environ.get("EU5_INSTALL_DIR")
    if install_dir:
        install_root = Path(install_dir).expanduser().resolve()
        for candidate in (install_root / "game", install_root):
            if (candidate / "in_game/common").is_dir():
                return candidate

    common_dir = os.environ.get("EU5_GAME_COMMON_DIR")
    if common_dir:
        common = Path(common_dir).expanduser().resolve()
        if common.name == "common" and common.parent.name == "in_game":
            return common.parent.parent

    raise SystemExit(
        "Could not locate the EU5 game root. Pass --game-root, set EU5_INSTALL_DIR, "
        "or set EU5_GAME_COMMON_DIR."
    )


def parse_multiplier(raw: str) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise SystemExit(f"Multiplier must be numeric; got {raw!r}.") from exc
    if not value.is_finite() or value < 0:
        raise SystemExit(f"Multiplier must be a finite non-negative number; got {raw!r}.")
    return value


def format_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value.normalize(), "f")
    if "." not in text:
        return f"{text}.0"
    return text.rstrip("0").rstrip(".")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def is_delegated(relative_path: PurePosixPath) -> bool:
    return any(
        relative_path == prefix or prefix in relative_path.parents
        for prefix in DELEGATED_PREFIXES
    )


def iter_source_files(game_root: Path) -> list[tuple[PurePosixPath, Path]]:
    discovered: dict[PurePosixPath, Path] = {}
    for relative_root in SCAN_ROOTS:
        root = game_root / Path(relative_root)
        if not root.is_dir():
            continue
        for source_file in sorted(root.rglob("*.txt")):
            relative_path = PurePosixPath(source_file.relative_to(game_root).as_posix())
            if is_delegated(relative_path):
                continue
            discovered[relative_path] = source_file
    return sorted(discovered.items(), key=lambda item: item[0].as_posix())


def split_comment(line: str) -> tuple[str, str]:
    if "#" not in line:
        return line, ""
    code, comment = line.split("#", 1)
    return code, f"#{comment}"


def transform_file(relative_path: PurePosixPath, source_file: Path, multiplier: Decimal) -> GeneratedFile | None:
    source_bytes = source_file.read_bytes()
    has_bom = source_bytes.startswith(b"\xef\xbb\xbf")
    try:
        source_text = source_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"Vanilla source is not UTF-8: {source_file}") from exc

    lines = source_text.splitlines(keepends=True)
    transformed_lines: list[str] = []
    occurrences: list[Occurrence] = []
    object_stack: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        line_without_newline = line.rstrip("\r\n")
        newline = line[len(line_without_newline) :]
        code, comment = split_comment(line_without_newline)
        stripped = code.lstrip()

        block_match = BLOCK_START.match(code)
        path_for_line = "/".join(object_stack)
        if block_match:
            path_for_line = "/".join([*object_stack, block_match.group(1)])

        token_count = len(TOKEN.findall(code))
        replacements = 0

        def replace(match: re.Match[str]) -> str:
            nonlocal replacements
            old_raw = match.group(2)
            old_value = Decimal(old_raw)
            new_raw = format_decimal(old_value * multiplier)
            occurrences.append(
                Occurrence(
                    line=line_number,
                    object_path=path_for_line or "<root>",
                    old=old_raw,
                    new=new_raw,
                )
            )
            replacements += 1
            return f"{match.group(1)}{new_raw}"

        transformed_code = NUMERIC_ASSIGNMENT.sub(replace, code)
        if token_count != replacements:
            raise SystemExit(
                f"Unsupported {MODIFIER} syntax in {relative_path}:{line_number}: "
                f"{line_without_newline.strip()}"
            )

        transformed_lines.append(f"{transformed_code}{comment}{newline}")

        # Lightweight Clausewitz/Jomini object-path tracking. It is used for the
        # audit manifest only; transformation safety is enforced by exact token
        # and numeric-assignment checks above.
        opens = code.count("{")
        closes = code.count("}")
        if block_match and opens > closes:
            object_stack.append(block_match.group(1))
            opens -= 1
        net_closes = max(0, closes - opens)
        for _ in range(net_closes):
            if object_stack:
                object_stack.pop()

    if not occurrences:
        return None

    generated_text = "".join(transformed_lines)
    if relative_path == PurePosixPath("main_menu/common/static_modifiers/country.txt"):
        # This legacy modifier is rejected by the current EU5 build. Keep the
        # exact-path US-177 override compatible when composing from Vanilla.
        generated_text = re.sub(
            r"^[ \t]*building_upkeep_multiplier[ \t]*=.*(?:\r?\n|$)",
            "",
            generated_text,
            flags=re.MULTILINE,
        )
    generated_text = "\n".join(
        line.rstrip(" \t") for line in generated_text.splitlines()
    ) + "\n"
    generated_bytes = generated_text.encode("utf-8")
    if has_bom:
        generated_bytes = b"\xef\xbb\xbf" + generated_bytes

    return GeneratedFile(
        relative_path=relative_path,
        source_sha256=sha256_bytes(source_bytes),
        generated_bytes=generated_bytes,
        occurrences=tuple(occurrences),
    )


def build_outputs(game_root: Path, multiplier: Decimal) -> list[GeneratedFile]:
    outputs: list[GeneratedFile] = []
    for relative_path, source_file in iter_source_files(game_root):
        generated = transform_file(relative_path, source_file, multiplier)
        if generated is not None:
            outputs.append(generated)
    if not outputs:
        raise SystemExit(
            f"No numeric {MODIFIER} assignments were found below {game_root}. "
            "Refusing to produce an empty override set."
        )
    return outputs


def manifest_payload(outputs: list[GeneratedFile], multiplier: Decimal) -> dict[str, object]:
    fingerprint_input = "\n".join(
        f"{item.relative_path.as_posix()}:{item.source_sha256}" for item in outputs
    ).encode("utf-8")
    return {
        "schema_version": MANIFEST_SCHEMA,
        "source_root": "<EU5_GAME_ROOT>",
        "source_fingerprint_sha256": sha256_bytes(fingerprint_input),
        "modifier": MODIFIER,
        "multiplier": format_decimal(multiplier),
        "generated_file_count": len(outputs),
        "occurrence_count": sum(len(item.occurrences) for item in outputs),
        "delegated_prefixes": [prefix.as_posix() for prefix in DELEGATED_PREFIXES],
        "files": [
            {
                "path": item.relative_path.as_posix(),
                "source_sha256": item.source_sha256,
                "generated_sha256": sha256_bytes(item.generated_bytes),
                "occurrences": [
                    {
                        "line": occurrence.line,
                        "object_path": occurrence.object_path,
                        "old": occurrence.old,
                        "new": occurrence.new,
                    }
                    for occurrence in item.occurrences
                ],
            }
            for item in outputs
        ],
    }


def render_manifest(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def safe_output_path(package_root: Path, relative_path: PurePosixPath) -> Path:
    output = (package_root / Path(relative_path)).resolve()
    package = package_root.resolve()
    try:
        output.relative_to(package)
    except ValueError as exc:
        raise SystemExit(f"Refusing to write outside package root: {output}") from exc
    return output


def read_previous_paths(manifest_path: Path) -> set[PurePosixPath]:
    if not manifest_path.is_file():
        return set()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read previous US-177 manifest: {manifest_path}") from exc
    paths: set[PurePosixPath] = set()
    for item in payload.get("files", []):
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.add(PurePosixPath(item["path"]))
    return paths


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def check_outputs(
    package_root: Path,
    manifest_path: Path,
    outputs: list[GeneratedFile],
    expected_manifest: bytes,
) -> None:
    failures: list[str] = []
    expected_paths = {item.relative_path for item in outputs}
    previous_paths = read_previous_paths(manifest_path)

    for item in outputs:
        output_path = safe_output_path(package_root, item.relative_path)
        if not output_path.is_file():
            failures.append(f"missing generated override: {item.relative_path}")
        elif output_path.read_bytes() != item.generated_bytes:
            failures.append(f"stale generated override: {item.relative_path}")

    for stale in sorted(previous_paths - expected_paths, key=lambda path: path.as_posix()):
        if safe_output_path(package_root, stale).exists():
            failures.append(f"stale generated path retained: {stale}")

    if not manifest_path.is_file():
        failures.append(f"missing manifest: {manifest_path}")
    elif manifest_path.read_bytes() != expected_manifest:
        failures.append(f"stale manifest: {manifest_path}")

    if failures:
        raise SystemExit("US-177 minting override validation failed:\n- " + "\n- ".join(failures))


def write_outputs(
    package_root: Path,
    manifest_path: Path,
    outputs: list[GeneratedFile],
    expected_manifest: bytes,
) -> None:
    expected_paths = {item.relative_path for item in outputs}
    previous_paths = read_previous_paths(manifest_path)

    for stale in sorted(previous_paths - expected_paths, key=lambda path: path.as_posix()):
        stale_path = safe_output_path(package_root, stale)
        if stale_path.is_file():
            stale_path.unlink()

    for item in outputs:
        output_path = safe_output_path(package_root, item.relative_path)
        if output_path.exists() and item.relative_path not in previous_paths:
            raise SystemExit(
                f"Refusing to overwrite a package file not owned by the US-177 manifest: "
                f"{item.relative_path}"
            )
        write_atomic(output_path, item.generated_bytes)

    write_atomic(manifest_path, expected_manifest)


def main() -> int:
    args = parse_args()
    game_root = resolve_game_root(args.game_root)
    package_root = args.package_root.resolve()
    multiplier = parse_multiplier(args.multiplier)
    manifest_path = (
        args.manifest.resolve()
        if args.manifest is not None
        else package_root / "cbp_generated/us177_minting_income_manifest.json"
    )

    if not (game_root / "in_game/common").is_dir():
        raise SystemExit(f"Missing vanilla in_game/common below game root: {game_root}")

    outputs = build_outputs(game_root, multiplier)
    payload = manifest_payload(outputs, multiplier)
    expected_manifest = render_manifest(payload)

    if args.check:
        check_outputs(package_root, manifest_path, outputs, expected_manifest)
        print(
            f"US-177 minting overrides are current: {len(outputs)} files, "
            f"{payload['occurrence_count']} occurrences."
        )
        return 0

    write_outputs(package_root, manifest_path, outputs, expected_manifest)
    print(
        f"Generated US-177 minting overrides: {len(outputs)} files, "
        f"{payload['occurrence_count']} occurrences."
    )
    print(f"Manifest: {display_path(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

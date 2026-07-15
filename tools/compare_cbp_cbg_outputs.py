#!/usr/bin/env python3
"""Compare #188 generator outputs with a CBG candidate semantically."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    from tools.community_balance_generator import (
        ASSIGNMENT,
        BLOCK_ASSIGNMENT,
        field_matches,
        locate_object,
        matching_brace_line,
        scan_objects,
    )
except ModuleNotFoundError:
    from community_balance_generator import (
        ASSIGNMENT,
        BLOCK_ASSIGNMENT,
        field_matches,
        locate_object,
        matching_brace_line,
        scan_objects,
    )

from generate_cbp_community_balance_spec import EVENT_FIELDS, MONTHLY_FIELDS, PROFIT_FIELDS


NUMBER = re.compile(r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)")


@dataclass(frozen=True)
class Expression:
    base: str | None
    factor: Decimal

    def render(self) -> str:
        return str(self.factor.normalize()) if self.base is None else f"{self.base}*{self.factor.normalize()}"


def direct_scalar(lines: list[str], obj: Any, field: str) -> str | None:
    matches = field_matches(lines, obj, field)
    if len(matches) != 1:
        return None
    match = ASSIGNMENT.match(lines[matches[0]].rstrip("\r\n"))
    return match.group("value").strip() if match else None


def parse_definitions(root: Path) -> dict[str, tuple[str, Any]]:
    definitions: dict[str, tuple[str, Any]] = {}
    directory = root / "main_menu/common/script_values"
    if not directory.is_dir():
        return definitions
    for path in sorted(directory.glob("*.txt")):
        lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        depth = 0
        for line in lines:
            code = line.split("#", 1)[0]
            if depth == 0 and (match := ASSIGNMENT.match(line.rstrip("\r\n"))):
                definitions[match.group("field")] = ("scalar", match.group("value").strip())
            depth += code.count("{") - code.count("}")
        for obj in scan_objects(lines):
            if len(obj.path) != 1:
                continue
            value = direct_scalar(lines, obj, "value")
            if value is None:
                continue
            multiply = direct_scalar(lines, obj, "multiply") or "1"
            divide = direct_scalar(lines, obj, "divide") or "1"
            definitions[obj.path[0]] = ("formula", (value, multiply, divide))
    return definitions


def merged_definitions(game_root: Path, overlay_root: Path) -> dict[str, tuple[str, Any]]:
    result = parse_definitions(game_root)
    result.update(parse_definitions(overlay_root))
    return result


def resolve(value: str, definitions: dict[str, tuple[str, Any]], seen: tuple[str, ...] = ()) -> Expression:
    if NUMBER.fullmatch(value):
        return Expression(None, Decimal(value))
    if value in seen:
        return Expression(f"cycle:{value}", Decimal(1))
    definition = definitions.get(value)
    if definition is None:
        return Expression(value, Decimal(1))
    kind, payload = definition
    if kind == "scalar":
        return resolve(payload, definitions, (*seen, value))
    source, multiply, divide = payload
    base = resolve(source, definitions, (*seen, value))
    if not NUMBER.fullmatch(multiply) or not NUMBER.fullmatch(divide):
        return Expression(f"formula:{value}", Decimal(1))
    return Expression(base.base, base.factor * Decimal(multiply) / Decimal(divide))


def block_expression(lines: list[str], start: int, definitions: dict[str, tuple[str, Any]]) -> Expression:
    end = matching_brace_line(lines, start)
    block_lines = lines[start : end + 1]
    objects = scan_objects(block_lines)
    root = next(obj for obj in objects if len(obj.path) == 1)
    value = direct_scalar(block_lines, root, "value")
    multiply = direct_scalar(block_lines, root, "multiply") or "1"
    divide = direct_scalar(block_lines, root, "divide") or "1"
    if value is None or not NUMBER.fullmatch(multiply) or not NUMBER.fullmatch(divide):
        normalized = " ".join(
            token
            for line in block_lines
            for token in line.split("#", 1)[0].split()
        )
        return Expression(f"block:{normalized}", Decimal(1))
    base = resolve(value, definitions)
    return Expression(base.base, base.factor * Decimal(multiply) / Decimal(divide))


def political_occurrences(
    path: Path, fields: set[str], definitions: dict[str, tuple[str, Any]]
) -> list[tuple[str, Expression]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    found: list[tuple[int, int, str, Expression]] = []
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        scalar = ASSIGNMENT.match(body)
        block = BLOCK_ASSIGNMENT.match(body)
        if scalar and scalar.group("field") in fields:
            found.append((index, 0, scalar.group("field"), resolve(scalar.group("value").strip(), definitions)))
        elif block and block.group("field") in fields:
            found.append((index, 0, block.group("field"), block_expression(lines, index, definitions)))
        code = line.split("#", 1)[0]
        if scalar or block:
            continue
        for field in fields:
            pattern = re.compile(
                rf"(?<![A-Za-z0-9_]){re.escape(field)}[ \t]*=[ \t]*"
                r"(?P<value>-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)|[A-Za-z_][A-Za-z0-9_.:-]*)"
            )
            for match in pattern.finditer(code):
                found.append((index, match.start(), field, resolve(match.group("value"), definitions)))
    return [(field, expression) for _line, _column, field, expression in sorted(found)]


def scalar_state(path: Path, object_path: str, field: str) -> tuple[str, str | None]:
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    obj = locate_object(lines, tuple(part for part in object_path.split("/") if part))
    matches = field_matches(lines, obj, field)
    if len(matches) == 1:
        match = ASSIGNMENT.match(lines[matches[0]].rstrip("\r\n"))
        if match:
            return "present", match.group("value").strip()
    commented = re.compile(rf"^\s*#\s*{re.escape(field)}\s*=\s*([^#\s]+)")
    values = []
    for line in lines[obj.start + 1 : obj.end]:
        if match := commented.match(line):
            values.append(match.group(1))
    if len(values) == 1:
        return "commented", values[0]
    return "absent", None


def compare(args: argparse.Namespace) -> dict[str, Any]:
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    political_manifest = json.loads(
        (args.reference_root / "cbp_generated/political_reward_overrides_manifest.json").read_text()
    )
    reference_defs = merged_definitions(args.game_root, args.reference_root)
    candidate_defs = merged_definitions(args.game_root, args.candidate_root)
    mismatches: list[dict[str, Any]] = []
    checked = {"political_files": 0, "scalar_targets": 0}

    fields = set(EVENT_FIELDS) | set(MONTHLY_FIELDS)
    for entry in political_manifest.get("files", []):
        if entry.get("package_relative"):
            continue
        relative = Path("in_game") / entry["path"]
        vanilla = args.game_root / relative
        if vanilla.is_file() and not political_occurrences(vanilla, fields, reference_defs):
            # A generated manifest can lag a Vanilla patch by one run.
            continue
        reference = args.reference_root / relative
        candidate = args.candidate_root / relative
        if not reference.is_file() or not candidate.is_file():
            mismatches.append({"surface": "political", "path": str(relative), "reason": "missing output"})
            continue
        expected = political_occurrences(reference, fields, reference_defs)
        actual = political_occurrences(candidate, fields, candidate_defs)
        checked["political_files"] += 1
        if expected != actual:
            first_difference = next(
                (
                    {
                        "index": index,
                        "reference": (left[0], left[1].render()),
                        "candidate": (right[0], right[1].render()),
                    }
                    for index, (left, right) in enumerate(zip(expected, actual))
                    if left != right
                ),
                None,
            )
            mismatches.append({
                "surface": "political",
                "path": str(relative),
                "reason": "effective occurrence mismatch",
                "reference_count": len(expected),
                "candidate_count": len(actual),
                "first_reference": [(field, expr.render()) for field, expr in expected[:5]],
                "first_candidate": [(field, expr.render()) for field, expr in actual[:5]],
                "first_difference": first_difference,
            })

    for transformation in spec.get("transformations", []):
        if transformation.get("object") in {"**", ""} and transformation.get("field") not in PROFIT_FIELDS:
            continue
        relative = Path(transformation["file"])
        reference = args.reference_root / relative
        if relative.as_posix() == "main_menu/common/static_modifiers/location.txt":
            reference = args.repo_root / "main_menu/common/static_modifiers/cbp_location.txt"
        candidate = args.candidate_root / relative
        if not reference.is_file() or not candidate.is_file():
            mismatches.append({"surface": "scalar", "path": str(relative), "reason": "missing output"})
            continue
        object_path = transformation.get("object", "")
        field = transformation["field"]
        reference_state = scalar_state(reference, object_path, field)
        candidate_state = scalar_state(candidate, object_path, field)
        checked["scalar_targets"] += 1
        if reference_state != candidate_state:
            mismatches.append({
                "surface": "scalar",
                "path": str(relative),
                "object": object_path,
                "field": field,
                "reference": reference_state,
                "candidate": candidate_state,
            })

    return {
        "schema_version": 1,
        "reference": "PR #188 generated package",
        "candidate": "Community Balance Generator",
        "checked": checked,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:200],
        "known_structural_gaps": spec.get("parity_contract", {}).get("known_structural_gaps", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, default=Path("tools/specs/cbp_pr188_balance.generated.json"))
    parser.add_argument("--report", type=Path, default=Path("/tmp/cbp-cbg-parity-report.json"))
    args = parser.parse_args()
    report = compare(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"CBP/CBG parity: checked={report['checked']} mismatches={report['mismatch_count']}")
    print(f"Report: {args.report}")
    return 1 if report["mismatch_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

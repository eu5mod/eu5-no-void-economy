#!/usr/bin/env python3
"""Generate one auditable EU5 compatibility mod from declarative balance specs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any


ASSIGNMENT = re.compile(
    r"^(?P<indent>[ \t]*)(?P<field>[A-Za-z0-9_.:-]+)[ \t]*=[ \t]*"
    r"(?P<value>[^#{\s][^#\r\n]*?)[ \t]*(?P<comment>#.*)?$"
)
BLOCK_START = re.compile(r"^[ \t]*(?P<name>[A-Za-z0-9_.:-]+)[ \t]*=[ \t]*\{")
BLOCK_ASSIGNMENT = re.compile(
    r"^(?P<indent>[ \t]*)(?P<field>[A-Za-z0-9_.:-]+)[ \t]*=[ \t]*\{(?P<comment>[ \t]*#.*)?$"
)
SAFE_SCALAR = re.compile(r"[A-Za-z0-9_.:-]+")
SUPPORTED_OPERATIONS = {
    "replace", "multiply", "add", "clamp", "comment_out", "remove",
    "add_field", "add_custom", "upsert_block",
}
TERMINAL_OPERATIONS = {"comment_out", "remove", "upsert_block"}


@dataclass(frozen=True)
class Target:
    file: PurePosixPath
    object_path: tuple[str, ...]
    field: str


@dataclass(frozen=True)
class Intent:
    owner: str
    target: Target
    operation: str
    value: Any
    conflict: str
    position_after: str | None
    source_spec: str
    sequence: int
    occurrences: str
    on_missing: str
    exclude_values: tuple[str, ...]
    where: dict[str, list[dict[str, str]]]
    exclude_objects: tuple[str, ...]


@dataclass
class LocatedObject:
    path: tuple[str, ...]
    start: int
    end: int
    indent: str


def decimal(raw: Any, label: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be numeric; got {raw!r}") from exc
    if not value.is_finite():
        raise ValueError(f"{label} must be finite; got {raw!r}")
    return value


def render_number(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def render_scalar(raw: Any, label: str) -> str:
    if isinstance(raw, bool):
        return "yes" if raw else "no"
    if isinstance(raw, (int, float, Decimal)):
        return render_number(decimal(raw, label))
    value = str(raw)
    if not SAFE_SCALAR.fullmatch(value):
        raise ValueError(f"{label} must be one safe scalar token; got {raw!r}")
    return value


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_object_path(raw: Any) -> tuple[str, ...]:
    if isinstance(raw, str):
        return tuple(part for part in raw.split("/") if part)
    if isinstance(raw, list) and all(isinstance(part, str) for part in raw):
        return tuple(raw)
    raise ValueError("object must be a slash-separated string or a string array")


def load_intents(spec_paths: list[Path], game_root: Path) -> tuple[list[Intent], dict[str, str]]:
    intents: list[Intent] = []
    custom_fields: dict[str, str] = {}
    sequence = 0
    for spec_path in spec_paths:
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ValueError(f"{spec_path}: schema_version must be 1")
        owner = payload.get("mod_id")
        if not isinstance(owner, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", owner):
            raise ValueError(f"{spec_path}: mod_id must be a stable lowercase identifier")
        for field, declaration in payload.get("custom_fields", {}).items():
            if field in custom_fields and custom_fields[field] != owner:
                raise ValueError(
                    f"Custom field {field!r} is declared by both {custom_fields[field]} and {owner}"
                )
            if declaration not in {"modifier", "scripted_value", "engine_extension"}:
                raise ValueError(f"{spec_path}: unsupported declaration for custom field {field}")
            custom_fields[field] = owner
        transformations = payload.get("transformations")
        if not isinstance(transformations, list):
            raise ValueError(f"{spec_path}: transformations must be an array")
        for raw in transformations:
            operation = raw.get("operation")
            if operation not in SUPPORTED_OPERATIONS:
                raise ValueError(f"{spec_path}: unsupported operation {operation!r}")
            selectors = raw.get("file")
            if isinstance(selectors, str):
                selectors = [selectors]
            if not isinstance(selectors, list) or not selectors or not all(
                isinstance(pattern, str)
                and not pattern.startswith("/")
                and ".." not in PurePosixPath(pattern).parts
                for pattern in selectors
            ):
                raise ValueError(f"{spec_path}: file must be a safe path/glob or a non-empty array of them")
            matches = sorted({
                PurePosixPath(path.relative_to(game_root).as_posix())
                for pattern in selectors
                for path in game_root.glob(pattern)
                if path.is_file()
            })
            excluded_selectors = raw.get("exclude_files", [])
            if not isinstance(excluded_selectors, list) or not all(
                isinstance(pattern, str)
                and not pattern.startswith("/")
                and ".." not in PurePosixPath(pattern).parts
                for pattern in excluded_selectors
            ):
                raise ValueError(f"{spec_path}: exclude_files must be an array of safe paths/globs")
            excluded_files = {
                PurePosixPath(path.relative_to(game_root).as_posix())
                for pattern in excluded_selectors
                for path in game_root.glob(pattern)
                if path.is_file()
            }
            matches = [relative for relative in matches if relative not in excluded_files]
            if not matches:
                raise ValueError(f"{spec_path}: file selector matched nothing: {selectors}")
            field = raw.get("field")
            if not isinstance(field, str) or not field:
                raise ValueError(f"{spec_path}: field is required")
            if operation == "add_custom" and custom_fields.get(field) != owner:
                raise ValueError(
                    f"{spec_path}: add_custom field {field!r} must be declared by the same mod"
                )
            conflict = raw.get("conflict", "error")
            if conflict not in {"error", "compose", "last_wins"}:
                raise ValueError(f"{spec_path}: invalid conflict policy {conflict!r}")
            position = raw.get("position", {})
            position_after = position.get("after") if isinstance(position, dict) else None
            occurrences = raw.get("occurrences", "one")
            if occurrences not in {"one", "all"}:
                raise ValueError(f"{spec_path}: occurrences must be 'one' or 'all'")
            object_path = normalize_object_path(raw.get("object", ""))
            if object_path == ("**",) and occurrences != "all":
                raise ValueError(f"{spec_path}: object '**' requires occurrences='all'")
            if operation in {"add_field", "add_custom"} and occurrences == "all":
                raise ValueError(f"{spec_path}: insertion operations cannot target all occurrences")
            on_missing = raw.get("on_missing", "error")
            if on_missing not in {"error", "skip"}:
                raise ValueError(f"{spec_path}: on_missing must be 'error' or 'skip'")
            excluded = raw.get("exclude_values", [])
            if not isinstance(excluded, list) or not all(
                isinstance(value, str) and SAFE_SCALAR.fullmatch(value) for value in excluded
            ):
                raise ValueError(f"{spec_path}: exclude_values must be an array of safe scalar tokens")
            where = raw.get("where", {})
            if isinstance(where, dict):
                where = {
                    key: [value] if isinstance(value, dict) else value
                    for key, value in where.items()
                }
            if not isinstance(where, dict) or any(
                key not in {"inside", "not_inside"}
                or not isinstance(clauses, list)
                or not all(
                    isinstance(clause, dict)
                    and all(isinstance(k, str) and isinstance(v, str) for k, v in clause.items())
                    for clause in clauses
                )
                for key, clauses in where.items()
            ):
                raise ValueError(f"{spec_path}: where supports scalar inside/not_inside maps")
            exclude_objects = raw.get("exclude_objects", [])
            if not isinstance(exclude_objects, list) or not all(
                isinstance(value, str) and SAFE_SCALAR.fullmatch(value) for value in exclude_objects
            ):
                raise ValueError(f"{spec_path}: exclude_objects must contain safe top-level object names")
            for relative in matches:
                sequence += 1
                intents.append(Intent(
                    owner=owner,
                    target=Target(relative, object_path, field),
                    operation=operation,
                    value=raw.get("value"),
                    conflict=conflict,
                    position_after=position_after,
                    source_spec=spec_path.name,
                    sequence=sequence,
                    occurrences=occurrences,
                    on_missing=on_missing,
                    exclude_values=tuple(excluded),
                    where=where,
                    exclude_objects=tuple(exclude_objects),
                ))
    return intents, custom_fields


def validate_conflicts(intents: list[Intent]) -> None:
    grouped: dict[Target, list[Intent]] = {}
    for intent in intents:
        grouped.setdefault(intent.target, []).append(intent)
    for target, chain in grouped.items():
        owners = {item.owner for item in chain}
        if len(owners) < 2:
            continue
        if any(item.conflict == "error" for item in chain):
            raise ValueError(f"Unresolved multi-mod conflict at {target}: owners={sorted(owners)}")
        terminal = [item for item in chain if item.operation in TERMINAL_OPERATIONS]
        if terminal and len(chain) > 1 and chain[-1].conflict != "last_wins":
            raise ValueError(f"Terminal operation cannot be composed at {target}")


def scan_objects(lines: list[str]) -> list[LocatedObject]:
    objects: list[LocatedObject] = []
    stack: list[tuple[str, int, str, int]] = []
    depth = 0
    for index, line in enumerate(lines):
        code = line.split("#", 1)[0]
        match = BLOCK_START.match(code)
        opens = code.count("{")
        closes = code.count("}")
        if match:
            indent = line[: len(line) - len(line.lstrip(" \t"))]
            stack.append((match.group("name"), index, indent, depth + 1))
        depth += opens - closes
        while stack and depth < stack[-1][3]:
            names = tuple(entry[0] for entry in stack)
            name, start, indent, _object_depth = stack.pop()
            objects.append(LocatedObject(names, start, index, indent))
    if stack:
        raise ValueError("Unbalanced object braces")
    return objects


def locate_object(lines: list[str], path: tuple[str, ...]) -> LocatedObject:
    if not path:
        return LocatedObject((), -1, len(lines), "")
    matches = [item for item in scan_objects(lines) if item.path == path]
    if len(matches) != 1:
        raise ValueError(f"Object {'/'.join(path)!r} matched {len(matches)} blocks; expected exactly one")
    return matches[0]


def field_matches(lines: list[str], obj: LocatedObject, field: str) -> list[int]:
    result: list[int] = []
    child_depth = 0
    for index in range(obj.start + 1, obj.end):
        code = lines[index].split("#", 1)[0]
        if child_depth == 0:
            match = ASSIGNMENT.match(lines[index].rstrip("\r\n"))
            block = BLOCK_ASSIGNMENT.match(lines[index].rstrip("\r\n"))
            if (match and match.group("field") == field) or (
                block and block.group("field") == field
            ):
                result.append(index)
        child_depth += code.count("{") - code.count("}")
    return result


def all_field_matches(lines: list[str], field: str) -> list[int]:
    result = []
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        scalar = ASSIGNMENT.match(body)
        block = BLOCK_ASSIGNMENT.match(body)
        if (scalar and scalar.group("field") == field) or (
            block and block.group("field") == field
        ):
            result.append(index)
    return result


def matching_brace_line(lines: list[str], start: int) -> int:
    depth = 0
    for index in range(start, len(lines)):
        code = lines[index].split("#", 1)[0]
        depth += code.count("{") - code.count("}")
        if depth == 0:
            return index
    raise ValueError(f"Unclosed value block at line {start + 1}")


def index_matches_where(
    lines: list[str], index: int, where: dict[str, list[dict[str, str]]], objects: list[LocatedObject]
) -> bool:
    if not where:
        return True
    containing = [obj for obj in objects if obj.start < index < obj.end]

    def object_has(obj: LocatedObject, field: str, value: str) -> bool:
        for match_index in field_matches(lines, obj, field):
            match = ASSIGNMENT.match(lines[match_index].rstrip("\r\n"))
            if match and match.group("value").strip() == value:
                return True
        return False

    for clause in where.get("inside", []):
        if not all(any(object_has(obj, field, value) for obj in containing) for field, value in clause.items()):
            return False
    for clause in where.get("not_inside", []):
        if all(any(object_has(obj, field, value) for obj in containing) for field, value in clause.items()):
            return False
    return True


def index_inside_excluded_object(
    index: int, names: tuple[str, ...], objects: list[LocatedObject]
) -> bool:
    return any(
        obj.path and obj.path[0] in names and obj.start < index < obj.end
        for obj in objects
    )


def alias_name(intent: Intent, source: str, factor: Any) -> str:
    owner = re.sub(r"[^a-z0-9_]+", "_", intent.owner.lower()).strip("_")
    field = re.sub(r"[^a-z0-9_]+", "_", intent.target.field.lower()).strip("_")
    digest = hashlib.sha256(
        f"{intent.owner}|{intent.target.field}|{source}|{factor}".encode()
    ).hexdigest()[:12]
    return f"cbg_{owner}_{field}_{digest}"


def apply_inline_matches(
    lines: list[str], intent: Intent, aliases: dict[str, tuple[str, str]]
) -> list[dict[str, Any]]:
    pattern = re.compile(
        rf"(?<![A-Za-z0-9_])(?P<field>{re.escape(intent.target.field)})"
        r"[ \t]*=[ \t]*(?P<value>-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)|[A-Za-z_][A-Za-z0-9_.:-]*)"
    )
    outcomes: list[dict[str, Any]] = []
    for index, raw in enumerate(lines):
        if ASSIGNMENT.match(raw.rstrip("\r\n")) or BLOCK_ASSIGNMENT.match(raw.rstrip("\r\n")):
            continue
        code, separator, comment = raw.partition("#")
        matches = list(pattern.finditer(code))
        if not matches:
            continue
        if intent.operation in TERMINAL_OPERATIONS:
            raise ValueError(
                f"Inline {intent.target.field} does not support {intent.operation}"
            )
        for match in reversed(matches):
            before = match.group("value")
            if before in intent.exclude_values:
                continue
            if intent.operation == "multiply" and not re.fullmatch(
                r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", before
            ):
                after = alias_name(intent, before, intent.value)
                aliases[after] = (before, render_number(decimal(intent.value, "multiplier")))
            else:
                after = numeric_result(intent.operation, before, intent.value)
            replacement = f"{intent.target.field} = {after}"
            code = code[: match.start()] + replacement + code[match.end() :]
            outcomes.append({
                "before": before,
                "after": after,
                "line_action": "inline_transformed",
            })
        lines[index] = code + (separator + comment if separator else "")
    return outcomes


def numeric_result(operation: str, current: str, raw_value: Any) -> str:
    if operation == "replace":
        return render_scalar(raw_value, "replacement value")
    base = decimal(current, "Vanilla/current value")
    if operation == "multiply":
        return render_number(base * decimal(raw_value, "multiplier"))
    if operation == "add":
        return render_number(base + decimal(raw_value, "delta"))
    if operation == "clamp":
        if not isinstance(raw_value, dict):
            raise ValueError("clamp value must contain min and/or max")
        minimum = decimal(raw_value["min"], "clamp minimum") if "min" in raw_value else None
        maximum = decimal(raw_value["max"], "clamp maximum") if "max" in raw_value else None
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("clamp minimum cannot exceed maximum")
        if minimum is not None:
            base = max(base, minimum)
        if maximum is not None:
            base = min(base, maximum)
        return render_number(base)
    raise ValueError(f"{operation} is not a numeric operation")


def apply_one_match(
    lines: list[str], intent: Intent, index: int, aliases: dict[str, tuple[str, str]]
) -> dict[str, Any]:
    raw = lines[index]
    newline = "\n" if raw.endswith("\n") else ""
    match = ASSIGNMENT.match(raw.rstrip("\r\n"))
    block = BLOCK_ASSIGNMENT.match(raw.rstrip("\r\n"))
    if block:
        if intent.operation != "multiply":
            raise ValueError(
                f"Block-valued {intent.target.field} supports multiply only"
            )
        factor = render_number(decimal(intent.value, "block multiplier"))
        end = matching_brace_line(lines, index)
        child_indent = re.match(r"^[ \t]*", lines[end]).group(0) + "\t"
        lines.insert(end, f"{child_indent}multiply = {factor} # CBG: {intent.owner}\n")
        return {
            "before": "<value block>",
            "after": f"<value block> * {factor}",
            "line_action": "block_multiplier_inserted",
        }
    assert match
    before = match.group("value").strip()
    if intent.operation == "remove":
        lines.pop(index)
        return {"before": before, "after": None, "line_action": "removed"}
    if intent.operation == "comment_out":
        lines[index] = f"{match.group('indent')}# {raw.lstrip().rstrip()} # CBG: commented by {intent.owner}{newline}"
        return {"before": before, "after": None, "line_action": "commented"}
    if intent.operation == "multiply" and SAFE_SCALAR.fullmatch(before):
        try:
            decimal(before, "current value")
        except ValueError:
            after = alias_name(intent, before, intent.value)
            aliases[after] = (before, render_number(decimal(intent.value, "multiplier")))
        else:
            after = numeric_result(intent.operation, before, intent.value)
    else:
        after = numeric_result(intent.operation, before, intent.value)
    existing = match.group("comment")
    suffix = f"; {existing.lstrip('# ').strip()}" if existing else ""
    lines[index] = (
        f"{match.group('indent')}{intent.target.field} = {after} "
        f"# VANILLA/PRIOR = {before}; CBG {intent.owner}: {intent.operation} {intent.value}{suffix}{newline}"
    )
    return {"before": before, "after": after, "line_action": "transformed"}


def apply_intent(
    lines: list[str], intent: Intent, aliases: dict[str, tuple[str, str]]
) -> list[dict[str, Any]]:
    wildcard = intent.target.object_path == ("**",)
    if wildcard:
        obj = None
    elif not intent.target.object_path:
        obj = LocatedObject((), -1, len(lines), "")
    else:
        object_matches = [
            item for item in scan_objects(lines) if item.path == intent.target.object_path
        ]
        if not object_matches and intent.on_missing == "skip":
            return []
        if len(object_matches) != 1:
            raise ValueError(
                f"Object {'/'.join(intent.target.object_path)!r} matched "
                f"{len(object_matches)} blocks; expected exactly one"
            )
        obj = object_matches[0]
    matches = all_field_matches(lines, intent.target.field) if wildcard else field_matches(lines, obj, intent.target.field)
    condition_objects = (
        scan_objects(lines)
        if matches and (intent.where or intent.exclude_objects)
        else []
    )
    matched_before_exclusions = bool(matches)
    matches = [
        index
        for index in matches
        if not (
            (match := ASSIGNMENT.match(lines[index].rstrip("\r\n")))
            and match.group("value").strip() in intent.exclude_values
        )
        and index_matches_where(lines, index, intent.where, condition_objects)
        and not index_inside_excluded_object(index, intent.exclude_objects, condition_objects)
    ]
    if intent.operation == "upsert_block":
        if not isinstance(intent.value, dict) or not intent.value:
            raise ValueError("upsert_block value must be a non-empty scalar map")
        rendered_children = [
            (field, render_scalar(value, f"upsert_block {field} value"))
            for field, value in intent.value.items()
            if isinstance(field, str) and SAFE_SCALAR.fullmatch(field)
        ]
        if len(rendered_children) != len(intent.value):
            raise ValueError("upsert_block field names must be safe scalar tokens")
        if len(matches) > 1:
            raise ValueError(f"upsert_block field {intent.target.field!r} matched multiple blocks")
        indent = obj.indent + ("\t" if obj.path else "")
        replacement = [
            f"{indent}{intent.target.field} = {{ # CBG: upserted by {intent.owner}\n",
            *(f"{indent}\t{field} = {value}\n" for field, value in rendered_children),
            f"{indent}}}\n",
        ]
        if matches:
            index = matches[0]
            if not BLOCK_ASSIGNMENT.match(lines[index].rstrip("\r\n")):
                raise ValueError("upsert_block cannot replace a scalar assignment")
            end = matching_brace_line(lines, index)
            lines[index : end + 1] = replacement
            return [{"before": "<value block>", "after": intent.value, "line_action": "block_replaced"}]
        insertion = obj.end
        if intent.position_after:
            anchors = field_matches(lines, obj, intent.position_after)
            if len(anchors) != 1:
                raise ValueError(f"Insertion anchor {intent.position_after!r} must match exactly once")
            insertion = matching_brace_line(lines, anchors[0]) + 1
        lines[insertion:insertion] = replacement
        return [{"before": None, "after": intent.value, "line_action": "block_inserted"}]
    inline_outcomes = (
        apply_inline_matches(lines, intent, aliases)
        if wildcard and intent.occurrences == "all"
        else []
    )
    adding = intent.operation in {"add_field", "add_custom"}
    if adding:
        if matches:
            raise ValueError(f"{intent.operation} requires an absent field at {intent.target}")
        insertion = obj.end
        if intent.position_after:
            anchors = field_matches(lines, obj, intent.position_after)
            if len(anchors) != 1:
                raise ValueError(f"Insertion anchor {intent.position_after!r} must match exactly once")
            insertion = anchors[0] + 1
        indent = obj.indent + ("\t" if obj.path else "")
        rendered = render_scalar(intent.value, f"{intent.operation} value")
        lines.insert(insertion, f"{indent}{intent.target.field} = {rendered} # CBG: added by {intent.owner}\n")
        return [{"before": None, "after": rendered, "line_action": "inserted"}]
    if intent.occurrences == "one" and len(matches) != 1:
        raise ValueError(f"Field {intent.target.field!r} at {intent.target} matched {len(matches)} lines")
    if intent.occurrences == "all" and not matches and not inline_outcomes and intent.on_missing == "skip":
        return []
    if intent.occurrences == "all" and not matches and not inline_outcomes and matched_before_exclusions:
        return []
    if intent.occurrences == "all" and not matches and not inline_outcomes:
        raise ValueError(f"Bulk field {intent.target.field!r} at {intent.target.file} matched no lines")
    outcomes = [apply_one_match(lines, intent, index, aliases) for index in reversed(matches)]
    outcomes.extend(inline_outcomes)
    return outcomes


def render_aliases(aliases: dict[str, tuple[str, str]]) -> bytes:
    lines = ["# Generated by Community Balance Generator.\n"]
    for name, (source, factor) in sorted(aliases.items()):
        lines.extend([
            f"{name} = {{\n",
            f"\tvalue = {source}\n",
            f"\tmultiply = {factor}\n",
            "}\n\n",
        ])
    return "".join(lines).encode("utf-8")


def previous_outputs(manifest_path: Path | None) -> dict[PurePosixPath, str]:
    if manifest_path is None or not manifest_path.is_file():
        return {}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("generator") != "community_balance_generator":
        raise ValueError(f"Refusing foreign manifest ownership: {manifest_path}")
    return {
        PurePosixPath(entry["path"]): entry["generated_sha256"]
        for entry in payload.get("files", [])
    }


def assert_owned_output(path: Path, relative: PurePosixPath, owned: dict[PurePosixPath, str]) -> None:
    if not path.exists():
        return
    expected = owned.get(relative)
    if expected is None:
        raise ValueError(f"Refusing to overwrite an output not owned by the previous CBG manifest: {relative}")
    actual = sha256(path.read_bytes())
    if actual != expected:
        raise ValueError(f"Refusing to overwrite a locally modified CBG output: {relative}")


def generate(
    game_root: Path,
    output_root: Path,
    intents: list[Intent],
    previous_manifest: Path | None = None,
) -> dict[str, Any]:
    validate_conflicts(intents)
    owned = previous_outputs(previous_manifest)
    by_file: dict[PurePosixPath, list[Intent]] = {}
    for intent in intents:
        by_file.setdefault(intent.target.file, []).append(intent)
    manifest_files: list[dict[str, Any]] = []
    aliases: dict[str, tuple[str, str]] = {}
    for relative, file_intents in sorted(by_file.items(), key=lambda item: item[0].as_posix()):
        source = game_root / Path(relative)
        source_bytes = source.read_bytes()
        has_bom = source_bytes.startswith(b"\xef\xbb\xbf")
        lines = source_bytes.decode("utf-8-sig").splitlines(keepends=True)
        audit: list[dict[str, Any]] = []
        for intent in sorted(file_intents, key=lambda item: item.sequence):
            outcomes = apply_intent(lines, intent, aliases)
            for outcome in reversed(outcomes):
                audit.append({
                    "owner": intent.owner,
                    "object": "/".join(intent.target.object_path),
                    "field": intent.target.field,
                    "operation": intent.operation,
                    "configured_value": intent.value,
                    "conflict": intent.conflict,
                    **outcome,
                })
        if not audit:
            continue
        rendered = "".join(line.rstrip(" \t\r\n") + ("\n" if line.endswith(("\n", "\r")) else "") for line in lines)
        generated = rendered.encode("utf-8")
        if has_bom:
            generated = b"\xef\xbb\xbf" + generated
        destination = output_root / Path(relative)
        assert_owned_output(destination, relative, owned)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(generated)
        manifest_files.append({
            "path": relative.as_posix(),
            "vanilla_sha256": sha256(source_bytes),
            "generated_sha256": sha256(generated),
            "transformations": audit,
        })
    if aliases:
        alias_relative = PurePosixPath(
            "main_menu/common/script_values/cbg_generated_scalars.txt"
        )
        alias_bytes = render_aliases(aliases)
        alias_destination = output_root / Path(alias_relative)
        assert_owned_output(alias_destination, alias_relative, owned)
        alias_destination.parent.mkdir(parents=True, exist_ok=True)
        alias_destination.write_bytes(alias_bytes)
        manifest_files.append({
            "path": alias_relative.as_posix(),
            "vanilla_sha256": None,
            "generated_sha256": sha256(alias_bytes),
            "transformations": [{"generated_alias_count": len(aliases)}],
        })
    current = {PurePosixPath(entry["path"]) for entry in manifest_files}
    for stale in sorted(set(owned) - current, key=lambda item: item.as_posix()):
        stale_path = output_root / Path(stale)
        if not stale_path.is_file():
            continue
        assert_owned_output(stale_path, stale, owned)
        stale_path.unlink()
    return {"schema_version": 1, "generator": "community_balance_generator", "files": manifest_files}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, action="append", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    game_root = args.game_root.resolve()
    output_root = args.output_root.resolve()
    try:
        intents, _custom_fields = load_intents(args.spec, game_root)
        manifest_path = args.manifest or output_root / "cbg_manifest.json"
        manifest = generate(game_root, output_root, intents, manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"Community Balance Generator failed: {exc}") from exc
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    applied = sum(
        len(entry.get("transformations", []))
        for entry in manifest["files"]
        if entry["path"] != "main_menu/common/script_values/cbg_generated_scalars.txt"
    )
    print(
        f"Generated {len(manifest['files'])} exact-path files; "
        f"expanded {len(intents)} file-rule candidates and applied {applied} mutations."
    )
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

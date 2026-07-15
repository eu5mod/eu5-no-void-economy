#!/usr/bin/env python3
"""Generate political reward balance overrides from the installed vanilla game.

Exclusively political script values are scaled once. Exact-path overrides are
generated for literal/dynamic assignments and political uses of constants that
are shared with an out-of-scope system such as Honor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

EVENT_EFFECTS = {
    "add_stability",
    "add_legitimacy",
    "add_republican_tradition",
    "add_devotion",
    "add_horde_unity",
    "add_tribal_cohesion",
    "add_government_power",
}
RESEARCH_MODIFIERS = {
    "stability_investment",
    "monthly_legitimacy",
    "monthly_republican_tradition",
    "monthly_devotion",
    "monthly_horde_unity",
    "monthly_tribal_cohesion",
}
PROFIT_MARGIN_FIELDS = {
    "rural_profit_margin",
    "guild_profit_margin",
    "workshop_profit_margin",
    "manufactory_profit_margin",
    "mills_profit_margin",
}
PROFIT_MARGIN_FACTOR = Decimal("1.10")
SIMPLE_ASSIGNMENT = re.compile(
    r"^(?P<indent>[ \t]*)(?P<field>[A-Za-z0-9_]+)[ \t]*=[ \t]*(?P<value>[^#{\s][^#\r\n]*?)[ \t]*(?P<comment>#.*)?$"
)
BLOCK_ASSIGNMENT = re.compile(
    r"^(?P<indent>[ \t]*)(?P<field>[A-Za-z0-9_]+)[ \t]*=[ \t]*\{(?P<comment>[ \t]*#.*)?$"
)
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass
class TransformResult:
    text: str
    count: int
    aliases: dict[str, tuple[str, str]]


def scaled_number(value: str, factor: Decimal) -> str:
    result = Decimal(value) * factor
    rendered = format(result.normalize(), "f")
    return "0" if rendered in {"-0", ""} else rendered


def transformed_comment(vanilla_value: str, existing: str | None = None) -> str:
    trace = f"# VANILLA = {vanilla_value}"
    if not existing:
        return trace
    return f"{trace}; {existing.lstrip('# ').strip()}"


def alias_name(surface: str, field: str, value: str, factor: Decimal) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")[:72]
    digest = hashlib.sha256(f"{surface}|{field}|{value}|{factor}".encode()).hexdigest()[:10]
    return f"cbp_{surface}_{field}_{slug}_{digest}"


def matching_brace_line(lines: list[str], start: int) -> int:
    depth = 0
    in_quote = False
    for index in range(start, len(lines)):
        line = lines[index]
        escaped = False
        for char in line:
            if char == '"' and not escaped:
                in_quote = not in_quote
            if not in_quote:
                if char == "#":
                    break
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return index
            escaped = char == "\\" and not escaped
    raise ValueError(f"Unclosed block starting on line {start + 1}")


def enclosing_named_blocks(lines: list[str]) -> list[set[str]]:
    active: list[tuple[str, int]] = []
    result: list[set[str]] = []
    depth = 0
    for line in lines:
        result.append({name for name, _depth in active})
        code = line.split("#", 1)[0]
        match = re.match(r"^[ \t]*(?P<name>[A-Za-z0-9_]+)[ \t]*=[ \t]*\{", code)
        opens = code.count("{")
        closes = code.count("}")
        if match:
            active.append((match.group("name"), depth))
        depth += opens - closes
        while active and depth <= active[-1][1]:
            active.pop()
    return result


def transform_assignments(
    text: str,
    fields: set[str],
    factor: Decimal,
    surface: str,
    required_ancestors: set[str] | None = None,
    centralized_tokens: set[str] | None = None,
) -> TransformResult:
    lines = text.splitlines(keepends=True)
    ancestors = enclosing_named_blocks(lines)
    aliases: dict[str, tuple[str, str]] = {}
    count = 0
    index = 0
    while index < len(lines):
        raw = lines[index]
        line = raw.rstrip("\r\n")
        newline = raw[len(line) :]
        simple = SIMPLE_ASSIGNMENT.match(line)
        block = BLOCK_ASSIGNMENT.match(line)
        field = simple.group("field") if simple else block.group("field") if block else ""
        allowed = field in fields and (
            required_ancestors is None or bool(ancestors[index] & required_ancestors)
        )
        if not allowed:
            index += 1
            continue

        if simple:
            value = simple.group("value").strip()
            if centralized_tokens and value in centralized_tokens:
                index += 1
                continue
            comment = " " + transformed_comment(value, simple.group("comment"))
            if NUMBER.fullmatch(value):
                replacement = scaled_number(value, factor)
            else:
                replacement = alias_name(surface, field, value, factor)
                aliases[replacement] = (value, str(factor))
            lines[index] = f"{simple.group('indent')}{field} = {replacement}{comment}{newline}"
            count += 1
            index += 1
            continue

        end = matching_brace_line(lines, index)
        closing = lines[end]
        closing_indent = re.match(r"^[ \t]*", closing).group(0)
        child_indent = closing_indent + "\t"
        lines.insert(end, f"{child_indent}multiply = {factor}\n")
        ancestors.insert(end, set(ancestors[index]))
        count += 1
        index = end + 2

    return TransformResult("".join(lines), count, aliases)


def transform_inline_assignments(
    text: str,
    fields: set[str],
    factor: Decimal,
    surface: str,
    centralized_tokens: set[str] | None = None,
) -> TransformResult:
    field_pattern = "|".join(re.escape(field) for field in sorted(fields))
    pattern = re.compile(
        rf"(?P<field>{field_pattern})(?P<spacing>[ \t]*=[ \t]*)"
        rf"(?P<value>-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*)"
    )
    aliases: dict[str, tuple[str, str]] = {}
    count = 0
    output: list[str] = []
    for raw in text.splitlines(keepends=True):
        code, separator, comment = raw.partition("#")

        def replace(match: re.Match[str]) -> str:
            nonlocal count
            if not code[: match.start()].strip():
                return match.group(0)
            value = match.group("value")
            if centralized_tokens and value in centralized_tokens:
                return match.group(0)
            if NUMBER.fullmatch(value):
                replacement = scaled_number(value, factor)
            else:
                replacement = alias_name(surface, match.group("field"), value, factor)
                aliases[replacement] = (value, str(factor))
            count += 1
            return f"{match.group('field')}{match.group('spacing')}{replacement}"

        transformed = pattern.sub(replace, code)
        output.append(transformed + (separator + comment if separator else ""))
    return TransformResult("".join(output), count, aliases)


def compose_simple_assignments(
    source_text: str,
    current_text: str,
    fields: set[str],
    factor: Decimal,
    surface: str,
    label: str = "<unknown>",
    centralized_tokens: set[str] | None = None,
) -> TransformResult:
    """Apply source-derived simple values to an existing exact-path override."""
    def records(text: str) -> list[tuple[int, tuple[tuple[str, ...], str, int], re.Match[str]]]:
        lines = text.splitlines(keepends=True)
        active: list[tuple[str, int]] = []
        depth = 0
        ordinals: dict[tuple[tuple[str, ...], str], int] = {}
        found: list[tuple[int, tuple[tuple[str, ...], str, int], re.Match[str]]] = []
        for index, raw in enumerate(lines):
            body = raw.rstrip("\r\n")
            assignment = SIMPLE_ASSIGNMENT.match(body)
            if assignment and assignment.group("field") in fields:
                base = (tuple(name for name, _depth in active), assignment.group("field"))
                ordinal = ordinals.get(base, 0)
                ordinals[base] = ordinal + 1
                found.append((index, (base[0], base[1], ordinal), assignment))
            code = body.split("#", 1)[0]
            block_match = re.match(r"^[ \t]*(?P<name>[A-Za-z0-9_.:-]+)[ \t]*=[ \t]*\{", code)
            opens = code.count("{")
            closes = code.count("}")
            if block_match:
                active.append((block_match.group("name"), depth))
            depth += opens - closes
            while active and depth <= active[-1][1]:
                active.pop()
        return found

    expected: dict[tuple[tuple[str, ...], str, int], tuple[str, str, str]] = {}
    aliases: dict[str, tuple[str, str]] = {}
    for _index, key, match in records(source_text):
        field = match.group("field")
        value = match.group("value").strip()
        if centralized_tokens and value in centralized_tokens:
            continue
        if NUMBER.fullmatch(value):
            replacement = scaled_number(value, factor)
        else:
            replacement = alias_name(surface, field, value, factor)
            aliases[replacement] = (value, str(factor))
        expected[key] = (field, replacement, value)

    if not expected:
        return TransformResult(current_text, 0, {})

    lines = current_text.splitlines(keepends=True)
    current = [item for item in records(current_text) if item[1] in expected]
    missing = [key for _index, key, _match in current if key not in expected]
    if missing:
        raise SystemExit(
            f"Cannot compose political rewards in {label}: {len(missing)} package "
            "modifier paths have no matching vanilla source object."
        )

    for index, key, match in current:
        field, replacement, vanilla_value = expected[key]
        raw = lines[index]
        body = raw.rstrip("\r\n")
        newline = raw[len(body) :]
        comment = " " + transformed_comment(vanilla_value, match.group("comment"))
        lines[index] = f"{match.group('indent')}{field} = {replacement}{comment}{newline}"
    return TransformResult("".join(lines), len(current), aliases)


def write_aliases(path: Path, aliases: dict[str, tuple[str, str]]) -> None:
    lines = ["# Generated by tools/generate_political_reward_overrides.py.\n"]
    for name, (source, factor) in sorted(aliases.items()):
        lines.extend([f"{name} = {{\n", f"\tvalue = {source}\n"])
        if factor == "preserve:0.5":
            lines.append("\tmultiply = 2\n")
        elif factor == "preserve:0.75":
            lines.extend(["\tmultiply = 4\n", "\tdivide = 3\n"])
        else:
            lines.append(f"\tmultiply = {factor}\n")
        lines.extend(["}\n\n"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def centralizable_script_values(game_root: Path) -> dict[str, Decimal]:
    target_policy: dict[str, Decimal] = {}
    scan_roots = [game_root / "in_game/events", game_root / "in_game/common"]
    for root in scan_roots:
        for path in root.rglob("*.txt"):
            if "debug" in path.parts:
                continue
            for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
                match = SIMPLE_ASSIGNMENT.match(line)
                if not match:
                    continue
                value = match.group("value").strip()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
                    continue
                field = match.group("field")
                if field in EVENT_EFFECTS:
                    factor = Decimal("0.5")
                elif field in RESEARCH_MODIFIERS:
                    factor = Decimal("0.75")
                else:
                    continue
                if value in target_policy and target_policy[value] != factor:
                    raise SystemExit(
                        f"Political script value {value} is used by conflicting policies "
                        f"{target_policy[value]} and {factor}."
                    )
                target_policy[value] = factor
    default_values = game_root / "main_menu/common/script_values/default_values.txt"
    numeric_definitions = {
        match.group("name")
        for line in default_values.read_text(encoding="utf-8-sig").splitlines()
        if (
            match := re.match(
                r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*-?\d+(?:\.\d+)?(?:\s*#.*)?$",
                line,
            )
        )
    }
    candidates = {name: factor for name, factor in target_policy.items() if name in numeric_definitions}
    shared_with_nonpolitical: set[str] = set()
    for root in [game_root / "in_game/events", game_root / "in_game/common", game_root / "main_menu/common"]:
        for path in root.rglob("*.txt"):
            lines = path.read_text(encoding="utf-8-sig", errors="ignore").splitlines(keepends=True)
            ancestors = enclosing_named_blocks(lines)
            for index, raw in enumerate(lines):
                match = SIMPLE_ASSIGNMENT.match(raw.rstrip("\r\n"))
                if not match or match.group("value").strip() not in candidates:
                    continue
                field = match.group("field")
                calculation_inside_target = field in {"value", "add", "subtract"} and bool(
                    ancestors[index] & (EVENT_EFFECTS | RESEARCH_MODIFIERS)
                )
                if field not in EVENT_EFFECTS | RESEARCH_MODIFIERS and not calculation_inside_target:
                    shared_with_nonpolitical.add(match.group("value").strip())
    return {
        name: factor
        for name, factor in candidates.items()
        if name not in shared_with_nonpolitical
    }


def preserve_nonpolitical_token_uses(text: str, centralized: dict[str, Decimal]) -> TransformResult:
    lines = text.splitlines(keepends=True)
    ancestors = enclosing_named_blocks(lines)
    aliases: dict[str, tuple[str, str]] = {}
    count = 0
    for index, raw in enumerate(lines):
        body = raw.rstrip("\r\n")
        newline = raw[len(body) :]
        match = SIMPLE_ASSIGNMENT.match(body)
        if not match:
            continue
        token = match.group("value").strip()
        if token not in centralized:
            continue
        field = match.group("field")
        calculation_inside_target = field in {"value", "add", "subtract"} and bool(
            ancestors[index] & (EVENT_EFFECTS | RESEARCH_MODIFIERS)
        )
        if field in EVENT_EFFECTS | RESEARCH_MODIFIERS or calculation_inside_target:
            continue
        factor = centralized[token]
        name = alias_name("preserve", field, token, factor)
        aliases[name] = (token, f"preserve:{factor}")
        comment = f" {match.group('comment')}" if match.group("comment") else ""
        lines[index] = f"{match.group('indent')}{field} = {name}{comment}{newline}"
        count += 1
    return TransformResult("".join(lines), count, aliases)


def write_central_script_value_override(game_root: Path, package_root: Path, policies: dict[str, Decimal]) -> Path:
    source = game_root / "main_menu/common/script_values/default_values.txt"
    output = package_root / "main_menu/common/script_values/default_values.txt"
    lines = source.read_text(encoding="utf-8-sig").splitlines()
    changed: set[str] = set()
    for index, line in enumerate(lines):
        match = re.match(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>-?\d+(?:\.\d+)?)(?P<comment>\s*#.*)?$", line)
        if not match or (
            match.group("name") not in policies
            and match.group("name") not in PROFIT_MARGIN_FIELDS
        ):
            continue
        name = match.group("name")
        vanilla_value = match.group("value")
        factor = policies.get(name, PROFIT_MARGIN_FACTOR)
        value = scaled_number(vanilla_value, factor)
        comment = transformed_comment(vanilla_value, match.group("comment"))
        lines[index] = f"{name} = {value} {comment}"
        changed.add(name)
    missing = (set(policies) | PROFIT_MARGIN_FIELDS) - changed
    if missing:
        raise SystemExit(f"Missing central CBP script-value definitions: {sorted(missing)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(normalize_generated_whitespace("\n".join(lines)), encoding="utf-8-sig")
    return output


def apply_package_compatibility_sanitizers(relative: Path, text: str) -> str:
    if relative.parts[:2] == ("common", "auto_modifiers"):
        text = re.sub(
            r"^[ \t]*building_upkeep_multiplier[ \t]*=.*(?:\r?\n|$)",
            "",
            text,
            flags=re.MULTILINE,
        )
    return text


def normalize_generated_whitespace(text: str) -> str:
    normalized: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip(" \t")
        while True:
            updated = re.sub(r"^(\t*) +\t", r"\1\t", line)
            if updated == line:
                break
            line = updated
        normalized.append(line)
    return "\n".join(normalized).rstrip() + "\n"


def update_composed_building_manifests(package_root: Path, relative: Path, output: Path) -> None:
    if relative.parts[:2] != ("common", "building_types"):
        return
    generated_hash = hashlib.sha256(
        output.read_text(encoding="utf-8-sig").encode("utf-8")
    ).hexdigest()
    us09_manifest = package_root / "cbp_generated/us09_buildings" / f"{relative.stem}.json"
    if us09_manifest.is_file():
        payload = json.loads(us09_manifest.read_text(encoding="utf-8"))
        payload["generated_sha256"] = generated_hash
        us09_manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    minting_manifest = package_root / "cbp_generated/us177_minting_building_manifest.json"
    if minting_manifest.is_file():
        payload = json.loads(minting_manifest.read_text(encoding="utf-8"))
        target = f"in_game/{relative.as_posix()}"
        changed = False
        for entry in payload.get("files", []):
            if entry.get("path") == target:
                entry["generated_sha256"] = generated_hash
                changed = True
        if changed:
            minting_manifest.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--clean", action="store_true", help="Remove only files created solely by this generator.")
    args = parser.parse_args()

    source_in_game = args.game_root / "in_game"
    output_in_game = args.package_root / "in_game"
    aliases: dict[str, tuple[str, str]] = {}
    generated: list[dict[str, object]] = []
    centralized = centralizable_script_values(args.game_root)

    manifest_path = args.package_root / "cbp_generated/political_reward_overrides_manifest.json"
    baseline_root = args.package_root / "cbp_generated/political_reward_baselines"
    if manifest_path.is_file():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in previous.get("files", []):
            stale = (
                args.package_root / entry["path"]
                if entry.get("package_relative")
                else output_in_game / entry["path"]
            )
            baseline = baseline_root / (entry.get("baseline") or entry["path"])
            if baseline.is_file():
                stale.parent.mkdir(parents=True, exist_ok=True)
                stale.write_bytes(baseline.read_bytes())
            elif entry.get("created", True) and stale.is_file() and not entry.get("package_relative"):
                stale.unlink()
        if args.clean:
            alias_path = args.package_root / "main_menu/common/script_values/cbp_political_reward_scalars_generated.txt"
            if alias_path.is_file():
                alias_path.unlink()
            central_path = args.package_root / "main_menu/common/script_values/default_values.txt"
            if central_path.is_file():
                central_path.unlink()
            if baseline_root.is_dir():
                shutil.rmtree(baseline_root)
            manifest_path.unlink()
            print("Cleaned files owned solely by the political reward generator.")
            return 0
    elif args.clean:
        print("No political reward manifest found; nothing to clean.")
        return 0
    for source in sorted((source_in_game / "events").rglob("*.txt")):
        if "debug" in source.relative_to(source_in_game / "events").parts:
            continue
        source_text = source.read_text(encoding="utf-8-sig")
        result = transform_assignments(
            source_text, EVENT_EFFECTS, Decimal("0.5"), "event",
            centralized_tokens=set(centralized),
        )
        inline = transform_inline_assignments(
            result.text, EVENT_EFFECTS, Decimal("0.5"), "event_inline", set(centralized)
        )
        result = TransformResult(
            inline.text,
            result.count + inline.count,
            result.aliases | inline.aliases,
        )
        preserved = preserve_nonpolitical_token_uses(result.text, centralized)
        if not result.count and not preserved.count:
            continue
        relative = source.relative_to(source_in_game)
        output = output_in_game / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(normalize_generated_whitespace(preserved.text), encoding="utf-8-sig")
        aliases.update(result.aliases)
        aliases.update(preserved.aliases)
        generated.append({
            "path": str(relative),
            "policy": "event_half",
            "changes": result.count + preserved.count,
            "political_changes": result.count,
            "preserved_nonpolitical_uses": preserved.count,
            "created": True,
        })

    common_root = source_in_game / "common"
    for source in sorted(common_root.rglob("*.txt")):
        source_text = source.read_text(encoding="utf-8-sig")
        relative = source.relative_to(source_in_game)
        output = output_in_game / relative
        created = not output.is_file()
        current_text = output.read_text(encoding="utf-8-sig") if output.is_file() else source_text
        baseline_relative = f"in_game/{relative.as_posix()}"
        if relative.parts[:2] == ("common", "building_types"):
            static_result = TransformResult(current_text, 0, {})
        else:
            static_result = compose_simple_assignments(
                source_text, current_text, RESEARCH_MODIFIERS, Decimal("0.75"), "static", str(relative), set(centralized)
            )
            static_inline = transform_inline_assignments(
                static_result.text, RESEARCH_MODIFIERS, Decimal("0.75"), "static_inline", set(centralized)
            )
            static_result = TransformResult(
                static_inline.text,
                static_result.count + static_inline.count,
                static_result.aliases | static_inline.aliases,
            )
        result_text = static_result.text
        outcome_count = 0
        outcome_aliases: dict[str, tuple[str, str]] = {}
        if relative.parts[:2] != ("common", "effect_localization"):
            if created:
                outcome = transform_assignments(
                    result_text, EVENT_EFFECTS, Decimal("0.5"), "instant",
                    centralized_tokens=set(centralized),
                )
            else:
                source_blocks = sum(
                    1
                    for line in source_text.splitlines()
                    if (match := BLOCK_ASSIGNMENT.match(line))
                    and match.group("field") in EVENT_EFFECTS
                )
                if source_blocks:
                    raise SystemExit(
                        f"Cannot compose block-valued instant political rewards into {relative}; "
                        "add an explicit delegated postprocessor."
                    )
                outcome = compose_simple_assignments(
                    source_text, result_text, EVENT_EFFECTS, Decimal("0.5"), "instant", str(relative), set(centralized)
                )
            result_text = outcome.text
            outcome_count = outcome.count
            outcome_aliases = outcome.aliases
            inline_outcome = transform_inline_assignments(
                result_text, EVENT_EFFECTS, Decimal("0.5"), "instant_inline", set(centralized)
            )
            result_text = inline_outcome.text
            outcome_count += inline_outcome.count
            outcome_aliases.update(inline_outcome.aliases)
        preserved = preserve_nonpolitical_token_uses(result_text, centralized)
        result_text = preserved.text
        if not static_result.count and not outcome_count and not preserved.count:
            continue
        if not created:
            baseline = baseline_root / baseline_relative
            baseline.parent.mkdir(parents=True, exist_ok=True)
            baseline.write_text(
                normalize_generated_whitespace(output.read_text(encoding="utf-8-sig")),
                encoding="utf-8-sig",
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        result_text = apply_package_compatibility_sanitizers(relative, result_text)
        if created:
            result_text = normalize_generated_whitespace(result_text)
        else:
            result_text = "\n".join(line.rstrip(" \t") for line in result_text.splitlines()) + "\n"
        output.write_text(result_text, encoding="utf-8-sig")
        update_composed_building_manifests(args.package_root, relative, output)
        aliases.update(static_result.aliases)
        aliases.update(outcome_aliases)
        aliases.update(preserved.aliases)
        generated.append(
            {
                "path": str(relative),
                "policy": "static_three_quarters" if static_result.count else "instant_half",
                "static_changes": static_result.count,
                "instant_changes": outcome_count,
                "preserved_nonpolitical_uses": preserved.count,
                "changes": static_result.count + outcome_count + preserved.count,
                "created": created,
                "baseline": baseline_relative if not created else None,
            }
        )

    main_menu_common = args.game_root / "main_menu/common"
    central_source = main_menu_common / "script_values/default_values.txt"
    for source in sorted(main_menu_common.rglob("*.txt")):
        if source == central_source:
            continue
        relative = source.relative_to(args.game_root)
        output = args.package_root / relative
        created = not output.is_file()
        input_path = source if created else output
        preserved = preserve_nonpolitical_token_uses(
            input_path.read_text(encoding="utf-8-sig"), centralized
        )
        if not preserved.count:
            continue
        baseline_relative = relative
        if not created:
            baseline = baseline_root / baseline_relative
            baseline.parent.mkdir(parents=True, exist_ok=True)
            baseline.write_text(
                normalize_generated_whitespace(output.read_text(encoding="utf-8-sig")),
                encoding="utf-8-sig",
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(normalize_generated_whitespace(preserved.text), encoding="utf-8-sig")
        aliases.update(preserved.aliases)
        generated.append({
            "path": str(relative),
            "policy": "preserve_nonpolitical_use",
            "changes": preserved.count,
            "created": created,
            "baseline": str(baseline_relative) if not created else None,
            "package_relative": True,
        })

    alias_path = args.package_root / "main_menu/common/script_values/cbp_political_reward_scalars_generated.txt"
    write_aliases(alias_path, aliases)
    write_central_script_value_override(args.game_root, args.package_root, centralized)
    manifest = {
        "generator": "tools/generate_political_reward_overrides.py",
        "policies": {"instant_effects": 0.5, "static_sources": 0.75},
        "profit_margin_factor": float(PROFIT_MARGIN_FACTOR),
        "files": generated,
        "aliases": len(aliases),
        "central_script_values": {name: float(factor) for name, factor in sorted(centralized.items())},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Generated {len(generated)} political reward override files and {len(aliases)} scaled script values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

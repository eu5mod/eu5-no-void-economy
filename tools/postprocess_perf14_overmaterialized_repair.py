#!/usr/bin/env python3
"""Postprocess generated stock-good adapters.

The historical PERF-14 repair remains disabled. This postprocessor now owns one
narrow US-00 safety rule: a previous overproduction penalty may be applied only
when the aggregate stock for that good has saturated the aggregate storage
capacity of all countries present in the market.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

EFFECT_RE = re.compile(
    r"(?m)^(cbp_apply_us00_previous_penalty_good_(?P<good>[a-z0-9_]+)) = \{\n"
)
OLD_LIMIT = "\tif = {\n\t\tlimit = { scope:cbp_us00_previous_production_penalty < 0 }"
MARKER = "cbp_us00_market_stock_saturated"


def find_matching_brace(source: str, open_index: int) -> int:
    depth = 0
    in_string = False
    index = open_index
    while index < len(source):
        char = source[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "#":
            newline = source.find("\n", index)
            if newline < 0:
                return len(source)
            index = newline
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    raise ValueError("unterminated scripted-effect block")


def saturation_guard(good: str) -> str:
    market_map = f"cbp_{good}_market_stock"
    return f'''\tsave_temporary_scope_value_as = {{ name = cbp_us00_market_stock_for_penalty value = 0 }}
\tif = {{
\t\tlimit = {{
\t\t\thas_global_variable_map = {market_map}
\t\t\tis_key_in_global_variable_map = {{ name = {market_map} target = scope:cbp_market }}
\t\t}}
\t\tsave_temporary_scope_value_as = {{
\t\t\tname = cbp_us00_market_stock_for_penalty
\t\t\tvalue = "global_variable_map({market_map}|scope:cbp_market)"
\t\t}}
\t}}

\tscope:cbp_country = {{
\t\tset_local_variable = {{ name = cbp_us00_market_capacity_accumulator value = 0 }}
\t}}
\tif = {{
\t\tlimit = {{ has_global_variable_list = cbp_countries_present_in_market }}
\t\tevery_in_global_list = {{
\t\t\tvariable = cbp_countries_present_in_market
\t\t\tif = {{
\t\t\t\tlimit = {{
\t\t\t\t\thas_variable_map = cbp_stock_cap_by_market
\t\t\t\t\tis_key_in_variable_map = {{ name = cbp_stock_cap_by_market target = scope:cbp_market }}
\t\t\t\t}}
\t\t\t\tsave_temporary_scope_value_as = {{
\t\t\t\t\tname = cbp_us00_country_market_capacity_for_penalty
\t\t\t\t\tvalue = "variable_map(cbp_stock_cap_by_market|scope:cbp_market)"
\t\t\t\t}}
\t\t\t\tscope:cbp_country = {{
\t\t\t\t\tchange_local_variable = {{
\t\t\t\t\t\tname = cbp_us00_market_capacity_accumulator
\t\t\t\t\t\tadd = scope:cbp_us00_country_market_capacity_for_penalty
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t}}
\tscope:cbp_country = {{
\t\tsave_temporary_scope_value_as = {{
\t\t\tname = cbp_us00_market_capacity_for_penalty
\t\t\tvalue = local_var:cbp_us00_market_capacity_accumulator
\t\t}}
\t}}
\tsave_temporary_scope_value_as = {{ name = {MARKER} value = 0 }}
\tif = {{
\t\tlimit = {{
\t\t\tscope:cbp_us00_market_capacity_for_penalty > 0
\t\t\tscope:cbp_us00_market_stock_for_penalty >= scope:cbp_us00_market_capacity_for_penalty
\t\t}}
\t\tsave_temporary_scope_value_as = {{ name = {MARKER} value = 1 }}
\t}}

\tif = {{
\t\tlimit = {{
\t\t\tscope:cbp_us00_previous_production_penalty < 0
\t\t\tscope:{MARKER} = 1
\t\t}}'''


def rewrite_penalty_effects(text: str) -> tuple[str, int]:
    pieces: list[str] = []
    position = 0
    rewritten = 0

    for match in EFFECT_RE.finditer(text):
        open_index = text.find("{", match.start(), match.end())
        end = find_matching_brace(text, open_index)
        block = text[match.start():end]
        if MARKER in block:
            continue
        if OLD_LIMIT not in block:
            raise SystemExit(f"expected production-penalty limit not found for {match.group('good')}")
        updated_block = block.replace(OLD_LIMIT, saturation_guard(match.group("good")), 1)
        pieces.append(text[position:match.start()])
        pieces.append(updated_block)
        position = end
        rewritten += 1

    pieces.append(text[position:])
    return "".join(pieces), rewritten


def validate(text: str) -> int:
    effects = list(EFFECT_RE.finditer(text))
    if not effects:
        raise SystemExit("no generated US-00 production-penalty effects found")
    missing = []
    for match in effects:
        open_index = text.find("{", match.start(), match.end())
        end = find_matching_brace(text, open_index)
        block = text[match.start():end]
        if MARKER not in block or "scope:cbp_us00_market_stock_for_penalty >= scope:cbp_us00_market_capacity_for_penalty" not in block:
            missing.append(match.group("good"))
    if missing:
        raise SystemExit("market-saturation guard missing for: " + ", ".join(missing[:20]))
    return len(effects)


def main() -> int:
    if len(sys.argv) not in {2, 3, 4}:
        print(
            "usage: postprocess_perf14_overmaterialized_repair.py <cbp_stock_goods_generated.txt> [legacy_perf14_guarded_test_effects.txt] [legacy_perf14_test_effects.txt]",
            file=sys.stderr,
        )
        return 2

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    updated, rewritten = rewrite_penalty_effects(text)
    effect_count = validate(updated)
    path.write_text(updated, encoding="utf-8")
    print(f"US-00 market-saturation penalty guards: {effect_count} effects validated, {rewritten} rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

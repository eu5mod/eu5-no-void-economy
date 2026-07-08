#!/usr/bin/env python3
"""Patch generated stock-good helpers that are too risky to hand-maintain.

This postprocessor intentionally patches only the generated stock-good adapter.
Older invocations may still pass PERF-14 test files as compatibility arguments;
those paths are accepted but not modified, so `tools/generate_all.sh` does not
 dirty hand-authored test files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PROMOTION_FN_RE = re.compile(
    r"(?m)^modeu5_promote_market_to_detailed_accounting_good_(?P<good>[a-z0-9_]+)\s*=\s*\{"
)

US10_CANDIDATE_SCAN_FN_RE = re.compile(
    r"(?m)^modeu5_scan_us10_candidate_country_good_(?P<good>[a-z0-9_]+)\s*=\s*\{"
)

OLD_OVERMATERIALIZED_BRANCH = """\tif = {
\t\tlimit = { scope:modeu5_promotion_overmaterialized_quantity > modeu5_initialization_rounding_epsilon }
\t\tset_global_variable = { name = modeu5_perf14_promotion_failure_detected value = 1 }
\t\tset_global_variable = {
\t\t\tname = modeu5_perf14_promotion_overmaterialized_failures
\t\t\tvalue = {
\t\t\t\tvalue = global_var:modeu5_perf14_promotion_overmaterialized_failures
\t\t\t\tadd = 1
\t\t\t}
\t\t}
\t}
"""


def find_matching_brace(source: str, open_index: int) -> int:
    if open_index >= len(source) or source[open_index] != "{":
        raise ValueError("find_matching_brace called without an opening brace")

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
            index += 1
            continue
        if char == '"':
            in_string = True
        elif char == "#":
            newline = source.find("\n", index)
            if newline < 0:
                return len(source)
            index = newline
            continue
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                raise ValueError("brace depth became negative")
        index += 1
    raise ValueError("unterminated brace block")


def assert_balanced_braces(source: str, *, label: str) -> None:
    depth = 0
    stack: list[int] = []
    in_string = False
    index = 0
    while index < len(source):
        char = source[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
        elif char == "#":
            newline = source.find("\n", index)
            if newline < 0:
                break
            index = newline
            continue
        elif char == "{":
            depth += 1
            stack.append(source.count("\n", 0, index) + 1)
        elif char == "}":
            depth -= 1
            if depth < 0:
                line_no = source.count("\n", 0, index) + 1
                raise SystemExit(f"{label}: generated script has an extra closing brace at line {line_no}")
            stack.pop()
        index += 1

    if depth != 0:
        first_unclosed = stack[-1] if stack else "unknown"
        raise SystemExit(f"{label}: generated script has an unclosed brace block starting at line {first_unclosed}")


def render_repair_branch(good: str) -> str:
    stock_map = f"modeu5_{good}_stock_by_market"
    return f"""\tif = {{
\t\tlimit = {{
\t\t\tscope:modeu5_promotion_country_sum_before > modeu5_initialization_rounding_epsilon
\t\t\tOR = {{
\t\t\t\tscope:modeu5_promotion_overmaterialized_quantity > modeu5_initialization_rounding_epsilon
\t\t\t\tscope:modeu5_promotion_quantity_to_materialize > modeu5_initialization_rounding_epsilon
\t\t\t}}
\t\t}}
\t\t# Pragmatic migration repair: market aggregate is the cap/source of truth;
\t\t# rebuild any non-zero country ledger from that aggregate when they differ.
\t\t# The historical counter name is kept so existing PERF-14 probes can observe it.
\t\tset_global_variable = {{
\t\t\tname = modeu5_perf14_promotion_overmaterialized_failures
\t\t\tvalue = {{
\t\t\t\tvalue = global_var:modeu5_perf14_promotion_overmaterialized_failures
\t\t\t\tadd = 1
\t\t\t}}
\t\t}}
\t\tdebug_log = "ModeU5 PERF-14 PROMOTION_REPAIR blocked=1 reason=country_sum_differs_from_market_aggregate source=market_aggregate action=rebuild_country_stocks_from_market_aggregate"

\t\tif = {{
\t\t\tlimit = {{ has_global_variable_list = modeu5_countries_present_in_market }}
\t\t\tevery_in_global_list = {{
\t\t\t\tvariable = modeu5_countries_present_in_market
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\thas_variable_map = {stock_map}
\t\t\t\t\t\tis_key_in_variable_map = {{
\t\t\t\t\t\t\tname = {stock_map}
\t\t\t\t\t\t\ttarget = scope:modeu5_promotion_market
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t\tsave_temporary_scope_value_as = {{
\t\t\t\t\t\tname = modeu5_perf14_repair_country_stock_before
\t\t\t\t\t\tvalue = "variable_map({stock_map}|scope:modeu5_promotion_market)"
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\telse = {{
\t\t\t\t\tsave_temporary_scope_value_as = {{ name = modeu5_perf14_repair_country_stock_before value = 0 }}
\t\t\t\t}}
\t\t\tsave_temporary_scope_value_as = {{
\t\t\t\tname = modeu5_perf14_repair_country_stock_after
\t\t\t\tvalue = {{
\t\t\t\t\tvalue = scope:modeu5_perf14_repair_country_stock_before
\t\t\t\t\tmultiply = scope:modeu5_promotion_market_aggregate_before
\t\t\t\t\tdivide = scope:modeu5_promotion_country_sum_before
\t\t\t\t\tmin = 0
\t\t\t\t}}
\t\t\t}}
\t\t\tif = {{
\t\t\t\tlimit = {{
\t\t\t\t\thas_variable_map = {stock_map}
\t\t\t\t\tis_key_in_variable_map = {{
\t\t\t\t\t\tname = {stock_map}
\t\t\t\t\t\ttarget = scope:modeu5_promotion_market
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\tremove_from_variable_map = {{ name = {stock_map} key = scope:modeu5_promotion_market }}
\t\t\t}}
\t\t\tif = {{
\t\t\t\tlimit = {{ scope:modeu5_perf14_repair_country_stock_after > modeu5_initialization_rounding_epsilon }}
\t\t\t\tadd_to_variable_map = {{
\t\t\t\t\tname = {stock_map}
\t\t\t\t\tkey = scope:modeu5_promotion_market
\t\t\t\t\tvalue = scope:modeu5_perf14_repair_country_stock_after
\t\t\t\t}}
\t\t\t}}
\t\t}}

\t\tscope:modeu5_promotion_market = {{
\t\t\tsave_temporary_scope_as = modeu5_market
\t\t\tsave_temporary_scope_as = modeu5_market_country_cache_market
\t\t\tsave_temporary_scope_as = modeu5_active_market
\t\t}}
\t\tmodeu5_mark_active_market_good_{good} = yes
\t\tsave_temporary_scope_as = modeu5_consistency_controller
\t\tmodeu5_rebuild_countries_present_in_market = yes
\t\tmodeu5_scan_stock_sources_from_prepared_market_country_cache_good_{good} = yes

\t\tsave_temporary_scope_value_as = {{ name = modeu5_perf14_repair_country_under value = {{ value = scope:modeu5_promotion_market_aggregate_before subtract = scope:modeu5_expected_market_stock min = 0 }} }}
\t\tsave_temporary_scope_value_as = {{ name = modeu5_perf14_repair_country_over value = {{ value = scope:modeu5_expected_market_stock subtract = scope:modeu5_promotion_market_aggregate_before min = 0 }} }}
\t\tsave_temporary_scope_value_as = {{ name = modeu5_perf14_repair_market_under value = {{ value = scope:modeu5_promotion_market_aggregate_before subtract = scope:modeu5_scanned_market_stock min = 0 }} }}
\t\tsave_temporary_scope_value_as = {{ name = modeu5_perf14_repair_market_over value = {{ value = scope:modeu5_scanned_market_stock subtract = scope:modeu5_promotion_market_aggregate_before min = 0 }} }}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tOR = {{
\t\t\t\t\tscope:modeu5_perf14_repair_country_under > modeu5_initialization_rounding_epsilon
\t\t\t\t\tscope:modeu5_perf14_repair_country_over > modeu5_initialization_rounding_epsilon
\t\t\t\t\tscope:modeu5_perf14_repair_market_under > modeu5_initialization_rounding_epsilon
\t\t\t\t\tscope:modeu5_perf14_repair_market_over > modeu5_initialization_rounding_epsilon
\t\t\t\t}}
\t\t\t}}
\t\t\tset_global_variable = {{ name = modeu5_perf14_promotion_failure_detected value = 1 }}
\t\t\tset_global_variable = {{
\t\t\t\tname = modeu5_perf14_promotion_validation_failures
\t\t\t\tvalue = {{
\t\t\t\t\tvalue = global_var:modeu5_perf14_promotion_validation_failures
\t\t\t\t\tadd = 1
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t}}
"""


def render_us10_candidate_scan(good: str) -> str:
    return f"""modeu5_scan_us10_candidate_country_good_{good} = {{
\tsave_temporary_scope_as = modeu5_candidate_country
\tscope:modeu5_us10_resolution_controller = {{
\t\tchange_local_variable = {{ name = modeu5_us10_candidate_count add = 1 }}
\t}}
\tmodeu5_prepare_us10_candidate_good_{good} = yes
\tmodeu5_audit_log_us10_candidate_trace_good_{good} = yes

\tif = {{
\t\tlimit = {{ NOT = {{ scope:modeu5_us10_candidate_allowed > 0 }} }}
\t\tscope:modeu5_us10_resolution_controller = {{
\t\t\tchange_local_variable = {{ name = modeu5_us10_excluded_candidate_count add = 1 }}
\t\t}}
\t}}

\tif = {{
\t\tlimit = {{ scope:modeu5_us10_candidate_allowed > 0 }}
\t\tif = {{
\t\t\tlimit = {{ scope:modeu5_us10_candidate_priority_bucket = 1 }}
\t\t\tscope:modeu5_us10_resolution_controller = {{
\t\t\t\tchange_local_variable = {{ name = modeu5_us10_bucket_1_candidates add = 1 }}
\t\t\t}}
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ scope:modeu5_us10_candidate_priority_bucket = 2 }}
\t\t\tscope:modeu5_us10_resolution_controller = {{
\t\t\t\tchange_local_variable = {{ name = modeu5_us10_bucket_2_candidates add = 1 }}
\t\t\t}}
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ scope:modeu5_us10_candidate_priority_bucket = 3 }}
\t\t\tscope:modeu5_us10_resolution_controller = {{
\t\t\t\tchange_local_variable = {{ name = modeu5_us10_bucket_3_candidates add = 1 }}
\t\t\t}}
\t\t}}
\t\telse = {{
\t\t\tscope:modeu5_us10_resolution_controller = {{
\t\t\t\tchange_local_variable = {{ name = modeu5_us10_bucket_4_candidates add = 1 }}
\t\t\t}}
\t\t}}
\t\tscope:modeu5_us10_resolution_controller = {{
\t\t\tchange_local_variable = {{
\t\t\t\tname = modeu5_us10_total_available_candidate_stock
\t\t\t\tadd = scope:modeu5_us10_candidate_stock
\t\t\t}}
\t\t}}
\t\tscope:modeu5_us10_resolution_controller = {{
\t\t\tif = {{
\t\t\t\tlimit = {{ scope:modeu5_us10_stock_candidate_score > local_var:modeu5_us10_best_stock_priority_score }}
\t\t\t\tset_local_variable = {{ name = modeu5_us10_best_stock_priority_score value = scope:modeu5_us10_stock_candidate_score }}
\t\t\t\tset_local_variable = {{ name = modeu5_us10_best_candidate_stock value = scope:modeu5_us10_candidate_stock }}
\t\t\t\tset_local_variable = {{ name = modeu5_us10_best_candidate_bucket value = scope:modeu5_us10_candidate_priority_bucket }}
\t\t\t}}
\t\t}}
\t}}
}}
"""


def patch_promotion_blocks(text: str) -> str:
    pieces: list[str] = []
    position = 0
    search_from = 0

    while True:
        match = PROMOTION_FN_RE.search(text, search_from)
        if match is None:
            break
        open_index = text.find("{", match.start(), match.end())
        end = find_matching_brace(text, open_index)
        block = text[match.start():end]
        good = match.group("good")

        if OLD_OVERMATERIALIZED_BRANCH in block:
            patched = block.replace(OLD_OVERMATERIALIZED_BRANCH, render_repair_branch(good), 1)
            pieces.append(text[position:match.start()])
            pieces.append(patched)
            position = end

        search_from = end

    pieces.append(text[position:])
    return "".join(pieces)


def patch_us10_candidate_scan_blocks(text: str) -> str:
    pieces: list[str] = []
    position = 0
    search_from = 0

    while True:
        match = US10_CANDIDATE_SCAN_FN_RE.search(text, search_from)
        if match is None:
            break
        open_index = text.find("{", match.start(), match.end())
        end = find_matching_brace(text, open_index)
        good = match.group("good")

        pieces.append(text[position:match.start()])
        pieces.append(render_us10_candidate_scan(good))
        position = end
        search_from = end

    pieces.append(text[position:])
    return "".join(pieces)


def patch_generated_goods(path: Path) -> bool:
    text = path.read_text()
    updated = patch_promotion_blocks(text)
    updated = patch_us10_candidate_scan_blocks(updated)
    assert_balanced_braces(updated, label=str(path))

    if updated == text:
        return False

    path.write_text(updated)
    return True


def main() -> int:
    if len(sys.argv) not in {2, 3, 4}:
        print(
            "usage: postprocess_perf14_overmaterialized_repair.py <modeu5_stock_goods_generated.txt> [legacy_perf14_guarded_test_effects.txt] [legacy_perf14_test_effects.txt]",
            file=sys.stderr,
        )
        return 2

    patch_generated_goods(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

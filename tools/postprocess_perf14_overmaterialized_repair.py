#!/usr/bin/env python3
"""Patch generated PERF-14 promotion aggregate/country-ledger mismatch handling.

The stock-good adapter template contains a conservative failure branch:
country_sum > market_aggregate => promotion failure. The current-save audit
showed a migration/stale-ledger case where detailed country stock can differ
from the market aggregate while the promoted marker is missing.

Business rule for this exception:

    if country_sum is non-zero and country_sum != market_aggregate:
        market aggregate is the cap/source of truth
        rebuild country stocks from the aggregate
        validate
        promote only if the repaired country sum and aggregate agree

If country_sum is zero and the market aggregate is positive, the original
materialization branch remains responsible for seeding country stocks from the
market aggregate, because there is no existing country ledger to rescale.

The PERF-14 AI live-market probe is marked BLOCKED when this repair is observed
so the test log explains that the campaign needed a migration repair instead of
silently passing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PROMOTION_FN_RE = re.compile(
    r"(?m)^modeu5_promote_market_to_detailed_accounting_good_(?P<good>[a-z0-9_]+)\s*=\s*\{"
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

AI_GATE_MARKER = "reason=ai_human_relevant_market_mismatch_repaired"


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
\t\tdebug_log = \"ModeU5 PERF-14 PROMOTION_REPAIR blocked=1 reason=country_sum_differs_from_market_aggregate source=market_aggregate action=rebuild_country_stocks_from_market_aggregate\"

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
\t\t\t\t\t\tvalue = \"variable_map({stock_map}|scope:modeu5_promotion_market)\"
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


def patch_generated_goods(path: Path) -> bool:
    text = path.read_text()
    pieces: list[str] = []
    position = 0
    changed = False
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
            changed = True

        search_from = end

    if not changed:
        return False

    pieces.append(text[position:])
    path.write_text("".join(pieces))
    return True


def patch_ai_gate_blocked_test(path: Path) -> bool:
    text = path.read_text()
    if AI_GATE_MARKER in text:
        return False

    # Patch the second AI stock-mutation probe, after the market was deliberately
    # marked human-relevant.  The earlier AI probe must remain a normal fallback
    # assertion and should not be turned into a migration block.
    needle = """\t\tmodeu5_clear_detailed_accounting_promoted_markets = yes
\t\tscope:modeu5_perf14_ai_market = { save_temporary_scope_as = modeu5_performance_relevant_market }
\t\tmodeu5_mark_performance_relevant_market = yes
\t\tmodeu5_prepare_stock_mutation_accounting_mode = { country = scope:modeu5_perf14_ai_country market = scope:modeu5_perf14_ai_market }
\t\tif = {
"""
    replacement = """\t\tmodeu5_clear_detailed_accounting_promoted_markets = yes
\t\tscope:modeu5_perf14_ai_market = { save_temporary_scope_as = modeu5_performance_relevant_market }
\t\tmodeu5_mark_performance_relevant_market = yes
\t\tmodeu5_prepare_stock_mutation_accounting_mode = { country = scope:modeu5_perf14_ai_country market = scope:modeu5_perf14_ai_market }
\t\tif = {
\t\t\tlimit = {
\t\t\t\thas_global_variable = modeu5_perf14_promotion_overmaterialized_failures
\t\t\t\tglobal_var:modeu5_perf14_promotion_overmaterialized_failures > 0
\t\t\t}
\t\t\tdebug_log = "ModeU5 PERF-14 BLOCKED reason=ai_human_relevant_market_mismatch_repaired source=current_save_country_sum_differs_from_market_aggregate action=rebuild_country_stocks_from_market_aggregate"
\t\t\tset_global_variable = modeu5_test_perf14_performance_mode_cmm_blocked
\t\t\tset_global_variable = modeu5_test_perf14_performance_mode_cmm_blocked_mismatch_repaired
\t\t}
\t\tif = {
"""
    if needle not in text:
        raise SystemExit(f"Could not find AI human-relevant promotion check in {path}")
    path.write_text(text.replace(needle, replacement, 1))
    return True


def patch_perf14_result_reason(path: Path) -> bool:
    text = path.read_text()
    changed = False

    clear_needle = "\tremove_global_variable = modeu5_test_perf14_performance_mode_cmm_blocked\n"
    clear_replacement = (
        "\tremove_global_variable = modeu5_test_perf14_performance_mode_cmm_blocked\n"
        "\tremove_global_variable = modeu5_test_perf14_performance_mode_cmm_blocked_mismatch_repaired\n"
    )
    if "modeu5_test_perf14_performance_mode_cmm_blocked_mismatch_repaired" not in text:
        if clear_needle not in text:
            raise SystemExit(f"Could not find PERF-14 blocked clear marker in {path}")
        text = text.replace(clear_needle, clear_replacement, 1)
        changed = True

    result_needle = """\telse_if = {
\t\tlimit = { has_global_variable = modeu5_test_perf14_performance_mode_cmm_blocked }
\t\tdebug_log = "ModeU5 PERF-14 RESULT performance_mode_cmm BLOCKED missing_fixture"
\t\tdebug_log = "ModeU5 TEST BLOCKED scenario=perf14_performance_mode_cmm"
\t}
"""
    result_replacement = """\telse_if = {
\t\tlimit = { has_global_variable = modeu5_test_perf14_performance_mode_cmm_blocked }
\t\tif = {
\t\t\tlimit = { has_global_variable = modeu5_test_perf14_performance_mode_cmm_blocked_mismatch_repaired }
\t\t\tdebug_log = "ModeU5 PERF-14 RESULT performance_mode_cmm BLOCKED mismatch_repaired"
\t\t}
\t\telse = {
\t\t\tdebug_log = "ModeU5 PERF-14 RESULT performance_mode_cmm BLOCKED missing_fixture"
\t\t}
\t\tdebug_log = "ModeU5 TEST BLOCKED scenario=perf14_performance_mode_cmm"
\t}
"""
    if result_needle in text:
        text = text.replace(result_needle, result_replacement, 1)
        changed = True

    if changed:
        path.write_text(text)
    return changed


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        print(
            "usage: postprocess_perf14_overmaterialized_repair.py <modeu5_stock_goods_generated.txt> <modeu5_perf14_guarded_test_effects.txt> [modeu5_perf14_test_effects.txt]",
            file=sys.stderr,
        )
        return 2

    generated_goods = Path(sys.argv[1])
    guarded_test = Path(sys.argv[2])

    patch_generated_goods(generated_goods)
    patch_ai_gate_blocked_test(guarded_test)
    if len(sys.argv) == 4:
        patch_perf14_result_reason(Path(sys.argv[3]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Guard generated PERF-14 promotion metric reads.

EU5/Jomini treats zero-valued globals as absent in some `global_var:` reads. The
PERF-14 promotion generator intentionally uses per-good scratch globals whose
natural default is zero. Generated code must therefore read those globals only
behind `has_global_variable`, with an explicit temporary/default value.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

GUARDED_GLOBALS = {
    "modeu5_perf14_promotion_market_total_capacity",
    "modeu5_perf14_promotion_market_eligible_country_count",
    "modeu5_perf14_promotion_market_allocated_quantity",
    "modeu5_perf14_promotion_market_negative_capacity_failure",
}

MULTILINE_SAVE_TEMP_RE = re.compile(
    r"(?P<indent>\t*)save_temporary_scope_value_as = \{\n"
    r"(?P=indent)\tname = (?P<temp>[a-zA-Z0-9_]+)\n"
    r"(?P=indent)\tvalue = global_var:(?P<glob>modeu5_perf14_promotion_market_[a-zA-Z0-9_]+)\n"
    r"(?P=indent)\}",
    re.M,
)

ONELINE_SAVE_TEMP_RE = re.compile(
    r"(?P<indent>\t*)save_temporary_scope_value_as = \{ name = (?P<temp>[a-zA-Z0-9_]+) value = global_var:(?P<glob>modeu5_perf14_promotion_market_[a-zA-Z0-9_]+) \}",
    re.M,
)

ACCUMULATOR_RE = re.compile(
    r"(?P<indent>\t*)set_global_variable = \{\n"
    r"(?P=indent)\tname = (?P<glob>modeu5_perf14_promotion_market_[a-zA-Z0-9_]+)\n"
    r"(?P=indent)\tvalue = \{\n"
    r"(?P=indent)\t\tvalue = global_var:(?P=glob)\n"
    r"(?P=indent)\t\tadd = (?P<add>[^\n]+)\n"
    r"(?P=indent)\t\}\n"
    r"(?P=indent)\}",
    re.M,
)


def guard_save_temp(match: re.Match[str]) -> str:
    indent = match.group("indent")
    temp = match.group("temp")
    glob = match.group("glob")

    if glob not in GUARDED_GLOBALS:
        return match.group(0)

    return (
        f"{indent}save_temporary_scope_value_as = {{ name = {temp} value = 0 }}\n"
        f"{indent}if = {{\n"
        f"{indent}\tlimit = {{ has_global_variable = {glob} }}\n"
        f"{indent}\tsave_temporary_scope_value_as = {{\n"
        f"{indent}\t\tname = {temp}\n"
        f"{indent}\t\tvalue = global_var:{glob}\n"
        f"{indent}\t}}\n"
        f"{indent}}}"
    )


def guard_accumulator(match: re.Match[str]) -> str:
    indent = match.group("indent")
    glob = match.group("glob")
    add = match.group("add").strip()

    if glob not in GUARDED_GLOBALS:
        return match.group(0)

    return (
        f"{indent}if = {{\n"
        f"{indent}\tlimit = {{ has_global_variable = {glob} }}\n"
        f"{indent}\tset_global_variable = {{\n"
        f"{indent}\t\tname = {glob}\n"
        f"{indent}\t\tvalue = {{\n"
        f"{indent}\t\t\tvalue = global_var:{glob}\n"
        f"{indent}\t\t\tadd = {add}\n"
        f"{indent}\t\t}}\n"
        f"{indent}\t}}\n"
        f"{indent}}}\n"
        f"{indent}else = {{\n"
        f"{indent}\tset_global_variable = {{ name = {glob} value = {add} }}\n"
        f"{indent}}}"
    )


def assert_no_unguarded_generated_reads(text: str) -> None:
    """Reject generated unsafe promotion reads.

    Guarded replacements still contain `global_var:<name>` inside an explicit
    `has_global_variable` branch, so this check rejects only known direct source
    shapes that caused runtime errors.
    """

    for regex in (MULTILINE_SAVE_TEMP_RE, ONELINE_SAVE_TEMP_RE, ACCUMULATOR_RE):
        for match in regex.finditer(text):
            glob = match.group("glob")
            if glob in GUARDED_GLOBALS:
                line_no = text.count("\n", 0, match.start()) + 1
                raise SystemExit(f"unguarded PERF-14 promotion global read remains at generated line {line_no}: {glob}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: postprocess_perf14_promotion_guards.py <modeu5_stock_goods_generated.txt>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    text = path.read_text()
    updated = ACCUMULATOR_RE.sub(guard_accumulator, text)
    updated = MULTILINE_SAVE_TEMP_RE.sub(guard_save_temp, updated)
    updated = ONELINE_SAVE_TEMP_RE.sub(guard_save_temp, updated)

    assert_no_unguarded_generated_reads(updated)

    path.write_text(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

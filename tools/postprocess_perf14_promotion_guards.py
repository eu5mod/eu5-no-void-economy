#!/usr/bin/env python3
"""Guard generated PERF-14 promotion metric reads.

EU5/Jomini treats zero-valued globals as absent in some `global_var:` reads. The
PERF-14 promotion generator intentionally uses per-good scratch globals whose
natural default is zero. Generated code must therefore read those globals only
behind `has_global_variable`, with an explicit temporary default of 0.
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


def assert_no_unguarded_generated_reads(text: str) -> None:
    """Reject generated one-line/multiline unsafe promotion reads.

    The guarded replacement still contains `value = global_var:<name>`, so this
    check is deliberately structural: it only rejects a direct save-temp read,
    not the guarded branch emitted by `guard_save_temp`.
    """

    for regex in (MULTILINE_SAVE_TEMP_RE, ONELINE_SAVE_TEMP_RE):
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
    updated = MULTILINE_SAVE_TEMP_RE.sub(guard_save_temp, text)
    updated = ONELINE_SAVE_TEMP_RE.sub(guard_save_temp, updated)

    assert_no_unguarded_generated_reads(updated)

    path.write_text(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

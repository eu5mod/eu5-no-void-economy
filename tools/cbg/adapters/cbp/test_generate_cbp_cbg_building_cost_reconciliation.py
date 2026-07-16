#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("generate_cbp_cbg_building_cost_reconciliation.py")
SPEC = importlib.util.spec_from_file_location("reconciliation", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildingCostReconciliationTests(unittest.TestCase):
    def test_comments_negative_discount_and_records_positive_contribution(self) -> None:
        block = [
            "example = {",
            "\tmodifier = {",
            "\t\tlocal_build_buildings_cost = -0.10",
            "\t}",
            "}",
        ]
        rendered, contribution = MODULE.comment_discount_lines(block)
        self.assertAlmostEqual(contribution, 0.10)
        self.assertIn("# local_build_buildings_cost = -0.10", "\n".join(rendered))

    def test_ignores_positive_cost_penalty(self) -> None:
        block = ["example = {", "\tlocal_build_buildings_cost = 0.10", "}"]
        rendered, contribution = MODULE.comment_discount_lines(block)
        self.assertEqual(rendered, block)
        self.assertEqual(contribution, 0)

    def test_runtime_formula_is_diminishing(self) -> None:
        contribution = MODULE.Contribution(MODULE.KINDS[0], "example", 1.0, "example.txt")
        effect = MODULE.render_effect([contribution], 1.5)
        self.assertIn("multiply = 1.5", effect)
        self.assertIn("divide = var:modeu5_building_cost_denominator", effect)
        self.assertIn("subtract = 1", effect)

    def test_only_supported_source_directories_are_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            common = root / "in_game/common"
            for directory in ("laws", "government_reforms", "estate_privileges", "advances"):
                path = common / directory
                path.mkdir(parents=True)
                (path / "sample.txt").write_text(
                    "sample = {\n\tlocal_build_buildings_cost = -0.10\n}\n",
                    encoding="utf-8",
                )
            package = root / "package"
            args = type("Args", (), {
                "game_root": root,
                "package_root": package,
                "factor": 1.5,
            })()
            payload = MODULE.build(args)
            files = {item["file"] for item in payload["transformations"]}
            self.assertTrue(any("/laws/" in path for path in files))
            self.assertTrue(any("/government_reforms/" in path for path in files))
            self.assertTrue(any("/estate_privileges/" in path for path in files))
            self.assertFalse(any("/advances/" in path for path in files))


if __name__ == "__main__":
    unittest.main()

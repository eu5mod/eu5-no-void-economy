from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from tools.cbg.adapters.cbp.generate_cbp_cbg_building_spec import (
    build_injection_fragment,
    build_prefixed_production_methods,
    build_spec,
    render_localization,
)


class BuildingSpecTests(unittest.TestCase):
    def test_override_mode_keeps_every_change_in_same_path_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            building_dir = root / "game/in_game/common/building_types"
            building_dir.mkdir(parents=True)
            (building_dir / "buildings.txt").write_text(
                "warehouse = {\n"
                "\tmodifier = {\n"
                "\t\tlocal_merchant_capacity = 2\n"
                "\t}\n"
                "\tmarket_center_modifier = {\n"
                "\t\tmaximum_stockpile_capacity = 200\n"
                "\t}\n"
                "\tunique_production_methods = {\n"
                "\t\twarehouse_method = {\n"
                "\t\t\tproduced = tools\n"
                "\t\t\toutput = 1\n"
                "\t\t\tcategory = workshop_input\n"
                "\t\t}\n"
                "\t}\n"
                "}\n",
                encoding="utf-8",
            )
            payload = build_spec(
                argparse.Namespace(
                    game_root=root / "game",
                    repo_root=Path(__file__).resolve().parents[5],
                    generation_mode="override",
                    output_multiplier=1.15,
                    trade_capacity_multiplier=1.15,
                    foreign_trade_capacity_multiplier=2.0,
                    maintenance_multiplier=1.0,
                    trade_maintenance_multiplier=1.0,
                    estate_power_multiplier=1.0,
                    minting_multiplier=1.0,
                    political_multiplier=1.0,
                )
            )

        rules = payload["transformations"]
        self.assertTrue(rules)
        self.assertTrue(
            all(rule["render_mode"] == "verbatim_with_header" for rule in rules)
        )
        rendered = "\n".join(rules[0]["value"])
        self.assertIn("local_merchant_capacity = 2.3", rendered)
        self.assertIn("# maximum_stockpile_capacity = 200", rendered)
        self.assertIn("output = 1.15", rendered)
        self.assertEqual(
            payload["scope_contract"]["generation_mode"],
            "override",
        )
        self.assertFalse(
            any("output_file" in rule for rule in rules)
        )

    def test_structural_source_uses_exact_path_and_additive_source_uses_inject(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            building_dir = root / "game/in_game/common/building_types"
            building_dir.mkdir(parents=True)
            (building_dir / "structural.txt").write_text(
                "workshop = {\n"
                "\tunique_production_methods = {\n"
                "\t\tworkshop_method = {\n"
                "\t\t\tiron = 1\n"
                "\t\t\tproduced = wheat\n"
                "\t\t\toutput = 1\n"
                "\t\t\tcategory = workshop_input\n"
                "\t\t}\n"
                "\t\tworkshop_upkeep = {\n"
                "\t\t\ttools = 1\n"
                "\t\t\tcategory = building_maintenance\n"
                "\t\t}\n"
                "\t}\n"
                "\tmodifier = {\n"
                "\t\tlocal_merchant_capacity = 2\n"
                "\t}\n"
                "}\n",
                encoding="utf-8",
            )
            (building_dir / "additive.txt").write_text(
                "marketplace = {\n"
                "\tmodifier = {\n"
                "\t\tlocal_merchant_capacity = 2\n"
                "\t}\n"
                "}\n",
                encoding="utf-8",
            )
            payload = build_spec(
                argparse.Namespace(
                    game_root=root / "game",
                    repo_root=Path(__file__).resolve().parents[5],
                    generation_mode="compatibility",
                    output_multiplier=1.15,
                    trade_capacity_multiplier=1.15,
                    foreign_trade_capacity_multiplier=2.0,
                    maintenance_multiplier=1.2,
                    trade_maintenance_multiplier=1.0,
                    estate_power_multiplier=0.5,
                    minting_multiplier=2.0,
                    political_multiplier=0.75,
                )
            )

        structural = [
            rule
            for rule in payload["transformations"]
            if rule["file"].endswith("/structural.txt")
        ]
        additive = [
            rule
            for rule in payload["transformations"]
            if rule["file"].endswith("/additive.txt")
        ]
        self.assertTrue(structural)
        self.assertEqual(
            {rule["render_mode"] for rule in structural},
            {"verbatim_with_header", "inject_objects"},
        )
        self.assertTrue(additive)
        self.assertTrue(
            all(rule["render_mode"] == "inject_objects" for rule in additive)
        )
        self.assertIn(
            "in_game/common/building_types/structural.txt",
            payload["scope_contract"]["owned_outputs"],
        )
        self.assertIn(
            (
                "in_game/common/building_types/"
                "cbp_local_merchant_capacity_structural.txt"
            ),
            payload["scope_contract"]["owned_outputs"],
        )
        self.assertIn(
            (
                "in_game/common/building_types/"
                "cbp_us09_production_methods_structural.txt"
            ),
            payload["scope_contract"]["owned_outputs"],
        )
        self.assertIn(
            (
                "in_game/common/building_types/"
                "cbp_local_merchant_capacity_additive.txt"
            ),
            payload["scope_contract"]["owned_outputs"],
        )
        self.assertNotIn(
            "in_game/common/building_types/cbp_structural.txt",
            payload["scope_contract"]["owned_outputs"],
        )

    def test_output_bonus_is_a_prefixed_concurrent_method(self):
        source = [
            "workshop = {",
            "\tunique_production_methods = {",
            "\t\tworkshop_method = {",
            "\t\t\tiron = 1",
            "\t\t\tproduced = tools",
            "\t\t\toutput = 1.1",
            "\t\t\tcategory = workshop_input",
            "\t\t}",
            "\t}",
            "}",
        ]

        variants = build_prefixed_production_methods(source, 1.15)

        self.assertEqual(
            variants["workshop"],
            [[
                "\t\tcbp_us09_workshop_method = {",
                "\t\t\tiron = 1",
                "\t\t\tproduced = tools",
                "\t\t\toutput = 1.265 # VANILLA = 1.1",
                "\t\t\tcategory = workshop_input",
                "\t\t}",
            ]],
        )
        fragment = build_injection_fragment(
            source,
            source,
            "workshop",
            variants["workshop"],
        )
        self.assertIn("\tunique_production_methods = {", fragment)
        self.assertIn("\t\tcbp_us09_workshop_method = {", fragment)
        self.assertNotIn("\t\tworkshop_method = {", fragment)

    def test_localization_reuses_vanilla_method_label(self):
        payload = {
            "scope_contract": {
                "production_method_localizations": {
                    "cbp_us09_workshop_method": "workshop_method",
                }
            }
        }
        self.assertEqual(
            render_localization(payload),
            (
                "\ufeffl_english:\n"
                ' cbp_us09_workshop_method:0 "(CBP) Improved $workshop_method$"\n'
            ),
        )

    def test_advance_unlock_is_mirrored_for_prefixed_method(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            building_dir = root / "game/in_game/common/building_types"
            advance_dir = root / "game/in_game/common/advances"
            building_dir.mkdir(parents=True)
            advance_dir.mkdir(parents=True)
            (building_dir / "workshops.txt").write_text(
                "workshop = {\n"
                "\tunique_production_methods = {\n"
                "\t\tadvanced_method = {\n"
                "\t\t\tiron = 1\n"
                "\t\t\tproduced = tools\n"
                "\t\t\toutput = 2\n"
                "\t\t\tcategory = workshop_input\n"
                "\t\t}\n"
                "\t}\n"
                "}\n",
                encoding="utf-8",
            )
            (advance_dir / "industry.txt").write_text(
                "advanced_industry = {\n"
                "\tunlock_production_method = advanced_method\n"
                "}\n",
                encoding="utf-8",
            )
            payload = build_spec(
                argparse.Namespace(
                    game_root=root / "game",
                    repo_root=Path(__file__).resolve().parents[5],
                    generation_mode="compatibility",
                    output_multiplier=1.15,
                    trade_capacity_multiplier=1.0,
                    foreign_trade_capacity_multiplier=1.0,
                    maintenance_multiplier=1.0,
                    trade_maintenance_multiplier=1.0,
                    estate_power_multiplier=1.0,
                    minting_multiplier=1.0,
                    political_multiplier=1.0,
                )
            )

        unlock_rules = [
            rule
            for rule in payload["transformations"]
            if rule["file"].endswith("/advances/industry.txt")
        ]
        self.assertEqual(len(unlock_rules), 1)
        self.assertEqual(
            unlock_rules[0]["value"],
            [
                "advanced_industry = {",
                "\tunlock_production_method = cbp_us09_advanced_method",
                "}",
            ],
        )
        self.assertEqual(
            unlock_rules[0]["output_file"],
            "in_game/common/advances/cbp_inject_us09_industry.txt",
        )
        self.assertEqual(
            payload["scope_contract"]["mirrored_production_method_unlocks"],
            1,
        )

    def test_modifier_injection_uses_delta_not_absolute_target(self):
        source = [
            "marketplace = {",
            "\tmodifier = {",
            "\t\tlocal_merchant_capacity = 2",
            "\t}",
            "}",
        ]
        transformed = [
            "marketplace = {",
            "\tmodifier = {",
            "\t\tlocal_merchant_capacity = 2.3 # VANILLA = 2",
            "\t}",
            "}",
        ]

        self.assertEqual(
            build_injection_fragment(source, transformed, "marketplace"),
            [
                "marketplace = {",
                "\tmodifier = {",
                (
                    "\t\tlocal_merchant_capacity = 0.3 "
                    "# VANILLA = 2; TARGET = 2.3"
                ),
                "\t}",
                "}",
            ],
        )

    def test_modifier_injection_can_be_isolated_by_field_family(self):
        source = [
            "marketplace = {",
            "\tmodifier = {",
            "\t\tlocal_merchant_capacity = 2",
            "\t\tminting_income_factor = 0.1",
            "\t}",
            "}",
        ]
        transformed = [
            "marketplace = {",
            "\tmodifier = {",
            "\t\tlocal_merchant_capacity = 2.3",
            "\t\tminting_income_factor = 0.2",
            "\t}",
            "}",
        ]

        fragment = build_injection_fragment(
            source,
            transformed,
            "marketplace",
            additive_fields={"local_merchant_capacity"},
        )
        self.assertTrue(
            any(
                line.startswith("\t\tlocal_merchant_capacity = 0.3")
                for line in fragment
            )
        )
        self.assertFalse(any("minting_income_factor" in line for line in fragment))

    def test_stockpile_capacity_is_cancelled_with_negative_delta(self):
        source = [
            "warehouse = {",
            "\tmarket_center_modifier = {",
            "\t\tmaximum_stockpile_capacity = 200",
            "\t}",
            "}",
        ]
        transformed = [
            "warehouse = {",
            "\tmarket_center_modifier = {",
            "\t\t# maximum_stockpile_capacity = 200",
            "\t}",
            "}",
        ]

        self.assertEqual(
            build_injection_fragment(source, transformed, "warehouse"),
            [
                "warehouse = {",
                "\tmarket_center_modifier = {",
                (
                    "\t\tmaximum_stockpile_capacity = -200.0 "
                    "# VANILLA = 200; TARGET = 0"
                ),
                "\t}",
                "}",
            ],
        )


if __name__ == "__main__":
    unittest.main()

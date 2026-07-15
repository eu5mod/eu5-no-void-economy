from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSFORMER = REPO_ROOT / "tools" / "transform_cbp_economy_building_overrides.py"


class BuildingOverrideTransformerTest(unittest.TestCase):
    def test_fixed_monthly_political_modifier_is_scaled(self):
        temporary, result, output, manifest = self.run_transformer(
            """political_building = {
\tmodifier = {
\t\tmonthly_legitimacy = 0.4
\t}
}
"""
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("monthly_legitimacy = 0.3 # VANILLA = 0.4", output.read_text())
        payload = json.loads(manifest.read_text())
        self.assertEqual(
            payload["changed_buildings"]["political_building"][0]["field"],
            "monthly_legitimacy",
        )
        temporary.cleanup()

    def run_transformer(self, source_text: str, *, basename: str = "fixture.txt"):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        source = root / basename
        output = root / "output" / basename
        manifest = root / "manifests" / f"{Path(basename).stem}.json"
        source.write_text(source_text, encoding="utf-8")
        command = [
            sys.executable,
            str(TRANSFORMER),
            "--source",
            str(source),
            "--source-basename",
            basename,
            "--source-label",
            f"<EU5_GAME_COMMON_DIR>/building_types/{basename}",
            "--output",
            str(output),
            "--manifest",
            str(manifest),
            "--output-multiplier",
            "1.1",
            "--trade-capacity-multiplier",
            "1.15",
            "--maintenance-multiplier",
            "0.7",
            "--trade-building-maintenance-multiplier",
            "0.5",
            "--us07-trade-burghers-estate-power-multiplier",
            "0.5",
            "--minting-income-multiplier",
            "2",
            "--goods",
            "wheat",
            "cloth",
            "paper",
        ]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        return temporary, result, output, manifest

    def test_irrelevant_file_is_skipped(self):
        temporary, result, output, manifest = self.run_transformer(
            "irrelevant = {\n\tfoo = 1\n}\n"
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertFalse(output.exists())
        self.assertFalse(manifest.exists())

    def test_changes_are_building_scoped_and_unchanged_body_is_preserved(self):
        source = (
            "changed = {\n"
            "\toutput = 10\n"
            "}\n\n"
            "untouched = {\n"
            "\tfoo = 1  \n"
            "}\n"
        )
        temporary, result, output, manifest = self.run_transformer(source)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        output_text = output.read_text(encoding="utf-8")
        self.assertIn("\toutput = 11.0", output_text)
        self.assertIn("\tfoo = 1  \n", output_text)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["changed_building_count"], 1)
        self.assertEqual(data["unchanged_building_count"], 1)
        self.assertEqual(data["changed_buildings"]["changed"][0]["field"], "output")

    def test_maintenance_and_stockpile_changes_are_declared(self):
        source = (
            "warehouse = {\n"
            "\tmaintenance = {\n"
            "\t\twheat = 4\n"
            "\t\tcategory = building_maintenance\n"
            "\t}\n"
            "\tmaximum_stockpile_capacity = 200\n"
            "}\n"
        )
        temporary, result, output, manifest = self.run_transformer(source)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("wheat = 2.8", output.read_text(encoding="utf-8"))
        self.assertIn("# maximum_stockpile_capacity = 200", output.read_text(encoding="utf-8"))
        changes = json.loads(manifest.read_text(encoding="utf-8"))["changed_buildings"][
            "warehouse"
        ]
        self.assertEqual(
            {change["field"] for change in changes},
            {"maintenance:wheat", "maximum_stockpile_capacity"},
        )

    def test_market_warehouse_structural_only_file_is_generated(self):
        source = (
            "market_warehouse = {\n"
            "\tlocation_potential = {\n"
            "\t\tis_market_center = yes\n"
            "\t}\n"
            "}\n"
        )
        temporary, result, output, manifest = self.run_transformer(
            source, basename="market_buildings.txt"
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text(encoding="utf-8").count("always = no"), 2)
        change = json.loads(manifest.read_text(encoding="utf-8"))["changed_buildings"][
            "market_warehouse"
        ][0]
        self.assertEqual(change["action"], "disable")

    def test_ambiguous_structure_fails_closed(self):
        temporary, result, output, manifest = self.run_transformer(
            "broken = {\n\toutput = 10\n"
        )
        self.addCleanup(temporary.cleanup)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported or ambiguous building structure", result.stderr)
        self.assertFalse(output.exists())
        self.assertFalse(manifest.exists())

    def test_generation_is_deterministic(self):
        source = "changed = {\n\tlocal_merchant_capacity = 2\n}\n"
        first_temp, first_result, first_output, first_manifest = self.run_transformer(source)
        self.addCleanup(first_temp.cleanup)
        second_temp, second_result, second_output, second_manifest = self.run_transformer(source)
        self.addCleanup(second_temp.cleanup)
        self.assertEqual(first_result.returncode, 0, first_result.stderr)
        self.assertEqual(second_result.returncode, 0, second_result.stderr)
        self.assertEqual(first_output.read_bytes(), second_output.read_bytes())
        self.assertEqual(first_manifest.read_bytes(), second_manifest.read_bytes())

    def test_minting_change_is_registered(self):
        temporary, result, output, manifest = self.run_transformer(
            "mint = {\n\tminting_income_factor = 0.1\n}\n"
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("minting_income_factor = 0.2", output.read_text(encoding="utf-8"))
        change = json.loads(manifest.read_text(encoding="utf-8"))["changed_buildings"][
            "mint"
        ][0]
        self.assertEqual(change["field"], "minting_income_factor")


if __name__ == "__main__":
    unittest.main()

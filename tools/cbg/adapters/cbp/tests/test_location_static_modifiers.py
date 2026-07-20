#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
SOURCE = "main_menu/common/static_modifiers/location.txt"
OUTPUT = "main_menu/common/static_modifiers/cbp_location.txt"


class LocationStaticModifierParityTest(unittest.TestCase):
    def test_development_stockpile_capacity_is_commented_and_other_fields_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game_root = root / "game"
            source = game_root / SOURCE
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                """expensive_food_in_location = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_population_growth = -0.001
\tlocal_life_expectancy = -2
}

cheap_food_in_location = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_population_growth = 0.002
\tlocal_life_expectancy = 2
}

market_center = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_merchant_capacity = 2
\tmaximum_stockpile_capacity = 25
}

surplus_jobs = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_migration_attraction = 0.1
\tlocal_construction_speed = -0.1
}

development = {
\tgame_data = {
\t\tcategory = location
\t}
\tmaximum_stockpile_capacity = 5
\tlocal_construction_speed = 0.01
}
""",
                encoding="utf-8",
            )

            reference = root / "reference" / "cbp_location.txt"
            subprocess.run(
                [
                    "bash",
                    "tools/generate_cbp_location_overrides.sh",
                    "--source-file",
                    str(source),
                    "--output-file",
                    str(reference),
                ],
                cwd=REPO_ROOT,
                check=True,
            )

            spec = root / "location.json"
            subprocess.run(
                [
                    sys.executable,
                    "tools/cbg/adapters/cbp/generate_cbp_cbg_location_spec.py",
                    "--output",
                    str(spec),
                ],
                cwd=REPO_ROOT,
                check=True,
            )
            payload = json.loads(spec.read_text(encoding="utf-8"))
            development_rules = [
                rule
                for rule in payload["transformations"]
                if rule.get("object") == "development"
                and rule.get("field") == "maximum_stockpile_capacity"
            ]
            self.assertEqual(len(development_rules), 1)
            self.assertEqual(development_rules[0]["operation"], "comment_out")

            candidate_root = root / "candidate"
            subprocess.run(
                [
                    sys.executable,
                    "tools/cbg/community_balance_generator.py",
                    "--game-root",
                    str(game_root),
                    "--spec",
                    str(spec),
                    "--output-root",
                    str(candidate_root),
                    "--manifest",
                    str(candidate_root / "manifest.json"),
                ],
                cwd=REPO_ROOT,
                check=True,
            )
            candidate = candidate_root / OUTPUT
            self.assertEqual(reference.read_bytes(), candidate.read_bytes())

            output = candidate.read_text(encoding="utf-8")
            development = output[output.index("development = {") :]
            self.assertIn(
                "# maximum_stockpile_capacity = 5 # CBG: commented by cbp-location-static-modifiers",
                development,
            )
            self.assertNotRegex(
                development,
                re.compile(r"^\s*maximum_stockpile_capacity\s*=", re.MULTILINE),
            )
            self.assertIn("local_construction_speed = 0.01", development)
            self.assertIn("maximum_stockpile_capacity = 0 # VANILLA VALUE IS 25", output)


if __name__ == "__main__":
    unittest.main()

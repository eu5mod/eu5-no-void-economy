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

BASE_LOCATION_FIXTURE = """expensive_food_in_location = {
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
"""

NOOP_LOCATION_FIXTURE = """expensive_food_in_location = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_population_growth = 0
\tlocal_life_expectancy = -2
}

cheap_food_in_location = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_population_growth = 0.001
\tlocal_life_expectancy = 2
}

market_center = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_merchant_capacity = 2
\tmaximum_stockpile_capacity = 0
}

surplus_jobs = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_migration_attraction = 0.2
\tlocal_construction_speed = -0.1
}
"""

DEVELOPMENT_FIXTURE = """
development = {
\tgame_data = {
\t\tcategory = location
\t}
\tmaximum_stockpile_capacity = 5
\tlocal_construction_speed = 0.01
}
"""


class LocationStaticModifierParityTest(unittest.TestCase):
    def run_generators(self, root: Path, source_text: str):
        game_root = root / "game"
        source = game_root / SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(source_text, encoding="utf-8")

        reference = root / "reference" / "cbp_location.txt"
        legacy = subprocess.run(
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
            capture_output=True,
            text=True,
        )

        spec = root / "location.json"
        spec_run = subprocess.run(
            [
                sys.executable,
                "tools/cbg/adapters/cbp/generate_cbp_cbg_location_spec.py",
                "--source-file",
                str(source),
                "--output",
                str(spec),
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(spec.read_text(encoding="utf-8"))

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
            capture_output=True,
            text=True,
        )
        candidate = candidate_root / OUTPUT
        self.assertEqual(reference.is_file(), candidate.is_file())
        if reference.is_file():
            self.assertEqual(reference.read_bytes(), candidate.read_bytes())
            output = candidate.read_text(encoding="utf-8")
        else:
            output = None
        return (
            output,
            payload,
            legacy.stderr,
            spec_run.stderr,
            source,
        )

    def test_development_stockpile_capacity_is_commented_and_other_fields_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, payload, legacy_stderr, spec_stderr, _ = self.run_generators(
                Path(temporary),
                BASE_LOCATION_FIXTURE + DEVELOPMENT_FIXTURE,
            )

            self.assertIsNotNone(output)
            assert output is not None
            development_rules = [
                rule
                for rule in payload["transformations"]
                if rule.get("object") == "development"
                and rule.get("field") == "maximum_stockpile_capacity"
            ]
            self.assertEqual(len(development_rules), 1)
            self.assertEqual(development_rules[0]["operation"], "comment_out")
            self.assertEqual(legacy_stderr, "")
            self.assertEqual(spec_stderr, "")

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

    def test_changed_vanilla_value_warns_with_link_and_does_not_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            changed_development = DEVELOPMENT_FIXTURE.replace(
                "maximum_stockpile_capacity = 5",
                "maximum_stockpile_capacity = 8",
            )
            output, payload, legacy_stderr, spec_stderr, source = self.run_generators(
                Path(temporary),
                BASE_LOCATION_FIXTURE + changed_development,
            )

            self.assertIsNotNone(output)
            assert output is not None
            self.assertTrue(
                any(
                    rule.get("object") == "development"
                    and rule.get("operation") == "comment_out"
                    for rule in payload["transformations"]
                )
            )
            self.assertIn(
                "# maximum_stockpile_capacity = 8 # CBG: commented by cbp-location-static-modifiers",
                output,
            )
            expected_message = (
                "Vanilla value changed: development.maximum_stockpile_capacity "
                "was reviewed at 5 and is now 8"
            )
            expected_link = source.resolve().as_uri() + "#L"
            for warning in (legacy_stderr, spec_stderr):
                self.assertIn("[⚠️]", warning)
                self.assertIn(expected_message, warning)
                self.assertIn(expected_link, warning)
                self.assertIn("CBP will continue", warning)

    def test_missing_development_block_warns_and_does_not_fail_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, payload, legacy_stderr, spec_stderr, source = self.run_generators(
                Path(temporary),
                BASE_LOCATION_FIXTURE,
            )

            self.assertIsNotNone(output)
            assert output is not None
            development_rules = [
                rule
                for rule in payload["transformations"]
                if rule.get("object") == "development"
            ]
            self.assertEqual(development_rules, [])
            self.assertNotIn("development = {", output)
            for warning in (legacy_stderr, spec_stderr):
                self.assertIn("[⚠️] Vanilla development static modifier", warning)
                self.assertIn(source.resolve().as_uri(), warning)
            self.assertIn("maximum_stockpile_capacity = 0 # VANILLA VALUE IS 25", output)

    def test_unchanged_replacement_objects_are_not_copied(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, payload, legacy_stderr, spec_stderr, _ = self.run_generators(
                Path(temporary),
                NOOP_LOCATION_FIXTURE + DEVELOPMENT_FIXTURE,
            )

            self.assertIsNotNone(output)
            assert output is not None
            self.assertEqual(legacy_stderr, "")
            self.assertEqual(spec_stderr, "")
            self.assertEqual(
                [rule.get("object") for rule in payload["transformations"]],
                ["development"],
            )
            for unchanged_object in (
                "expensive_food_in_location",
                "cheap_food_in_location",
                "market_center",
                "surplus_jobs",
            ):
                self.assertNotIn(f"{unchanged_object} = {{", output)
            self.assertIn("development = {", output)
            self.assertIn("# maximum_stockpile_capacity = 5", output)

    def test_output_file_is_omitted_when_every_policy_is_a_noop(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, payload, legacy_stderr, spec_stderr, source = self.run_generators(
                Path(temporary),
                NOOP_LOCATION_FIXTURE,
            )

            self.assertIsNone(output)
            self.assertEqual(payload["transformations"], [])
            for warning in (legacy_stderr, spec_stderr):
                self.assertIn("[⚠️] Vanilla development static modifier", warning)
                self.assertIn(source.resolve().as_uri(), warning)


if __name__ == "__main__":
    unittest.main()

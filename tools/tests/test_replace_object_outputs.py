#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "tools/cbp/cbp_community_balance_generator.py"


class ReplaceObjectOutputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.game = self.root / "game"
        self.output = self.root / "output"
        self.spec = self.root / "spec.json"
        self.manifest = self.output / "manifest.json"

    def tearDown(self):
        self.temporary.cleanup()

    def write_source(self, relative: str, content: str) -> Path:
        path = self.game / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_generator(self, payload: dict[str, object], *, check: bool = True):
        self.spec.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--game-root",
                str(self.game),
                "--spec",
                str(self.spec),
                "--output-root",
                str(self.output),
                "--manifest",
                str(self.manifest),
            ],
            cwd=REPO_ROOT,
            check=check,
            capture_output=True,
            text=True,
        )

    def test_emits_only_changed_object_in_prefixed_replace_file(self):
        relative = "in_game/common/building_types/market.txt"
        self.write_source(
            relative,
            "marketplace = {\n\tmaintenance = 1\n}\n\n"
            "warehouse = {\n\tmaintenance = 2\n}\n",
        )
        self.run_generator(
            {
                "schema_version": 1,
                "mod_id": "test-replace-output",
                "transformations": [
                    {
                        "file": relative,
                        "object": "marketplace",
                        "field": "maintenance",
                        "operation": "replace",
                        "value": 0.5,
                        "render_mode": "replace_objects",
                        "header": ["# Generated override."],
                        "provenance": "preserve",
                    },
                    {
                        "file": relative,
                        "object": "warehouse",
                        "field": "maintenance",
                        "operation": "replace",
                        "value": 2,
                        "render_mode": "replace_objects",
                        "header": ["# Generated override."],
                        "provenance": "preserve",
                    },
                ],
            }
        )

        destination = self.output / "in_game/common/building_types/cbp_market.txt"
        self.assertTrue(destination.is_file())
        self.assertFalse((self.output / relative).exists())
        content = destination.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("# Generated override.\n\n"))
        self.assertIn("REPLACE:marketplace = {", content)
        self.assertIn("maintenance = 0.5", content)
        self.assertNotIn("warehouse = {", content)

        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            [entry["path"] for entry in manifest["files"]],
            ["in_game/common/building_types/cbp_market.txt"],
        )
        self.assertEqual(manifest["files"][0]["database_entry_mode"], "REPLACE")
        self.assertEqual(
            [entry["object"] for entry in manifest["files"][0]["transformations"]],
            ["marketplace"],
        )

    def test_removes_trailing_whitespace_from_selected_objects(self):
        relative = "in_game/common/building_types/production_saltpeter.txt"
        self.write_source(
            relative,
            "saltpeter_guild = {\n\toutput = 1\n}\t\n\n"
            "saltpeter_workshop = {\n\toutput = 1.1\n}\n",
        )
        self.run_generator(
            {
                "schema_version": 1,
                "mod_id": "test-object-boundary-whitespace",
                "transformations": [
                    {
                        "file": relative,
                        "object": "saltpeter_guild",
                        "field": "output",
                        "operation": "replace",
                        "value": 1.15,
                        "render_mode": "replace_objects",
                        "header": ["# Generated override."],
                        "provenance": "preserve",
                    }
                ],
            }
        )

        destination = (
            self.output
            / "in_game/common/building_types/cbp_production_saltpeter.txt"
        )
        generated = destination.read_bytes()
        self.assertIn(b"REPLACE:saltpeter_guild = {", generated)
        self.assertNotIn(b"\n}\t\n", generated)
        self.assertNotIn(b"\t\n", generated)
        self.assertNotIn(b"saltpeter_workshop", generated)

    def test_emits_sparse_inject_object_in_separate_prefixed_file(self):
        relative = "in_game/common/building_types/market.txt"
        self.write_source(
            relative,
            "marketplace = {\n"
            "\tmodifier = {\n"
            "\t\tlocal_merchant_capacity = 1\n"
            "\t}\n"
            "}\n",
        )
        self.run_generator(
            {
                "schema_version": 1,
                "mod_id": "test-inject-output",
                "transformations": [
                    {
                        "file": relative,
                        "object": "marketplace",
                        "field": "__object__",
                        "operation": "replace_object",
                        "value": [
                            "marketplace = {",
                            "\tmodifier = {",
                            "\t\tlocal_merchant_capacity = 0.15",
                            "\t}",
                            "}",
                        ],
                        "render_mode": "inject_objects",
                        "header": ["# Generated injection."],
                        "provenance": "preserve",
                    }
                ],
            }
        )

        destination = (
            self.output / "in_game/common/building_types/cbp_inject_market.txt"
        )
        content = destination.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("# Generated injection.\n\n"))
        self.assertIn("INJECT:marketplace = {", content)
        self.assertIn("local_merchant_capacity = 0.15", content)
        self.assertNotIn("REPLACE:marketplace", content)

        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest["files"][0]["database_entry_mode"], "INJECT")

    def test_one_vanilla_source_can_emit_replace_and_inject_outputs(self):
        relative = "in_game/common/building_types/market.txt"
        self.write_source(
            relative,
            "warehouse = {\n\tavailability = yes\n}\n\n"
            "marketplace = {\n\tmodifier = {\n"
            "\t\tlocal_merchant_capacity = 1\n\t}\n}\n",
        )
        self.run_generator(
            {
                "schema_version": 1,
                "mod_id": "test-hybrid-output",
                "transformations": [
                    {
                        "file": relative,
                        "object": "warehouse",
                        "field": "availability",
                        "operation": "replace",
                        "value": "no",
                        "render_mode": "replace_objects",
                        "provenance": "preserve",
                    },
                    {
                        "file": relative,
                        "object": "marketplace",
                        "field": "__object__",
                        "operation": "replace_object",
                        "value": [
                            "marketplace = {",
                            "\tmodifier = {",
                            "\t\tlocal_merchant_capacity = 0.15",
                            "\t}",
                            "}",
                        ],
                        "render_mode": "inject_objects",
                        "provenance": "preserve",
                    },
                ],
            }
        )

        replace = self.output / "in_game/common/building_types/cbp_market.txt"
        inject = (
            self.output / "in_game/common/building_types/cbp_inject_market.txt"
        )
        self.assertIn("REPLACE:warehouse", replace.read_text(encoding="utf-8"))
        self.assertIn("INJECT:marketplace", inject.read_text(encoding="utf-8"))
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                entry["path"]: entry["database_entry_mode"]
                for entry in manifest["files"]
            },
            {
                "in_game/common/building_types/cbp_market.txt": "REPLACE",
                "in_game/common/building_types/cbp_inject_market.txt": "INJECT",
            },
        )

    def test_explicit_output_must_be_cbp_prefixed(self):
        relative = "main_menu/common/static_modifiers/location.txt"
        self.write_source(relative, "development = {\n\tvalue = 1\n}\n")
        result = self.run_generator(
            {
                "schema_version": 1,
                "mod_id": "test-invalid-output",
                "transformations": [
                    {
                        "file": relative,
                        "output_file": "main_menu/common/static_modifiers/location_patch.txt",
                        "object": "development",
                        "field": "value",
                        "operation": "replace",
                        "value": 2,
                        "render_mode": "replace_objects",
                    }
                ],
            },
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must start with 'cbp_'", result.stderr)

    def test_explicit_inject_output_accepts_cbp_prefixed_filename(self):
        relative = "in_game/common/building_types/market.txt"
        self.write_source(relative, "marketplace = {\n\tvalue = 1\n}\n")
        self.run_generator(
            {
                "schema_version": 1,
                "mod_id": "test-explicit-inject-output",
                "transformations": [
                    {
                        "file": relative,
                        "output_file": (
                            "in_game/common/building_types/cbp_market_patch.txt"
                        ),
                        "object": "marketplace",
                        "field": "value",
                        "operation": "replace",
                        "value": 2,
                        "render_mode": "inject_objects",
                    }
                ],
            }
        )

        destination = (
            self.output / "in_game/common/building_types/cbp_market_patch.txt"
        )
        self.assertIn("INJECT:marketplace", destination.read_text(encoding="utf-8"))

    def test_explicit_inject_output_must_be_cbp_prefixed(self):
        relative = "in_game/common/building_types/market.txt"
        self.write_source(relative, "marketplace = {\n\tvalue = 1\n}\n")
        result = self.run_generator(
            {
                "schema_version": 1,
                "mod_id": "test-invalid-inject-output",
                "transformations": [
                    {
                        "file": relative,
                        "output_file": (
                            "in_game/common/building_types/market_patch.txt"
                        ),
                        "object": "marketplace",
                        "field": "value",
                        "operation": "replace",
                        "value": 2,
                        "render_mode": "inject_objects",
                    }
                ],
            },
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must start with 'cbp_'", result.stderr)

    def test_rejects_non_common_database(self):
        relative = "in_game/events/test.txt"
        self.write_source(relative, "test.1 = {\n\tvalue = 1\n}\n")
        result = self.run_generator(
            {
                "schema_version": 1,
                "mod_id": "test-invalid-surface",
                "transformations": [
                    {
                        "file": relative,
                        "object": "test.1",
                        "field": "value",
                        "operation": "replace",
                        "value": 2,
                        "render_mode": "replace_objects",
                    }
                ],
            },
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is not supported", result.stderr)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.cbg.community_balance_generator import generate, load_intents


class EffectiveChangeDetectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.game = self.root / "game"
        self.output = self.root / "output"

    def tearDown(self):
        self.temporary.cleanup()

    def write_source(self, relative: str, content: str) -> Path:
        path = self.game / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_spec(self, transformations: list[dict[str, object]]) -> Path:
        path = self.root / "spec.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "mod_id": "effective-change-test",
                    "business_rule": "Test effective CBG business-rule mutations.",
                    "transformations": transformations,
                }
            ),
            encoding="utf-8",
        )
        return path

    def run_spec(
        self,
        transformations: list[dict[str, object]],
        manifest_path: Path | None = None,
    ) -> dict[str, object]:
        spec = self.write_spec(transformations)
        intents, _custom_fields = load_intents([spec], self.game)
        return generate(self.game, self.output, intents, manifest_path)

    def test_scalar_noops_do_not_emit_files_despite_headers(self):
        relative = "in_game/common/building_types/noop.txt"
        self.write_source(
            relative,
            "workshop = {\n\tmaintenance = 1.0\n\toutput = 0\n}\n",
        )

        manifest = self.run_spec(
            [
                {
                    "file": relative,
                    "object": "workshop",
                    "field": "maintenance",
                    "operation": "replace",
                    "value": 1,
                    "conflict": "compose",
                    "render_mode": "normalized_with_header",
                    "header": ["# Generated override."],
                },
                {
                    "file": relative,
                    "object": "workshop",
                    "field": "maintenance",
                    "operation": "multiply",
                    "value": 1,
                    "conflict": "compose",
                    "render_mode": "normalized_with_header",
                    "header": ["# Generated override."],
                },
                {
                    "file": relative,
                    "object": "workshop",
                    "field": "output",
                    "operation": "add",
                    "value": 0,
                    "render_mode": "normalized_with_header",
                    "header": ["# Generated override."],
                },
            ]
        )

        self.assertEqual(manifest["files"], [])
        self.assertFalse((self.output / relative).exists())

    def test_glob_outputs_only_files_with_effective_mutations(self):
        unchanged = "in_game/common/building_types/unchanged.txt"
        changed = "in_game/common/building_types/changed.txt"
        self.write_source(unchanged, "building = {\n\tmaintenance = 2\n}\n")
        self.write_source(changed, "building = {\n\tmaintenance = 3\n}\n")

        manifest = self.run_spec(
            [
                {
                    "file": "in_game/common/building_types/*.txt",
                    "object": "building",
                    "field": "maintenance",
                    "operation": "replace",
                    "value": 2,
                    "render_mode": "verbatim_with_header",
                    "header": ["# Generated override."],
                }
            ]
        )

        self.assertEqual(
            [entry["path"] for entry in manifest["files"]],
            [changed],
        )
        self.assertFalse((self.output / unchanged).exists())
        changed_output = self.output / changed
        self.assertTrue(changed_output.is_file())
        self.assertIn("# Generated override.", changed_output.read_text(encoding="utf-8"))
        self.assertIn("maintenance = 2", changed_output.read_text(encoding="utf-8"))

    def test_selected_object_output_excludes_unchanged_objects(self):
        relative = "main_menu/common/static_modifiers/location.txt"
        output_relative = "main_menu/common/static_modifiers/cbp_location.txt"
        self.write_source(
            relative,
            "unchanged = {\n\tvalue = 1.0\n}\n\nchanged = {\n\tvalue = 3\n}\n",
        )

        manifest = self.run_spec(
            [
                {
                    "file": relative,
                    "output_file": output_relative,
                    "render_mode": "selected_objects",
                    "header": ["# Generated override."],
                    "object": "unchanged",
                    "field": "value",
                    "operation": "replace",
                    "value": 1,
                    "conflict": "compose",
                },
                {
                    "file": relative,
                    "output_file": output_relative,
                    "render_mode": "selected_objects",
                    "header": ["# Generated override."],
                    "object": "changed",
                    "field": "value",
                    "operation": "replace",
                    "value": 2,
                    "conflict": "compose",
                },
            ]
        )

        self.assertEqual(len(manifest["files"]), 1)
        output = (self.output / output_relative).read_text(encoding="utf-8")
        self.assertNotIn("unchanged = {", output)
        self.assertIn("changed = {", output)
        self.assertIn("value = 2", output)

    def test_symbolic_and_block_multiply_by_one_are_noops(self):
        symbolic = "in_game/common/building_types/symbolic.txt"
        block = "in_game/common/building_types/block.txt"
        self.write_source(symbolic, "building = {\n\tmaintenance = maintenance_medium\n}\n")
        self.write_source(
            block,
            "building = {\n\tmaintenance = {\n\t\tvalue = base_maintenance\n\t}\n}\n",
        )

        manifest = self.run_spec(
            [
                {
                    "file": [symbolic, block],
                    "object": "building",
                    "field": "maintenance",
                    "operation": "multiply",
                    "value": 1,
                }
            ]
        )

        self.assertEqual(manifest["files"], [])
        self.assertFalse((self.output / symbolic).exists())
        self.assertFalse((self.output / block).exists())
        self.assertFalse(
            (
                self.output
                / "main_menu/common/script_values/cbg_generated_scalars.txt"
            ).exists()
        )

    def test_semantically_identical_upsert_block_is_a_noop(self):
        relative = "in_game/common/building_types/block_values.txt"
        self.write_source(
            relative,
            "building = {\n\trequirements = { # Vanilla comment\n"
            "\t\ttools = 2.0 # source\n\t\twood = 1\n\t}\n}\n",
        )

        manifest = self.run_spec(
            [
                {
                    "file": relative,
                    "object": "building",
                    "field": "requirements",
                    "operation": "upsert_block",
                    "value": {"tools": 2, "wood": 1.0},
                }
            ]
        )

        self.assertEqual(manifest["files"], [])
        self.assertFalse((self.output / relative).exists())

    def test_stale_owned_output_is_removed_when_rule_becomes_noop(self):
        relative = "in_game/common/building_types/stale.txt"
        self.write_source(relative, "building = {\n\tmaintenance = 3\n}\n")
        manifest_path = self.output / "manifest.json"

        changed = self.run_spec(
            [
                {
                    "file": relative,
                    "object": "building",
                    "field": "maintenance",
                    "operation": "replace",
                    "value": 2,
                }
            ]
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(changed), encoding="utf-8")
        destination = self.output / relative
        self.assertTrue(destination.is_file())

        unchanged = self.run_spec(
            [
                {
                    "file": relative,
                    "object": "building",
                    "field": "maintenance",
                    "operation": "replace",
                    "value": 3,
                }
            ],
            manifest_path,
        )

        self.assertEqual(unchanged["files"], [])
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()

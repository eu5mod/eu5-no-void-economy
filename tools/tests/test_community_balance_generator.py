import json
import tempfile
import unittest
from pathlib import Path

from tools.community_balance_generator import generate, load_intents


VANILLA = """marketplace = {
\tmaintenance = 1.0
\tmaximum_stockpile_capacity = 200
\tmodifier = {
\t\tlocal_merchant_capacity = 1
\t}
}
"""


class CommunityBalanceGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        self.output = self.root / "output"
        source = self.game / "in_game/common/building_types/market.txt"
        source.parent.mkdir(parents=True)
        source.write_text(VANILLA)

    def tearDown(self):
        self.temp.cleanup()

    def spec(self, name, owner, transformations, custom_fields=None):
        path = self.root / name
        path.write_text(json.dumps({
            "schema_version": 1,
            "mod_id": owner,
            "custom_fields": custom_fields or {},
            "transformations": transformations,
        }))
        return path

    def transform(self, *specs):
        intents, _ = load_intents(list(specs), self.game)
        manifest = generate(self.game, self.output, intents)
        text = (self.output / "in_game/common/building_types/market.txt").read_text()
        return text, manifest

    def target(self, operation, value=None, field="maintenance", **extra):
        result = {
            "file": "in_game/common/building_types/market.txt",
            "object": "marketplace",
            "field": field,
            "operation": operation,
        }
        if value is not None:
            result["value"] = value
        result.update(extra)
        return result

    def add_second_building(self):
        source = self.game / "in_game/common/building_types/market.txt"
        source.write_text(source.read_text() + "warehouse = {\n\tmaintenance = maintenance_medium\n}\n")

    def test_numeric_operations_compose(self):
        first = self.spec("a.json", "mod-a", [self.target("multiply", 0.5, conflict="compose")])
        second = self.spec("b.json", "mod-b", [self.target("add", 0.1, conflict="compose")])
        text, manifest = self.transform(first, second)
        self.assertIn("maintenance = 0.6", text)
        self.assertEqual("1.0", manifest["files"][0]["transformations"][0]["before"])
        self.assertEqual("0.6", manifest["files"][0]["transformations"][1]["after"])

    def test_replace_and_clamp(self):
        spec = self.spec("a.json", "mod-a", [
            self.target("replace", 4, conflict="compose"),
            self.target("clamp", {"max": 3}, conflict="compose"),
        ])
        text, _ = self.transform(spec)
        self.assertIn("maintenance = 3", text)

    def test_replace_accepts_safe_clausewitz_scalar(self):
        spec = self.spec("a.json", "mod-a", [self.target("replace", "maintenance_medium")])
        text, _ = self.transform(spec)
        self.assertIn("maintenance = maintenance_medium", text)

    def test_added_scalar_rejects_script_injection(self):
        spec = self.spec("a.json", "mod-a", [self.target(
            "add_field", "{ bad = yes }", field="new_field"
        )])
        with self.assertRaisesRegex(ValueError, "safe scalar token"):
            self.transform(spec)

    def test_comment_out(self):
        spec = self.spec("a.json", "mod-a", [self.target(
            "comment_out", field="maximum_stockpile_capacity"
        )])
        text, _ = self.transform(spec)
        self.assertIn("# maximum_stockpile_capacity = 200 # CBG: commented by mod-a", text)

    def test_remove(self):
        spec = self.spec("a.json", "mod-a", [self.target(
            "remove", field="maximum_stockpile_capacity"
        )])
        text, _ = self.transform(spec)
        self.assertNotIn("maximum_stockpile_capacity", text)

    def test_add_field_and_custom(self):
        spec = self.spec("a.json", "mod-a", [
            self.target("add_field", 8, field="maximum_market_capacity", position={"after": "maintenance"}),
            self.target("add_custom", 2, field="mod_a_custom_capacity"),
        ], {"mod_a_custom_capacity": "modifier"})
        text, _ = self.transform(spec)
        self.assertIn("maximum_market_capacity = 8 # CBG: added by mod-a", text)
        self.assertIn("mod_a_custom_capacity = 2 # CBG: added by mod-a", text)

    def test_custom_requires_declaration(self):
        spec = self.spec("a.json", "mod-a", [self.target(
            "add_custom", 2, field="mod_a_custom_capacity"
        )])
        with self.assertRaisesRegex(ValueError, "must be declared"):
            load_intents([spec], self.game)

    def test_multi_mod_conflict_fails_closed(self):
        first = self.spec("a.json", "mod-a", [self.target("multiply", 0.5)])
        second = self.spec("b.json", "mod-b", [self.target("replace", 1)])
        intents, _ = load_intents([first, second], self.game)
        with self.assertRaisesRegex(ValueError, "Unresolved multi-mod conflict"):
            generate(self.game, self.output, intents)

    def test_nested_object_path(self):
        spec = self.spec("a.json", "mod-a", [{
            **self.target("multiply", 1.5, field="local_merchant_capacity"),
            "object": "marketplace/modifier",
        }])
        text, _ = self.transform(spec)
        self.assertIn("local_merchant_capacity = 1.5", text)

    def test_bulk_multiply_numeric_and_symbolic_values(self):
        self.add_second_building()
        spec = self.spec("a.json", "mod-a", [{
            **self.target("multiply", 0.5),
            "object": "**",
            "occurrences": "all",
        }])
        text, manifest = self.transform(spec)
        self.assertIn("maintenance = 0.5", text)
        self.assertRegex(text, r"maintenance = cbg_mod_a_maintenance_[a-f0-9]{12}")
        aliases = self.output / "main_menu/common/script_values/cbg_generated_scalars.txt"
        self.assertIn("value = maintenance_medium", aliases.read_text())
        self.assertEqual(2, len(manifest["files"][0]["transformations"]))

    def test_bulk_multiply_appends_factor_to_value_block(self):
        source = self.game / "in_game/common/building_types/market.txt"
        source.write_text(source.read_text().replace(
            "maintenance = 1.0",
            "maintenance = {\n\t\tvalue = base_maintenance\n\t}",
        ))
        spec = self.spec("a.json", "mod-a", [{
            **self.target("multiply", 0.75),
            "object": "**",
            "occurrences": "all",
        }])
        text, _ = self.transform(spec)
        self.assertIn("multiply = 0.75 # CBG: mod-a", text)

    def test_bulk_glob_can_skip_files_without_field(self):
        other = self.game / "in_game/common/building_types/other.txt"
        other.write_text("other = {\n\toutput = 2\n}\n")
        spec = self.spec("a.json", "mod-a", [{
            "file": "in_game/common/building_types/*.txt",
            "object": "**",
            "field": "maintenance",
            "operation": "multiply",
            "value": 0.5,
            "occurrences": "all",
            "on_missing": "skip",
        }])
        text, manifest = self.transform(spec)
        self.assertIn("maintenance = 0.5", text)
        self.assertEqual(1, len(manifest["files"]))
        self.assertFalse((self.output / "in_game/common/building_types/other.txt").exists())

    def test_file_selector_accepts_exact_path_array(self):
        other = self.game / "in_game/common/building_types/other.txt"
        other.write_text("marketplace = {\n\tmaintenance = 2\n}\n")
        target = self.target("multiply", 0.5)
        target["file"] = [
            "in_game/common/building_types/market.txt",
            "in_game/common/building_types/other.txt",
        ]
        spec = self.spec("a.json", "mod-a", [target])
        intents, _ = load_intents([spec], self.game)
        manifest = generate(self.game, self.output, intents)
        self.assertEqual(2, len(manifest["files"]))

    def test_bulk_multiply_transforms_compact_inline_assignment(self):
        source = self.game / "in_game/common/building_types/market.txt"
        source.write_text(source.read_text() + "probe = { else = { maintenance = 4 } }\n")
        spec = self.spec("a.json", "mod-a", [{
            **self.target("multiply", 0.5),
            "object": "**",
            "occurrences": "all",
        }])
        text, _ = self.transform(spec)
        self.assertIn("else = { maintenance = 2 }", text)

    def test_bulk_exclusion_skips_direct_and_inline_values_but_not_blocks(self):
        source = self.game / "in_game/common/building_types/market.txt"
        source.write_text(
            "marketplace = {\n"
            "\tmaintenance = shared_value\n"
            "\tprobe = { else = { maintenance = shared_value } }\n"
            "\tother = {\n\t\tmaintenance = {\n\t\t\tvalue = shared_value\n\t\t}\n\t}\n"
            "\tmaximum_stockpile_capacity = 200\n"
            "}\n"
        )
        spec = self.spec("a.json", "mod-a", [{
            **self.target("multiply", 0.5),
            "object": "**",
            "occurrences": "all",
            "exclude_values": ["shared_value"],
        }])
        text, manifest = self.transform(spec)
        self.assertEqual(2, text.count("maintenance = shared_value"))
        self.assertEqual(1, len(manifest["files"][0]["transformations"]))
        self.assertIn("multiply = 0.5 # CBG: mod-a", text)

    def test_refuses_unowned_existing_output(self):
        destination = self.output / "in_game/common/building_types/market.txt"
        destination.parent.mkdir(parents=True)
        destination.write_text("foreign output\n")
        spec = self.spec("a.json", "mod-a", [self.target("multiply", 0.5)])
        intents, _ = load_intents([spec], self.game)
        with self.assertRaisesRegex(ValueError, "not owned"):
            generate(self.game, self.output, intents)

    def test_refuses_modified_owned_output(self):
        spec = self.spec("a.json", "mod-a", [self.target("multiply", 0.5)])
        intents, _ = load_intents([spec], self.game)
        manifest = generate(self.game, self.output, intents)
        manifest_path = self.output / "cbg_manifest.json"
        manifest_path.write_text(json.dumps(manifest))
        destination = self.output / "in_game/common/building_types/market.txt"
        destination.write_text("locally modified\n")
        with self.assertRaisesRegex(ValueError, "locally modified"):
            generate(self.game, self.output, intents, manifest_path)


if __name__ == "__main__":
    unittest.main()

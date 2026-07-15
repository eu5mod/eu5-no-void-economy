import json
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from tools.cbg.community_balance_generator import Intent, Target, apply_intent, generate, load_intents
VANILLA = """marketplace = {
\tmaintenance = 1.0
\tmaximum_stockpile_capacity = 200
\tmodifier = {
\t\tlocal_merchant_capacity = 1
\t}
}
"""


class CommunityBalanceGeneratorTests(unittest.TestCase):
    def test_top_level_field_can_be_transformed(self):
        lines = ["first = 10\n", "object = {\n", "\tfirst = 20\n", "}\n"]
        intent = Intent(
            owner="test",
            target=Target(PurePosixPath("test.txt"), (), "first"),
            operation="multiply",
            value=0.5,
            conflict="error",
            position_after=None,
            source_spec="test.json",
            sequence=0,
            occurrences="one",
            on_missing="error",
            exclude_values=(),
            where={},
            exclude_objects=(),
            provenance="cbg",
        )

        outcomes = apply_intent(lines, intent, {})

        self.assertEqual(outcomes[0]["after"], "5")
        self.assertIn("first = 5", lines[0])
        self.assertIn("first = 20", lines[2])

    def test_block_can_be_replaced_or_inserted(self):
        lines = [
            "warehouse = {\n", "\tlocation_potential = {\n",
            "\t\tis_market_center = yes\n", "\t}\n", "}\n",
        ]
        common = dict(
            owner="test", conflict="error", source_spec="test.json",
            occurrences="one", on_missing="error", exclude_values=(),
            where={}, exclude_objects=(),
            provenance="cbg",
        )
        replace = Intent(
            target=Target(PurePosixPath("test.txt"), ("warehouse",), "location_potential"),
            operation="upsert_block", value={"always": "no"}, position_after=None,
            sequence=1, **common,
        )
        insert = Intent(
            target=Target(PurePosixPath("test.txt"), ("warehouse",), "country_potential"),
            operation="upsert_block", value={"always": "no"},
            position_after="location_potential", sequence=2, **common,
        )

        apply_intent(lines, replace, {})
        apply_intent(lines, insert, {})

        self.assertEqual(sum("always = no" in line for line in lines), 2)
        self.assertFalse(any("is_market_center" in line for line in lines))

    def test_complete_object_can_be_replaced_from_compiled_edge_case_plan(self):
        lines = ["warehouse = {\n", "\tcapacity = 20\n", "}\n"]
        intent = Intent(
            owner="test",
            target=Target(PurePosixPath("test.txt"), ("warehouse",), "__object__"),
            operation="replace_object",
            value=["warehouse = {", "\t# capacity = 20", "}"],
            conflict="error",
            position_after=None,
            source_spec="test.json",
            sequence=0,
            occurrences="one",
            on_missing="error",
            exclude_values=(),
            where={},
            exclude_objects=(),
            provenance="preserve",
        )

        outcomes = apply_intent(lines, intent, {})

        self.assertEqual(outcomes[0]["line_action"], "object_replaced")
        self.assertEqual(lines, ["warehouse = {\n", "\t# capacity = 20\n", "}\n"])

    def test_complete_file_can_be_replaced_from_composed_policy_ledger(self):
        lines = ["old = 1\n"]
        intent = Intent(
            owner="test",
            target=Target(PurePosixPath("test.txt"), (), "__file__"),
            operation="replace_file",
            value="new = 2\n",
            conflict="error",
            position_after=None,
            source_spec="test.json",
            sequence=0,
            occurrences="one",
            on_missing="error",
            exclude_values=(),
            where={},
            exclude_objects=(),
            provenance="preserve",
        )

        outcomes = apply_intent(lines, intent, {})

        self.assertEqual(outcomes[0]["line_action"], "file_replaced")
        self.assertEqual(lines, ["new = 2\n"])

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

    def test_vanilla_provenance_matches_legacy_generator_comment(self):
        source = self.game / "in_game/common/building_types/market.txt"
        source.write_text(source.read_text() + "\n")
        spec = self.spec("a.json", "mod-a", [{
            **self.target("multiply", 0.5),
            "provenance": "vanilla",
        }])
        text, _ = self.transform(spec)
        self.assertIn("maintenance = 0.5 # VANILLA = 1.0", text)
        self.assertNotIn("VANILLA/PRIOR", text)
        self.assertFalse(text.endswith("\n\n"))

    def test_preserve_provenance_changes_only_the_scalar(self):
        source = self.game / "in_game/common/building_types/market.txt"
        original = source.read_text().replace("maintenance = 1.0", "maintenance = 1.0 # source")
        source.write_text(original)
        spec = self.spec("a.json", "mod-a", [{
            **self.target("multiply", 0.5),
            "provenance": "preserve",
        }])
        text, _ = self.transform(spec)
        self.assertEqual(text, original.replace("maintenance = 1.0", "maintenance = 0.5"))

    def test_selected_objects_can_publish_to_dedicated_output(self):
        spec = self.spec("a.json", "mod-a", [{
            **self.target("replace", 0, field="maximum_stockpile_capacity"),
            "output_file": "main_menu/common/static_modifiers/mod_location.txt",
            "render_mode": "selected_objects",
            "header": ["# Generated test output."],
            "provenance": "vanilla_value",
        }])
        intents, _ = load_intents([spec], self.game)
        manifest = generate(self.game, self.output, intents)
        destination = self.output / "main_menu/common/static_modifiers/mod_location.txt"
        text = destination.read_text()
        self.assertTrue(text.startswith("# Generated test output.\n\nmarketplace = {"))
        self.assertIn("maximum_stockpile_capacity = 0 # VANILLA VALUE IS 200", text)
        self.assertEqual(manifest["files"][0]["path"], destination.relative_to(self.output).as_posix())

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

    def test_existing_identical_output_can_be_adopted_once(self):
        spec = self.spec("a.json", "mod-a", [self.target("multiply", 0.5)])
        intents, _ = load_intents([spec], self.game)
        generated = generate(self.game, self.output, intents)
        manifest_path = self.output / "manifest.json"
        manifest_path.write_text(json.dumps(generated))

        manifest_path.unlink()
        adopted = generate(
            self.game,
            self.output,
            intents,
            manifest_path,
            adopt_identical=True,
        )
        self.assertEqual(generated["files"][0]["generated_sha256"], adopted["files"][0]["generated_sha256"])

    def test_existing_different_output_cannot_be_adopted(self):
        spec = self.spec("a.json", "mod-a", [self.target("multiply", 0.5)])
        intents, _ = load_intents([spec], self.game)
        destination = self.output / "in_game/common/building_types/market.txt"
        destination.parent.mkdir(parents=True)
        destination.write_text("locally changed\n")

        with self.assertRaisesRegex(ValueError, "not owned"):
            generate(self.game, self.output, intents, adopt_identical=True)

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

    def test_master_rule_can_exclude_file_globs(self):
        debug = self.game / "in_game/common/building_types/debug/probe.txt"
        debug.parent.mkdir()
        debug.write_text("marketplace = {\n\tmaintenance = 4\n}\n")
        target = self.target("multiply", 0.5)
        target.update({
            "file": "in_game/common/building_types/**/*.txt",
            "exclude_files": ["in_game/common/building_types/debug/**/*.txt"],
        })
        spec = self.spec("a.json", "mod-a", [target])
        intents, _ = load_intents([spec], self.game)
        manifest = generate(self.game, self.output, intents)
        self.assertEqual(1, len(manifest["files"]))
        self.assertFalse((self.output / debug.relative_to(self.game)).exists())

    def test_master_rule_filters_by_ancestor_fields(self):
        source = self.game / "in_game/common/building_types/market.txt"
        source.write_text(
            "workshop = {\n\tcategory = production_category\n\treq = {\n"
            "\t\ttools = 2\n\t\tcategory = building_maintenance\n\t}\n}\n"
            "marketplace = {\n\tcategory = trade_category\n\treq = {\n"
            "\t\ttools = 2\n\t\tcategory = building_maintenance\n\t}\n}\n"
        )
        rule = {
            "file": "in_game/common/building_types/*.txt",
            "object": "**",
            "field": "tools",
            "operation": "multiply",
            "value": 0.5,
            "occurrences": "all",
            "on_missing": "skip",
            "where": {
                "inside": {"category": "building_maintenance"},
                "not_inside": {"category": "trade_category"},
            },
        }
        text, manifest = self.transform(self.spec("a.json", "mod-a", [rule]))
        self.assertEqual(1, len(manifest["files"][0]["transformations"]))
        self.assertEqual(1, text.count("tools = 1"))
        self.assertEqual(1, text.count("tools = 2"))

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

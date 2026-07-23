#!/usr/bin/env python3

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from tools.cbg.adapters.cbp.generate_cbp_cbg_default_values_spec import build_spec
from tools.cbg.adapters.cbp.optional_vanilla_fields import (
    PROFIT_MARGIN_FIELDS,
    discover_optional_root_numeric_fields,
)


class OptionalVanillaFieldsTest(unittest.TestCase):
    def make_game(self, default_values_text: str) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        game_root = Path(temporary.name)
        target = game_root / "main_menu/common/script_values/default_values.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(default_values_text, encoding="utf-8")
        (game_root / "in_game/events").mkdir(parents=True)
        (game_root / "in_game/common").mkdir(parents=True)
        return game_root

    def test_removed_profit_margin_fields_warn_and_are_skipped(self):
        game_root = self.make_game(
            "stability_weak_bonus = 2.5\n"
            "guild_profit_margin = 0.2\n"
        )
        warning = io.StringIO()
        available = discover_optional_root_numeric_fields(
            game_root / "main_menu/common/script_values/default_values.txt",
            PROFIT_MARGIN_FIELDS,
            policy_name="production profit-margin",
            warning_stream=warning,
        )

        self.assertEqual(available, ("guild_profit_margin",))
        self.assertIn("[⚠️]", warning.getvalue())
        self.assertIn("rural_profit_margin", warning.getvalue())

        spec = build_spec(game_root)
        fields = {rule["field"] for rule in spec["transformations"]}
        self.assertIn("guild_profit_margin", fields)
        self.assertNotIn("rural_profit_margin", fields)
        self.assertEqual(
            spec["scope_contract"]["active_optional_vanilla_fields"],
            ["guild_profit_margin"],
        )

    def test_all_removed_profit_margin_fields_leave_generation_valid(self):
        game_root = self.make_game("stability_weak_bonus = 2.5\n")
        spec = build_spec(game_root)
        fields = {rule["field"] for rule in spec["transformations"]}

        self.assertIn("stability_weak_bonus", fields)
        self.assertTrue(fields.isdisjoint(PROFIT_MARGIN_FIELDS))
        self.assertEqual(spec["scope_contract"]["active_optional_vanilla_fields"], [])

    def test_present_non_numeric_optional_field_is_unsafe(self):
        game_root = self.make_game("guild_profit_margin = dynamic_value\n")
        with self.assertRaisesRegex(ValueError, "Unsupported non-numeric"):
            discover_optional_root_numeric_fields(
                game_root / "main_menu/common/script_values/default_values.txt",
                PROFIT_MARGIN_FIELDS,
                policy_name="production profit-margin",
                warning_stream=io.StringIO(),
            )

    def test_duplicate_optional_field_is_unsafe(self):
        game_root = self.make_game(
            "guild_profit_margin = 0.2\n"
            "guild_profit_margin = 0.3\n"
        )
        with self.assertRaisesRegex(ValueError, "multiple definitions"):
            discover_optional_root_numeric_fields(
                game_root / "main_menu/common/script_values/default_values.txt",
                PROFIT_MARGIN_FIELDS,
                policy_name="production profit-margin",
                warning_stream=io.StringIO(),
            )


if __name__ == "__main__":
    unittest.main()

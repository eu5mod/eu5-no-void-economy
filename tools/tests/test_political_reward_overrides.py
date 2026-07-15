#!/usr/bin/env python3

import importlib.util
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "generate_political_reward_overrides.py"
SPEC = importlib.util.spec_from_file_location("political_rewards", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PoliticalRewardTransformTest(unittest.TestCase):
    def test_political_intensity_selector_excludes_similarly_named_engine_fields(self):
        self.assertFalse(MODULE.is_explicit_half_default_value("has_stability_investment"))
        self.assertFalse(MODULE.is_explicit_half_default_value("stability_investment_penalty"))
        self.assertTrue(MODULE.is_explicit_half_default_value("stability_radical_penalty"))
        self.assertTrue(MODULE.is_explicit_half_default_value("horde_unity_severe_bonus"))

    def test_all_political_default_penalties_and_bonuses_are_halved(self):
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary)
            default_values = game / "main_menu/common/script_values/default_values.txt"
            default_values.parent.mkdir(parents=True, exist_ok=True)
            expected = {
                f"{prefix}_{intensity}_{kind}"
                for prefix in MODULE.POLITICAL_DEFAULT_VALUE_PREFIXES
                for intensity in ("weak", "mild", "radical")
                for kind in ("penalty", "bonus")
            }
            default_values.write_text(
                "".join(f"{name} = 10\n" for name in sorted(expected)), encoding="utf-8"
            )
            (game / "in_game/events").mkdir(parents=True, exist_ok=True)
            (game / "in_game/common").mkdir(parents=True, exist_ok=True)

            policies = MODULE.centralizable_script_values(game)

            self.assertEqual(set(policies), expected)
            self.assertTrue(all(str(factor) == "0.5" for factor in policies.values()))

    def test_event_tokens_numbers_and_blocks_are_halved(self):
        source = """option = {
\tadd_stability = stability_mild_bonus
\tadd_legitimacy = -10 # signed penalty
\tadd_devotion = {
\t\tvalue = root.devotion
\t}
}
"""
        result = MODULE.transform_assignments(source, MODULE.EVENT_EFFECTS, Decimal("0.5"), "event")
        self.assertEqual(result.count, 2)
        self.assertIn("add_legitimacy = -5 # VANILLA = -10; signed penalty", result.text)
        self.assertIn("\t\tmultiply = 0.5\n\t}", result.text)
        self.assertIn("add_stability = stability_mild_bonus", result.text)
        self.assertEqual(result.aliases, {})

    def test_parliament_transform_is_limited_to_outcomes(self):
        source = """issue = {
\tmodifier_when_in_debate = { add_stability = stability_mild_bonus }
\ton_debate_passed = {
\t\tadd_stability = stability_severe_bonus
\t}
}
"""
        result = MODULE.transform_assignments(
            source, MODULE.EVENT_EFFECTS, Decimal("0.5"), "parliament", {"on_debate_passed", "on_debate_failed"}
        )
        self.assertEqual(result.count, 0)
        self.assertIn("modifier_when_in_debate = { add_stability = stability_mild_bonus }", result.text)

    def test_common_instant_effect_is_composed_from_vanilla_value(self):
        source = "law = {\n\tadd_legitimacy = legitimacy_mild_bonus\n}\n"
        current = "law = {\n\tadd_legitimacy = old_package_value # retained comment\n}\n"
        result = MODULE.compose_simple_assignments(
            source, current, MODULE.EVENT_EFFECTS, Decimal("0.5"), "instant"
        )
        self.assertEqual(result.count, 0)
        self.assertEqual(result.text, current)

    def test_research_fixed_values_keep_three_quarters(self):
        source = """advance = {
\tmonthly_legitimacy = 0.1
\tstability_investment = small_stability_investment
}
"""
        result = MODULE.transform_assignments(source, MODULE.RESEARCH_MODIFIERS, Decimal("0.75"), "research")
        self.assertIn("monthly_legitimacy = 0.075", result.text)
        self.assertEqual(result.count, 1)
        self.assertIn("stability_investment = small_stability_investment", result.text)

    def test_scaled_numbers_are_stable(self):
        self.assertEqual(MODULE.scaled_number("0.1", Decimal("0.75")), "0.075")
        self.assertEqual(MODULE.scaled_number("-2", Decimal("0.5")), "-1")

    def test_transformed_comment_keeps_vanilla_value(self):
        self.assertEqual(
            MODULE.transformed_comment("0.35"),
            "# VANILLA = 0.35",
        )
        self.assertEqual(
            MODULE.transformed_comment("0.35", "# source note"),
            "# VANILLA = 0.35; source note",
        )

    def test_profit_margin_targets_are_ten_percent_higher(self):
        expected = {
            "0.20": "0.22",
            "0.25": "0.275",
            "0.30": "0.33",
            "0.35": "0.385",
        }
        for vanilla, transformed in expected.items():
            self.assertEqual(
                MODULE.scaled_number(vanilla, MODULE.PROFIT_MARGIN_FACTOR),
                transformed,
            )

    def test_honor_is_preserved_when_it_shares_a_scaled_value(self):
        source = "add_honor = government_power_weak_bonus\n"
        result = MODULE.preserve_nonpolitical_token_uses(
            source, {"government_power_weak_bonus": Decimal("0.5")}
        )
        self.assertEqual(result.count, 1)
        self.assertIn("add_honor = cbp_preserve_add_honor_", result.text)
        self.assertEqual(next(iter(result.aliases.values()))[1], "preserve:0.5")

    def test_political_use_keeps_the_central_scaled_value(self):
        source = "add_government_power = government_power_weak_bonus\n"
        result = MODULE.preserve_nonpolitical_token_uses(
            source, {"government_power_weak_bonus": Decimal("0.5")}
        )
        self.assertEqual(result.count, 0)
        self.assertEqual(result.text, source)

    def test_inline_numeric_is_halved_and_shared_symbol_is_unchanged(self):
        source = "else = { add_government_power = 5 }\n10 = { add_stability = shared_value }\n"
        result = MODULE.transform_inline_assignments(
            source, MODULE.EVENT_EFFECTS, Decimal("0.5"), "inline", set()
        )
        self.assertEqual(result.count, 1)
        self.assertIn("add_government_power = 2.5", result.text)
        self.assertIn("add_stability = shared_value", result.text)
        self.assertEqual(result.aliases, {})


if __name__ == "__main__":
    unittest.main()

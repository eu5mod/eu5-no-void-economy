#!/usr/bin/env python3

import importlib.util
import sys
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
        self.assertEqual(result.count, 3)
        self.assertIn("add_legitimacy = -5 # signed penalty", result.text)
        self.assertIn("\t\tmultiply = 0.5\n\t}", result.text)
        self.assertIn("stability_mild_bonus", next(iter(result.aliases.values()))[0])

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
        self.assertEqual(result.count, 1)
        self.assertIn("modifier_when_in_debate = { add_stability = stability_mild_bonus }", result.text)

    def test_common_instant_effect_is_composed_from_vanilla_value(self):
        source = "law = {\n\tadd_legitimacy = legitimacy_mild_bonus\n}\n"
        current = "law = {\n\tadd_legitimacy = old_package_value # retained comment\n}\n"
        result = MODULE.compose_simple_assignments(
            source, current, MODULE.EVENT_EFFECTS, Decimal("0.5"), "instant"
        )
        self.assertEqual(result.count, 1)
        self.assertIn("add_legitimacy = cbp_instant_add_legitimacy_", result.text)
        self.assertIn("# retained comment", result.text)

    def test_research_fixed_values_keep_three_quarters(self):
        source = """advance = {
\tmonthly_legitimacy = 0.1
\tstability_investment = small_stability_investment
}
"""
        result = MODULE.transform_assignments(source, MODULE.RESEARCH_MODIFIERS, Decimal("0.75"), "research")
        self.assertIn("monthly_legitimacy = 0.075", result.text)
        self.assertEqual(result.count, 2)

    def test_scaled_numbers_are_stable(self):
        self.assertEqual(MODULE.scaled_number("0.1", Decimal("0.75")), "0.075")
        self.assertEqual(MODULE.scaled_number("-2", Decimal("0.5")), "-1")

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

    def test_inline_numeric_and_shared_values_are_halved(self):
        source = "else = { add_government_power = 5 }\n10 = { add_stability = shared_value }\n"
        result = MODULE.transform_inline_assignments(
            source, MODULE.EVENT_EFFECTS, Decimal("0.5"), "inline", set()
        )
        self.assertEqual(result.count, 2)
        self.assertIn("add_government_power = 2.5", result.text)
        self.assertIn("add_stability = cbp_inline_add_stability_shared_value_", result.text)


if __name__ == "__main__":
    unittest.main()

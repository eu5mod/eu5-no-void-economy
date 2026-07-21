#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tools.cbg.adapters.cbp.generate_cbp_cbg_rgo_prices_spec import (
    ABSOLUTE_MODE,
    LEGACY_INVERSE_PERCENT_MODE,
    SOURCE,
    TARGETS,
    build_spec,
)


class RgoPricePolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.game_root = Path(self.temporary.name)
        source = self.game_root / SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "\n\n".join(
                f"{name} = {{\n\tgold = {value}\n}}"
                for name, value in zip(TARGETS, (100, 120, 80, 75, 150), strict=True)
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def values(self, payload: dict[str, object]) -> dict[str, Decimal]:
        return {
            str(rule["object"]): Decimal(str(rule["value"]))
            for rule in payload["transformations"]
        }

    def test_absolute_mode_sets_every_rgo_price_to_60(self) -> None:
        payload = build_spec(
            self.game_root,
            mode=ABSOLUTE_MODE,
            price=Decimal("60"),
            percent=Decimal("40"),
        )

        self.assertEqual(payload["policy"]["mode"], ABSOLUTE_MODE)
        self.assertEqual(
            self.values(payload),
            {name: Decimal("60") for name in TARGETS},
        )
        self.assertIn("absolute target", payload["business_rule"])

    def test_legacy_inverse_percent_mode_is_retained(self) -> None:
        payload = build_spec(
            self.game_root,
            mode=LEGACY_INVERSE_PERCENT_MODE,
            price=Decimal("60"),
            percent=Decimal("40"),
        )

        self.assertEqual(payload["policy"]["mode"], LEGACY_INVERSE_PERCENT_MODE)
        self.assertEqual(
            self.values(payload),
            {
                "expand_rgo_mining": Decimal("71.43"),
                "expand_rgo_farming": Decimal("85.71"),
                "expand_rgo_hunting": Decimal("57.14"),
                "expand_rgo_gathering": Decimal("53.57"),
                "expand_rgo_forestry": Decimal("107.14"),
            },
        )

    def test_absolute_price_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be positive"):
            build_spec(
                self.game_root,
                mode=ABSOLUTE_MODE,
                price=Decimal("0"),
                percent=Decimal("40"),
            )


if __name__ == "__main__":
    unittest.main()

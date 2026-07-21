#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tools.cbg.adapters.cbp.generate_cbp_cbg_fixed_rgo_prices_spec import build_spec as build_fixed_spec
from tools.cbg.adapters.cbp.generate_cbp_cbg_rgo_prices_spec import build_spec as build_offset_spec


REPO_ROOT = Path(__file__).resolve().parents[5]
SOURCE = Path("in_game/common/prices/00_hardcoded.txt")
TARGETS = (
    "expand_rgo_mining",
    "expand_rgo_farming",
    "expand_rgo_hunting",
    "expand_rgo_gathering",
    "expand_rgo_forestry",
)


class RgoPriceAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.game_root = Path(self.temporary.name) / "game"
        source = self.game_root / SOURCE
        source.parent.mkdir(parents=True)
        blocks = [
            f"{name} = {{\n\tgold = 100\n}}"
            for name in TARGETS
        ]
        blocks.append("unrelated_price = {\n\tgold = 999\n}")
        source.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_fixed_adapter_sets_every_target_to_sixty(self) -> None:
        payload = build_fixed_spec(self.game_root, Decimal("60"))

        self.assertEqual("cbp-us09-fixed-rgo-prices", payload["mod_id"])
        self.assertIn("fixed value 60.0", payload["business_rule"])
        self.assertEqual(len(TARGETS), len(payload["transformations"]))
        self.assertEqual(
            {"60.0"},
            {rule["value"] for rule in payload["transformations"]},
        )
        self.assertEqual(
            set(TARGETS),
            {rule["object"] for rule in payload["transformations"]},
        )

    def test_fixed_adapter_accepts_configured_value(self) -> None:
        payload = build_fixed_spec(self.game_root, Decimal("72.5"))
        self.assertEqual(
            {"72.5"},
            {rule["value"] for rule in payload["transformations"]},
        )

    def test_fixed_adapter_rejects_non_positive_price(self) -> None:
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            build_fixed_spec(self.game_root, Decimal("0"))

    def test_previous_percentage_offset_adapter_is_retained(self) -> None:
        payload = build_offset_spec(self.game_root, Decimal("40"))
        self.assertEqual("cbp-us09-rgo-prices", payload["mod_id"])
        self.assertEqual(
            {"71.43"},
            {rule["value"] for rule in payload["transformations"]},
        )

    def run_entrypoint(self, *, adapter: str | None, fixed_price: str) -> dict[str, object]:
        output = Path(self.temporary.name) / f"{adapter or 'environment'}.json"
        command = [
            sys.executable,
            "tools/cbg/adapters/cbp/generate_cbp_cbg_rgo_prices_spec.py",
            "--game-root",
            str(self.game_root),
            "--percent",
            "40",
            "--fixed-price",
            fixed_price,
            "--output",
            str(output),
        ]
        if adapter is not None:
            command.extend(["--adapter", adapter])
        environment = os.environ.copy()
        environment["MODEU5_US09_RGO_PRICE_ADAPTER"] = "fixed"
        environment["MODEU5_US09_RGO_FIXED_PRICE"] = fixed_price
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_environment_selects_fixed_adapter(self) -> None:
        payload = self.run_entrypoint(adapter=None, fixed_price="60")
        self.assertEqual("cbp-us09-fixed-rgo-prices", payload["mod_id"])
        self.assertEqual({"60.0"}, {rule["value"] for rule in payload["transformations"]})

    def test_explicit_offset_selection_keeps_old_adapter_available(self) -> None:
        payload = self.run_entrypoint(adapter="offset", fixed_price="60")
        self.assertEqual("cbp-us09-rgo-prices", payload["mod_id"])
        self.assertEqual({"71.43"}, {rule["value"] for rule in payload["transformations"]})


if __name__ == "__main__":
    unittest.main()

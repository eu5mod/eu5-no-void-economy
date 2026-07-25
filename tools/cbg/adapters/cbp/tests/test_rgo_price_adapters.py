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
from unittest.mock import patch

from tools.cbg.adapters.cbp.generate_cbp_cbg_fixed_rgo_prices_spec import build_spec as build_fixed_spec
from tools.cbg.adapters.cbp.generate_cbp_cbg_rgo_prices_spec import (
    FIXED_ADAPTER,
    OFFSET_ADAPTER,
    OUTPUT,
    build_selected_spec,
    build_spec as build_offset_spec,
)
from tools.cbg.adapters.cbp.generate_cbp_community_balance_spec import rgo_price_transformations
from tools.cbg.community_balance_generator import ASSIGNMENT, field_matches, scan_objects


REPO_ROOT = Path(__file__).resolve().parents[5]
SOURCE = Path("in_game/common/prices/00_hardcoded.txt")
GENERATED = Path(OUTPUT)
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
        self.root = Path(self.temporary.name)
        self.game_root = self.root / "game"
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

    @staticmethod
    def rule_values(payload: dict[str, object]) -> dict[str, Decimal]:
        return {
            str(rule["object"]): Decimal(str(rule["value"]))
            for rule in payload["transformations"]
        }

    @staticmethod
    def materialized_values(path: Path) -> dict[str, Decimal]:
        text = path.read_text(encoding="utf-8-sig").replace("REPLACE:", "")
        lines = text.splitlines(keepends=True)
        objects = {obj.path: obj for obj in scan_objects(lines)}
        values: dict[str, Decimal] = {}
        for name in TARGETS:
            obj = objects.get((name,))
            if obj is None:
                continue
            matches = field_matches(lines, obj, "gold")
            if len(matches) != 1:
                raise AssertionError(f"Expected one generated gold field in {name}")
            match = ASSIGNMENT.match(lines[matches[0]].rstrip("\r\n"))
            if match is None:
                raise AssertionError(f"Generated gold field is not numeric in {name}")
            values[name] = Decimal(match.group("value"))
        return values

    def materialize(self, payload: dict[str, object], label: str) -> Path:
        spec = self.root / f"{label}.json"
        output = self.root / f"{label}-output"
        manifest = output / "manifest.json"
        spec.write_text(json.dumps(payload), encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                "tools/cbg/cbp_community_balance_generator.py",
                "--game-root",
                str(self.game_root),
                "--spec",
                str(spec),
                "--output-root",
                str(output),
                "--manifest",
                str(manifest),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        return output / GENERATED

    def test_fixed_adapter_sets_every_target_to_sixty(self) -> None:
        payload = build_fixed_spec(self.game_root, Decimal("60"))

        self.assertEqual("cbp-us09-fixed-rgo-prices", payload["mod_id"])
        self.assertIn("fixed value 60.0", payload["business_rule"])
        self.assertEqual(len(TARGETS), len(payload["transformations"]))
        self.assertEqual(
            {name: Decimal("60") for name in TARGETS},
            self.rule_values(payload),
        )

    def test_fixed_adapter_accepts_configured_value(self) -> None:
        payload = build_fixed_spec(self.game_root, Decimal("72.5"))
        self.assertEqual(
            {Decimal("72.5")},
            set(self.rule_values(payload).values()),
        )

    def test_fixed_adapter_rejects_non_positive_price(self) -> None:
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            build_fixed_spec(self.game_root, Decimal("0"))

    def test_previous_percentage_offset_adapter_is_retained(self) -> None:
        payload = build_offset_spec(self.game_root, Decimal("40"))
        self.assertEqual("cbp-us09-rgo-prices", payload["mod_id"])
        self.assertEqual(
            {name: Decimal("71.43") for name in TARGETS},
            self.rule_values(payload),
        )

    def test_shared_selector_chooses_exactly_one_adapter(self) -> None:
        fixed = build_selected_spec(
            self.game_root,
            FIXED_ADAPTER,
            Decimal("60"),
            Decimal("40"),
        )
        offset = build_selected_spec(
            self.game_root,
            OFFSET_ADAPTER,
            Decimal("60"),
            Decimal("40"),
        )
        self.assertEqual("cbp-us09-fixed-rgo-prices", fixed["mod_id"])
        self.assertEqual("cbp-us09-rgo-prices", offset["mod_id"])

    def test_fixed_adapter_materializes_configured_values(self) -> None:
        generated = self.materialize(
            build_fixed_spec(self.game_root, Decimal("60")),
            "fixed",
        )
        self.assertEqual(
            {name: Decimal("60") for name in TARGETS},
            self.materialized_values(generated),
        )
        self.assertNotIn("unrelated_price", generated.read_text(encoding="utf-8"))

    def test_offset_adapter_materializes_legacy_values(self) -> None:
        generated = self.materialize(
            build_offset_spec(self.game_root, Decimal("40")),
            "offset",
        )
        self.assertEqual(
            {name: Decimal("71.43") for name in TARGETS},
            self.materialized_values(generated),
        )
        self.assertNotIn("unrelated_price", generated.read_text(encoding="utf-8"))

    def test_master_spec_follows_fixed_adapter_selection(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MODEU5_US09_RGO_PRICE_ADAPTER": FIXED_ADAPTER,
                "MODEU5_US09_RGO_FIXED_PRICE": "72.5",
                "MODEU5_US09_RGO_PRICE_OFFSET_PERCENT": "40",
            },
        ):
            rules = rgo_price_transformations(self.game_root)
        self.assertEqual(
            {name: Decimal("72.5") for name in TARGETS},
            {
                str(rule["object"]): Decimal(str(rule["value"]))
                for rule in rules
            },
        )

    def test_master_spec_follows_offset_adapter_selection(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MODEU5_US09_RGO_PRICE_ADAPTER": OFFSET_ADAPTER,
                "MODEU5_US09_RGO_FIXED_PRICE": "60",
                "MODEU5_US09_RGO_PRICE_OFFSET_PERCENT": "40",
            },
        ):
            rules = rgo_price_transformations(self.game_root)
        self.assertEqual(
            {name: Decimal("71.43") for name in TARGETS},
            {
                str(rule["object"]): Decimal(str(rule["value"]))
                for rule in rules
            },
        )

    def run_entrypoint(self, *, adapter: str | None, fixed_price: str) -> dict[str, object]:
        output = self.root / f"{adapter or 'environment'}.json"
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
        environment["MODEU5_US09_RGO_PRICE_ADAPTER"] = FIXED_ADAPTER
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
        self.assertEqual(
            {name: Decimal("60") for name in TARGETS},
            self.rule_values(payload),
        )

    def test_explicit_offset_selection_keeps_old_adapter_available(self) -> None:
        payload = self.run_entrypoint(adapter=OFFSET_ADAPTER, fixed_price="60")
        self.assertEqual("cbp-us09-rgo-prices", payload["mod_id"])
        self.assertEqual(
            {name: Decimal("71.43") for name in TARGETS},
            self.rule_values(payload),
        )


if __name__ == "__main__":
    unittest.main()

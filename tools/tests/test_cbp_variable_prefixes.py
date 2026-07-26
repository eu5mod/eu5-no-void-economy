#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import cbp_variable_prefixes


class CbpVariablePrefixesTests(unittest.TestCase):
    def test_manifest_owned_cbg_outputs_are_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "packages/cbp_economy_rebalance"
            generated = package / "in_game/common/advances/cbp_country_test.txt"
            generated.parent.mkdir(parents=True)
            generated.write_text(
                "test = {\n\tset_variable = vanilla_owned_variable\n}\n",
                encoding="utf-8",
            )
            authored = package / "in_game/common/scripted_effects/cbp_test.txt"
            authored.parent.mkdir(parents=True)
            authored.write_text(
                "test = {\n\tset_variable = cbp_owned_variable\n}\n",
                encoding="utf-8",
            )
            vanilla_carrier = (
                package / "in_game/events/DHE/flavor_test.txt"
            )
            vanilla_carrier.parent.mkdir(parents=True)
            vanilla_carrier.write_text(
                "test.1 = {\n\tset_variable = vanilla_event_variable\n}\n",
                encoding="utf-8",
            )
            manifest = package / "cbp_generated/cbg_test_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps(
                    {
                        "files": [
                            {
                                "path": (
                                    "in_game/common/advances/"
                                    "cbp_country_test.txt"
                                )
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            roots = (
                root / "in_game",
                root / "main_menu",
                root / "packages",
                root / "tools/templates",
            )
            with (
                mock.patch.object(cbp_variable_prefixes, "ROOT", root),
                mock.patch.object(cbp_variable_prefixes, "EU5_ROOTS", roots),
            ):
                files = cbp_variable_prefixes.iter_eu5_files()

        self.assertIn(authored, files)
        self.assertNotIn(generated, files)
        self.assertNotIn(vanilla_carrier, files)


if __name__ == "__main__":
    unittest.main()

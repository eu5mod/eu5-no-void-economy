#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
BOOTSTRAP = ROOT / "tools/cbg/adapters/cbp/helpers/bootstrap_cbg_manifest_from_git.py"


class CbpManifestBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.output = self.repo / "package/in_game/common/example.txt"
        self.output.parent.mkdir(parents=True)
        self.output.write_text("tracked generated output\n")
        self.spec = self.repo / "spec.json"
        self.spec.write_text(json.dumps({"transformations": [{
            "file": "in_game/common/example.txt",
            "object": "example",
            "field": "value",
            "operation": "replace",
            "value": 1,
        }]}))
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=CBG Test", "-c", "user.email=cbg@example.invalid", "commit", "-qm", "fixture"],
            cwd=self.repo,
            check=True,
        )
        self.manifest = self.repo / "manifest.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_bootstrap(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3", str(BOOTSTRAP),
                "--spec", str(self.spec),
                "--output-root", str(self.repo / "package"),
                "--manifest", str(self.manifest),
            ],
            cwd=self.repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def test_bootstraps_clean_tracked_output(self) -> None:
        result = self.run_bootstrap()
        self.assertEqual(0, result.returncode, result.stdout)
        payload = json.loads(self.manifest.read_text())
        self.assertEqual("community_balance_generator", payload["generator"])
        self.assertEqual("in_game/common/example.txt", payload["files"][0]["path"])

    def test_refuses_locally_modified_output(self) -> None:
        self.output.write_text("locally modified\n")
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("locally modified output", result.stdout)


if __name__ == "__main__":
    unittest.main()

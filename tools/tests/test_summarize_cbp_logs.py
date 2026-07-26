#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARIZER = ROOT / "tools/summarize_cbp_logs.sh"


class SummarizeCbpLogsTests(unittest.TestCase):
    def summarize(self, lines: list[str]) -> str:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary)
            (logs / "debug.log").write_text("\n".join(lines) + "\n")
            result = subprocess.run(
                [
                    str(SUMMARIZER),
                    "--logs-dir",
                    str(logs),
                    "--expected",
                    "none",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stdout)
        return result.stdout

    def test_completed_summary_closes_main_wrapper(self) -> None:
        output = self.summarize(
            [
                "ModeU5 TEST ENTERED scenario=main_revalidation",
                "ModeU5 TEST ENTERED scenario=main_revalidation_summary",
                "ModeU5 TEST PASS scenario=main_revalidation_summary",
            ]
        )

        self.assertIn("Incomplete latest scenario runs: 0", output)
        self.assertNotIn(
            "Incomplete latest scenario runs:\n"
            "ModeU5 TEST ENTERED scenario=main_revalidation",
            output,
        )

    def test_real_unfinished_scenario_remains_visible(self) -> None:
        output = self.summarize(
            [
                "ModeU5 TEST ENTERED scenario=main_revalidation",
                "ModeU5 TEST ENTERED scenario=main_revalidation_summary",
                "ModeU5 TEST PASS scenario=main_revalidation_summary",
                "ModeU5 TEST ENTERED scenario=us04_estate_level_accounting",
            ]
        )

        self.assertIn("Incomplete latest scenario runs: 1", output)
        self.assertIn(
            "ModeU5 TEST ENTERED scenario=us04_estate_level_accounting",
            output,
        )


if __name__ == "__main__":
    unittest.main()

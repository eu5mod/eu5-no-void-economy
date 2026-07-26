#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL_LIB = ROOT / "tools/cbp_tool_lib.sh"
GENERATE_ALL = ROOT / "tools/generate_all.sh"
DEV_PREPARE = ROOT / "tools/dev_prepare_game.sh"


class ConsoleProtocolTests(unittest.TestCase):
    def run_bash(self, script: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "-c", script],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def test_task_reports_start_success_and_status_record(self) -> None:
        with tempfile.NamedTemporaryFile() as status:
            result = self.run_bash(
                f"""
                export CBG_COLOR=never
                export CBP_CONSOLE_STATUS_FILE={status.name!r}
                source {str(TOOL_LIB)!r}
                cbp_console_run_task 3.1 'Example validator' quiet \
                    sh -c 'printf "validator passed\\n"'
                """
            )
            record = Path(status.name).read_text()

        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("[3.1] START Example validator", result.stdout)
        self.assertIn("[3.1] END ✅ Example validator", result.stdout)
        self.assertNotIn("validator passed", result.stdout)
        self.assertEqual("3.1\tOK\tExample validator\t\n", record)

    def test_warning_is_visible_and_recorded(self) -> None:
        with tempfile.NamedTemporaryFile() as status:
            result = self.run_bash(
                f"""
                export CBG_COLOR=never
                export CBP_CONSOLE_STATUS_FILE={status.name!r}
                source {str(TOOL_LIB)!r}
                cbp_console_run_task 3.2 'Warning validator' quiet \
                    sh -c 'printf "WARNING: review this\\n"'
                """
            )
            record = Path(status.name).read_text()

        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("WARNING: review this", result.stdout)
        self.assertIn("[3.2] END ⚠️ Warning validator", result.stdout)
        self.assertEqual(
            "3.2\tWARNING\tWarning validator\t1 warning(s)\n",
            record,
        )

    def test_failure_keeps_full_diagnostics_and_exit_status(self) -> None:
        with tempfile.NamedTemporaryFile() as status:
            result = self.run_bash(
                f"""
                export CBG_COLOR=never
                export CBP_CONSOLE_STATUS_FILE={status.name!r}
                source {str(TOOL_LIB)!r}
                if cbp_console_run_task 3.3 'Failing validator' quiet \
                    sh -c 'printf "specific failure\\n"; exit 7'
                then
                    exit 99
                else
                    exit $?
                fi
                """
            )
            record = Path(status.name).read_text()

        self.assertEqual(7, result.returncode, result.stdout)
        self.assertIn("[3.3] END ❌ Failing validator", result.stdout)
        self.assertIn("Full diagnostic output for 3.3", result.stdout)
        self.assertIn("specific failure", result.stdout)
        self.assertEqual(
            "3.3\tFAILED\tFailing validator\texit 7\n",
            record,
        )

    def test_compact_output_hides_json_metadata_chatter(self) -> None:
        result = self.run_bash(
            f"""
            source {str(TOOL_LIB)!r}
            printf '%s\\n' \
                'Generated ./generated/spec.json with policy.' \
                'Reconciled ./generated/manifest.json with 2 owned output(s).' \
                'Applied mutations 42' |
                cbp_console_filter_stream compact
            """
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assertEqual("Applied mutations 42\n", result.stdout)

    def test_canonical_scripts_expose_hierarchical_substeps(self) -> None:
        generation = GENERATE_ALL.read_text()
        preparation = DEV_PREPARE.read_text()

        generation_titles = [
            line
            for line in generation.splitlines()
            if line.startswith("generation_substep_start '")
        ]
        self.assertEqual(6, len(generation_titles))
        self.assertEqual(7, generation.count("run_generation_cbg python3"))
        for substep in range(1, 13):
            self.assertIn(f"'3.{substep}'", preparation)
        self.assertIn("PREPARATION SUMMARY", preparation)

    def test_major_step_uses_a_centered_hash_banner(self) -> None:
        result = self.run_bash(
            f"""
            export CBG_COLOR=never
            source {str(TOOL_LIB)!r}
            cbp_console_section_start 2/7 'Verify generation idempotence'
            """
        )

        self.assertEqual(0, result.returncode, result.stdout)
        lines = [line for line in result.stdout.splitlines() if line]
        self.assertEqual("#" * 73, lines[0])
        self.assertIn("STEP 2/7  Verify generation idempotence", lines[1])
        self.assertEqual("#" * 73, lines[2])

    def test_major_step_keeps_a_distinct_status_closure(self) -> None:
        result = self.run_bash(
            f"""
            export CBG_COLOR=never
            source {str(TOOL_LIB)!r}
            cbp_console_section_end 1/7 OK 'Generate all runtime and package artifacts'
            """
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assertEqual(
            "└─ [STEP 1/7] [OK] Generate all runtime and package artifacts\n",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()

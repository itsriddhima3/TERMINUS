from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import run_static_checks
from repo_tests.cases import COMMON_STATIC_PASS_MESSAGES, FIXTURE_TASKS_DIR, STATIC_CHECK_EXPECTATIONS

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "run_static_checks"


class RunStaticChecksRegressionTest(unittest.TestCase):
    """Pin repo-level static checker results for the checked-in benchmark fixtures."""

    def copy_fixture(self, fixture_name: str, tmpdir: str) -> Path:
        fixture_dir = FIXTURES_DIR / fixture_name
        task_dir = Path(tmpdir) / fixture_name
        shutil.copytree(fixture_dir, task_dir)
        return task_dir

    def test_fixture_tasks_keep_pinned_static_check_results(self) -> None:
        for task_name, expected in STATIC_CHECK_EXPECTATIONS.items():
            with self.subTest(task=task_name):
                reporter = run_static_checks.run_checks(FIXTURE_TASKS_DIR / task_name)
                self.assertEqual(reporter.failures, [])
                self.assertEqual(reporter.warnings, expected["warnings"])
                for message in COMMON_STATIC_PASS_MESSAGES:
                    self.assertIn(message, reporter.passes)

    def test_cli_exit_code_stays_successful_for_fixture_tasks(self) -> None:
        for task_name in STATIC_CHECK_EXPECTATIONS:
            with self.subTest(task=task_name):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = run_static_checks.main(
                        ["--task-dir", str(FIXTURE_TASKS_DIR / task_name), "--version", "edition_2"]
                    )
                self.assertEqual(exit_code, 0)
                self.assertIn("PASS", stdout.getvalue())

    def test_reward_json_footer_is_rejected(self) -> None:
        fixture = FIXTURE_TASKS_DIR / "implicit-step-restart"
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / fixture.name
            shutil.copytree(fixture, task_dir)

            test_sh = task_dir / "tests" / "test.sh"
            content = test_sh.read_text(encoding="utf-8")
            test_sh.write_text(
                content.replace("/logs/verifier/reward.txt", "/logs/verifier/reward.json"),
                encoding="utf-8",
            )

            reporter = run_static_checks.run_checks(task_dir)

        self.assertIn(
            "tests/test.sh must emit /logs/verifier/reward.txt; reward.json is not supported by the Edition 2 template",
            reporter.failures,
        )

    def test_internal_harness_path_leak_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = self.copy_fixture("public-contract-standard", tmpdir)
            instruction_path = task_dir / "instruction.md"
            instruction_path.write_text(
                instruction_path.read_text(encoding="utf-8")
                + "\nDo not touch `/app/.state/private-cache.bin` while preparing the output.\n",
                encoding="utf-8",
            )

            reporter = run_static_checks.run_checks(task_dir, {"output_contract"})

        self.assertIn(
            "instruction.md must not mention internal_harness_files unless they are also declared in user_visible_outputs: /app/.state/private-cache.bin",
            reporter.failures,
        )

    def test_internal_harness_path_is_allowed_when_it_is_also_user_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = self.copy_fixture("public-contract-standard", tmpdir)
            contract_path = task_dir / "output_contract.toml"
            contract_path.write_text(
                contract_path.read_text(encoding="utf-8").replace(
                    'internal_harness_files = [\n  "/app/.state/private-cache.bin",\n]',
                    'internal_harness_files = [\n  "/app/out/report.json",\n]',
                ),
                encoding="utf-8",
            )

            reporter = run_static_checks.run_checks(task_dir, {"output_contract"})

        self.assertEqual(reporter.failures, [])
        self.assertIn("output contract matches the declared user-visible outputs and schema checks", reporter.passes)

    def test_milestone_instruction_requires_signal_completion_directive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = self.copy_fixture("public-contract-milestone", tmpdir)
            instruction_path = task_dir / "instruction.md"
            instruction_path.write_text(
                "For the current milestone, write `/app/out/report.json` as JSON with `checksum` and `status` fields.\n",
                encoding="utf-8",
            )

            reporter = run_static_checks.run_checks(task_dir, {"instruction"})

        self.assertIn(
            "Milestone tasks must tell the agent to signal completion before advancing to the next milestone",
            reporter.failures,
        )

    def test_milestone_instruction_passes_with_signal_completion_directive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = self.copy_fixture("public-contract-milestone", tmpdir)

            reporter = run_static_checks.run_checks(task_dir, {"instruction"})

        self.assertEqual(reporter.failures, [])

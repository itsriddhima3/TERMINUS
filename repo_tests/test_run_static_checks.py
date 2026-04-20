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

    def test_oracle_knob_discoverability_warns_when_flag_is_invisible(self) -> None:
        """A knob referenced by solve.sh but absent from instruction.md
        AND absent from every comment/doc under environment/ must warn.

        Reproduces the rollback-replay-divergence failure mode: the oracle
        flips two CMake cache variables the agent cannot discover, so agents
        rewrite the source and lose the conditional-compilation ladder the
        grader depends on."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = FIXTURE_TASKS_DIR / "rollback-replay-divergence"
            task_dir = Path(tmpdir) / "rollback-replay-divergence"
            shutil.copytree(source, task_dir)

            instruction = task_dir / "instruction.md"
            instruction.write_text(
                instruction.read_text(encoding="utf-8")
                .replace("`TB_TIMELINE_MODE`", "the timeline knob")
                .replace("`TB_REEXEC_MODE`", "the re-exec knob"),
                encoding="utf-8",
            )
            cmake = task_dir / "environment" / "CMakeLists.txt"
            lines = cmake.read_text(encoding="utf-8").splitlines(keepends=True)
            cmake.write_text(
                "".join(
                    line for line in lines
                    if not line.lstrip().startswith("#")
                ),
                encoding="utf-8",
            )

            reporter = run_static_checks.run_checks(
                task_dir, {"oracle_knob_discoverability"}
            )

        warnings = [w for w in reporter.warnings if "build knobs" in w]
        self.assertEqual(len(warnings), 1, reporter.warnings)
        self.assertIn("TB_TIMELINE_MODE", warnings[0])
        self.assertIn("TB_REEXEC_MODE", warnings[0])

    def test_oracle_knob_discoverability_passes_when_flag_is_named_in_instruction(self) -> None:
        """Mentioning the knob in instruction.md alone clears the check even if
        the environment/ sources have no comment for it."""
        reporter = run_static_checks.run_checks(
            FIXTURE_TASKS_DIR / "rollback-replay-divergence",
            {"oracle_knob_discoverability"},
        )
        self.assertEqual(reporter.failures, [])
        self.assertIn(
            "build knobs required by solve.sh and tests are discoverable from instruction.md or environment/",
            reporter.passes,
        )

    def test_oracle_knob_discoverability_ignores_standard_cmake_knobs(self) -> None:
        """Standard CMake / compiler knobs (CMAKE_BUILD_TYPE, CC, CFLAGS, ...)
        must never trigger the check, even if they never appear in
        instruction.md. Tasks that only use standard knobs report a clean
        'no bespoke build knobs required' pass."""
        reporter = run_static_checks.run_checks(
            FIXTURE_TASKS_DIR / "byzantine-storage-rebalance",
            {"oracle_knob_discoverability"},
        )
        self.assertEqual(reporter.failures, [])
        self.assertEqual([], [w for w in reporter.warnings if "build knobs" in w])

    def test_oracle_path_discoverability_warns_when_install_path_is_invisible(self) -> None:
        """Reproduces the rollback-replay-divergence v4 failure mode: agents
        built the binary, ran it, produced the correct SIGNOFF digests, and
        still failed every test because nothing told them to install the
        binary at /app/bin/netplay_matrix. The check must catch this by
        warning that the test-required path is undocumented."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = FIXTURE_TASKS_DIR / "rollback-replay-divergence"
            task_dir = Path(tmpdir) / "rollback-replay-divergence"
            shutil.copytree(source, task_dir)

            instruction = task_dir / "instruction.md"
            instruction.write_text(
                instruction.read_text(encoding="utf-8")
                .replace("install it at `/app/bin/netplay_matrix`", "install the binary")
                .replace("`/app/bin/netplay_matrix`", "the binary"),
                encoding="utf-8",
            )

            reporter = run_static_checks.run_checks(
                task_dir, {"oracle_path_discoverability"}
            )

        warnings = [w for w in reporter.warnings if "agent must create" in w]
        self.assertEqual(len(warnings), 1, reporter.warnings)
        self.assertIn("/app/bin/netplay_matrix", warnings[0])

    def test_oracle_path_discoverability_passes_when_path_is_named_in_instruction(self) -> None:
        """Positive case on the patched fixture: every absolute /app path the
        tests resolve is either in the shipped tree, under a standard build-
        output prefix, or named in instruction.md / environment/."""
        reporter = run_static_checks.run_checks(
            FIXTURE_TASKS_DIR / "rollback-replay-divergence",
            {"oracle_path_discoverability"},
        )
        self.assertEqual(reporter.failures, [])
        self.assertIn(
            "agent-target paths declared in tests/ are discoverable from instruction.md or environment/",
            reporter.passes,
        )

    def test_oracle_path_discoverability_accepts_string_literals_in_source(self) -> None:
        """Paths mentioned only as quoted string literals in source files
        (e.g. ``const DefaultPath = \"/app/config/foo.yaml\"`` in Go,
        ``std::string work_dir = \"/app/work\"`` in C++) are discoverable —
        the agent can grep for them. This distinguishes paths from build
        knobs, where bare-code references don't count.

        Specifically: byzantine-storage-rebalance documents
        /app/config/sim_defaults.yaml only via a Go string-literal
        constant; the check must not warn on it."""
        reporter = run_static_checks.run_checks(
            FIXTURE_TASKS_DIR / "byzantine-storage-rebalance",
            {"oracle_path_discoverability"},
        )
        self.assertEqual(reporter.failures, [])
        self.assertEqual([], [w for w in reporter.warnings if "agent must create" in w])

    def test_oracle_path_discoverability_skips_standard_build_output_dirs(self) -> None:
        """Paths under /app/build/ (cmake), /app/target/ (cargo), /app/dist/
        and similar standard build-tool output directories are managed by
        the agent's toolchain and don't need to be documented in
        instruction.md."""
        reporter = run_static_checks.run_checks(
            FIXTURE_TASKS_DIR / "release-provenance-drift",
            {"oracle_path_discoverability"},
        )
        self.assertEqual(reporter.failures, [])
        warnings_with_build_dirs = [
            w for w in reporter.warnings
            if "/app/build/" in w or "/app/target/" in w
        ]
        self.assertEqual(warnings_with_build_dirs, [])

    def test_instruction_test_vocabulary_catches_extended_assertion_shapes(self) -> None:
        """The vocabulary check must catch all four assertion shapes:
        ``X == LITERAL``, ``X.startswith(LITERAL)``, ``LITERAL in X``,
        and ``len(X) == NUMBER`` — for any X reading an instruction-named
        field. Reproduces the release-provenance-drift gap where
        ``len(snapshot["epoch"]) == 24`` was tested but never documented."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "vocab_test"
            task_dir.mkdir()
            (task_dir / "instruction.md").write_text(
                "Output a `result` field. The status field is also part of the contract.\n"
            )
            tests = task_dir / "tests"
            tests.mkdir()
            (tests / "test_outputs.py").write_text(
                "def test_a():\n"
                "    obj = {}\n"
                "    assert obj['result'] == 'undocumented_value'\n"
                "    assert obj['result'].startswith('undocumented_prefix')\n"
                "    assert obj['result'].endswith('undocumented_suffix')\n"
                "    assert 'undocumented_substring' in obj['result']\n"
                "    assert len(obj['result']) == 42\n"
            )

            named_fields = run_static_checks._instruction_named_fields(
                (task_dir / "instruction.md").read_text(encoding="utf-8")
            )
            findings = run_static_checks._literal_assertions_on_named_fields(
                tests / "test_outputs.py", named_fields
            )

        literals_found = {literal for _, _, literal in findings}
        self.assertIn("undocumented_value", literals_found)         # ==
        self.assertIn("undocumented_prefix", literals_found)        # startswith
        self.assertIn("undocumented_suffix", literals_found)        # endswith
        self.assertIn("undocumented_substring", literals_found)     # in
        self.assertIn("42", literals_found)                         # len ==

    def test_instruction_test_vocabulary_passes_when_extended_literals_are_documented(self) -> None:
        """Counterpart to the negative test: when each literal IS named in
        instruction.md, no warning fires across all four assertion shapes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "vocab_pass"
            task_dir.mkdir()
            (task_dir / "instruction.md").write_text(
                "The `result` field equals 'documented_value', begins with "
                "'documented_prefix', ends with 'documented_suffix', contains "
                "the substring 'documented_substring', and has length 42.\n"
            )
            tests = task_dir / "tests"
            tests.mkdir()
            (tests / "test_outputs.py").write_text(
                "def test_a():\n"
                "    obj = {}\n"
                "    assert obj['result'] == 'documented_value'\n"
                "    assert obj['result'].startswith('documented_prefix')\n"
                "    assert obj['result'].endswith('documented_suffix')\n"
                "    assert 'documented_substring' in obj['result']\n"
                "    assert len(obj['result']) == 42\n"
            )

            named_fields = run_static_checks._instruction_named_fields(
                (task_dir / "instruction.md").read_text(encoding="utf-8")
            )
            findings = run_static_checks._literal_assertions_on_named_fields(
                tests / "test_outputs.py", named_fields
            )
            instruction_text = (task_dir / "instruction.md").read_text(encoding="utf-8")
            undocumented = [
                (field, literal) for _, field, literal in findings
                if literal not in instruction_text
            ]

        self.assertEqual(undocumented, [])

    def test_timeout_coherence_warns_when_subprocess_timeouts_exceed_verifier(self) -> None:
        """Reproduces the implicit-step-restart v6 failure mode: tests/
        declare explicit ``subprocess.run(..., timeout=N)`` ceilings on
        each cmake step (180+180+60+120+120+30 = 690s), but the verifier
        budget was 600s. The check must sum those literals and warn when
        the sum exceeds verifier.timeout_sec — that's the real wall-time
        ceiling, not the build-site count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "tsum"
            task_dir.mkdir()
            (task_dir / "task.toml").write_text(
                'version = "2.0"\n'
                "[metadata]\n"
                'author_name = "anonymous"\n'
                'author_email = "anonymous"\n'
                'difficulty = "hard"\n'
                'category = "debugging"\n'
                'tags = []\n'
                'languages = ["c++"]\n'
                'codebase_size = "small"\n'
                "number_of_milestones = 0\n"
                "subcategories = []\n"
                "expert_time_estimate_min = 60\n"
                "junior_time_estimate_min = 240\n"
                "[agent]\n"
                "timeout_sec = 1800\n"
                "[verifier]\n"
                "timeout_sec = 600\n"
                "[environment]\n"
                "build_timeout_sec = 600\n"
                "cpus = 2\n"
                "memory_mb = 4096\n"
                "storage_mb = 10240\n"
            )
            tests = task_dir / "tests"
            tests.mkdir()
            # Tests with explicit per-call timeouts summing > verifier
            (tests / "test_outputs.py").write_text(
                "import subprocess\n"
                "def test_x():\n"
                "    subprocess.run(['cmake', '-S', '.', '-B', 'build'], timeout=180)\n"
                "    subprocess.run(['cmake', '--build', 'build'], timeout=180)\n"
                "    subprocess.run(['./bin'], timeout=60)\n"
                "    subprocess.run(['cmake', '-S', 'p', '-B', 'pb'], timeout=120)\n"
                "    subprocess.run(['cmake', '--build', 'pb'], timeout=120)\n"
                "    subprocess.run(['./pb/probe'], timeout=30)\n"
            )

            reporter = run_static_checks.run_checks(task_dir, {"timeout_coherence"})

        sum_warnings = [w for w in reporter.warnings if "exceeds verifier" in w]
        self.assertEqual(len(sum_warnings), 1, reporter.warnings)
        self.assertIn("690s", sum_warnings[0])
        self.assertIn("600s", sum_warnings[0])

    def test_timeout_coherence_passes_when_subprocess_timeout_sum_fits_verifier(self) -> None:
        """Counterpart positive: same six subprocesses, verifier raised to
        900s, the sum (690s) fits under it, and the new rule stays silent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "tfit"
            task_dir.mkdir()
            (task_dir / "task.toml").write_text(
                'version = "2.0"\n'
                "[metadata]\n"
                'author_name = "anonymous"\n'
                'author_email = "anonymous"\n'
                'difficulty = "hard"\n'
                'category = "debugging"\n'
                'tags = []\n'
                'languages = ["c++"]\n'
                'codebase_size = "small"\n'
                "number_of_milestones = 0\n"
                "subcategories = []\n"
                "expert_time_estimate_min = 60\n"
                "junior_time_estimate_min = 240\n"
                "[agent]\n"
                "timeout_sec = 1800\n"
                "[verifier]\n"
                "timeout_sec = 900\n"
                "[environment]\n"
                "build_timeout_sec = 600\n"
                "cpus = 2\n"
                "memory_mb = 4096\n"
                "storage_mb = 10240\n"
            )
            tests = task_dir / "tests"
            tests.mkdir()
            (tests / "test_outputs.py").write_text(
                "import subprocess\n"
                "def test_x():\n"
                "    subprocess.run(['cmake', '-S', '.', '-B', 'build'], timeout=180)\n"
                "    subprocess.run(['cmake', '--build', 'build'], timeout=180)\n"
                "    subprocess.run(['./bin'], timeout=60)\n"
                "    subprocess.run(['cmake', '-S', 'p', '-B', 'pb'], timeout=120)\n"
                "    subprocess.run(['cmake', '--build', 'pb'], timeout=120)\n"
                "    subprocess.run(['./pb/probe'], timeout=30)\n"
            )

            reporter = run_static_checks.run_checks(task_dir, {"timeout_coherence"})

        sum_warnings = [w for w in reporter.warnings if "exceeds verifier" in w]
        self.assertEqual(sum_warnings, [])

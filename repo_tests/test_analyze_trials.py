from __future__ import annotations

import contextlib
import io
import json
import unittest

import analyze_trials
from repo_tests.cases import ANALYZE_TRIALS_EXPECTATION, ANALYZE_TRIALS_JOB_DIR


class AnalyzeTrialsRegressionTest(unittest.TestCase):
    """Pin analyzer behavior against archived Harbor evidence in jobs/."""

    def test_archived_job_summary_stays_pinned(self) -> None:
        payload = analyze_trials.analyze_job_dir(ANALYZE_TRIALS_JOB_DIR)
        for key in (
            "task_name",
            "agent_name",
            "model_id",
            "model_label",
            "requested_trials",
            "found_trial_dirs",
            "verifier_backed_trials",
            "infra_error_count",
            "full_suite_passes",
            "zero_pass_tests",
            "artifact_issues",
        ):
            self.assertEqual(payload[key], ANALYZE_TRIALS_EXPECTATION[key])

        self.assertAlmostEqual(payload["mean_reward"], ANALYZE_TRIALS_EXPECTATION["mean_reward"])
        self.assertAlmostEqual(
            payload["full_suite_pass_rate"],
            ANALYZE_TRIALS_EXPECTATION["full_suite_pass_rate"],
        )

        tests_by_name = {entry["name"]: entry for entry in payload["tests"]}
        for test_name, passes in ANALYZE_TRIALS_EXPECTATION["test_pass_counts"].items():
            self.assertEqual(tests_by_name[test_name]["passes"], passes)

        trials_by_name = {entry["trial"]: entry for entry in payload["trials"]}
        for trial_name, reward in ANALYZE_TRIALS_EXPECTATION["trial_rewards"].items():
            self.assertEqual(trials_by_name[trial_name]["reward"], reward)
        for trial_name, statuses in ANALYZE_TRIALS_EXPECTATION["pinned_statuses"].items():
            for test_name, status in statuses.items():
                self.assertEqual(trials_by_name[trial_name]["test_statuses"][test_name], status)

    def test_cli_json_output_matches_programmatic_payload(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = analyze_trials.main([str(ANALYZE_TRIALS_JOB_DIR), "--json"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertAlmostEqual(payload["mean_reward"], ANALYZE_TRIALS_EXPECTATION["mean_reward"])

    def test_text_report_mentions_pinned_summary_lines(self) -> None:
        report = analyze_trials.format_analysis_report(
            analyze_trials.analyze_job_dir(ANALYZE_TRIALS_JOB_DIR)
        )
        self.assertIn("Mean reward: 0.4", report)
        self.assertIn("Full-suite pass rate: 2/5 (40.0%)", report)
        self.assertIn("No individual test at 0/5.", report)
        self.assertIn("test_outputs.py::test_generated_scenarios_match_contract", report)

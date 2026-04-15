from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import approve_task
import run_static_checks
from repo_tests.cases import FIXTURE_TASKS_DIR


REPO_ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_DIR = REPO_ROOT / "Task_Ready_To_Submit"
JOB_DIR = REPO_ROOT / "jobs" / "2026-04-14__23-18-35"


def build_clean_reporter() -> run_static_checks.Reporter:
    reporter = run_static_checks.Reporter()
    reporter.ok("fixture static checks passed")
    return reporter


def build_clean_collapse_report() -> dict[str, object]:
    return {
        "oracle_targets": ["src/main.cc"],
        "oracle_loc_non_boilerplate": 42,
        "touched_roots": ["src"],
        "frontier_concentration": {
            "dominant_root": "src",
            "dominant_root_share": 0.5,
            "root_counts": {"src": 1},
        },
        "results": [],
        "fails": 0,
        "warns": 0,
    }


def write_zip_from_source(task_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(task_dir.rglob("*")):
            if not path.is_file():
                continue
            rel_path = Path(path.relative_to(task_dir).as_posix())
            if approve_task.should_skip_packaged_path(rel_path):
                continue
            archive.write(path, arcname=rel_path.as_posix())


def write_synthetic_job(job_dir: Path, task_name: str, task_path: Path) -> None:
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "config.json").write_text(
        json.dumps(
            {
                "job_name": job_dir.name,
                "n_attempts": 5,
                "agents": [{"name": "terminus-2", "model_name": approve_task.DEFAULT_HARD_MODEL}],
                "tasks": [{"path": str(task_path)}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (job_dir / "result.json").write_text(
        json.dumps({"n_total_trials": 5}, indent=2),
        encoding="utf-8",
    )

    statuses = [
        {"test_outputs.py::test_alpha": "passed", "test_outputs.py::test_beta": "failed"},
        {"test_outputs.py::test_alpha": "failed", "test_outputs.py::test_beta": "passed"},
        {"test_outputs.py::test_alpha": "passed", "test_outputs.py::test_beta": "passed"},
        {"test_outputs.py::test_alpha": "passed", "test_outputs.py::test_beta": "failed"},
        {"test_outputs.py::test_alpha": "failed", "test_outputs.py::test_beta": "passed"},
    ]

    for index, test_statuses in enumerate(statuses, start=1):
        trial_name = f"{task_name}__TRIAL{index}"
        trial_dir = job_dir / trial_name / "verifier"
        trial_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / trial_name / "result.json").write_text(
            json.dumps(
                {
                    "trial_name": trial_name,
                    "task_name": task_name,
                    "agent_info": {
                        "name": "terminus-2",
                        "model_info": {"provider": "anthropic", "name": "claude-opus-4-6"},
                    },
                    "config": {"agent": {"model_name": approve_task.DEFAULT_HARD_MODEL}},
                    "verifier_result": {"rewards": {"reward": 0.0}},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (trial_dir / "ctrf.json").write_text(
            json.dumps(
                {
                    "results": {
                        "tests": [
                            {"name": name, "status": status}
                            for name, status in test_statuses.items()
                        ]
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def write_verifier_health_report(
    path: Path,
    task_dir: Path,
    *,
    healthy: bool = True,
    blocking_failures: list[str] | None = None,
) -> None:
    payload = {
        "task_dir": str(task_dir.resolve()),
        "healthy": healthy,
        "decision": "PASS" if healthy else "FAIL",
        "blocking_failures": blocking_failures or [],
        "warnings": [],
        "checks": {
            "repeat_oracle": {"name": "repeat_oracle", "status": "PASS", "blocking_failures": [], "warnings": []},
            "randomized_order": {"name": "randomized_order", "status": "PASS", "blocking_failures": [], "warnings": []},
            "partial_oracle": {"name": "partial_oracle", "status": "PASS", "blocking_failures": [], "warnings": []},
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class ApproveTaskRegressionTest(unittest.TestCase):
    def test_archived_medium_job_fails_hard_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier_health_path = Path(tmpdir) / "verifier-health.json"
            write_verifier_health_report(
                verifier_health_path,
                FIXTURE_TASKS_DIR / "lsm-snapshot-recovery",
            )
            payload = approve_task.build_report(
                FIXTURE_TASKS_DIR / "lsm-snapshot-recovery",
                SUBMISSION_DIR / "lsm-snapshot-recovery.zip",
                JOB_DIR,
                verifier_health_path=verifier_health_path,
            )
        self.assertFalse(payload["approved"])
        self.assertIn(
            "default hard gate requires 0 full-suite passes, found 2",
            payload["blocking_failures"],
        )

    def test_synthetic_clean_fixture_passes_gate(self) -> None:
        fixture = FIXTURE_TASKS_DIR / "implicit-step-restart"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            task_dir = tmp_root / fixture.name
            shutil.copytree(fixture, task_dir)
            zip_path = tmp_root / f"{fixture.name}.zip"
            write_zip_from_source(task_dir, zip_path)
            job_dir = tmp_root / "jobs" / "2026-04-15__approve-pass"
            write_synthetic_job(job_dir, fixture.name, task_dir)
            verifier_health_path = tmp_root / "verifier-health.json"
            write_verifier_health_report(verifier_health_path, task_dir)

            with mock.patch.object(approve_task.run_static_checks, "run_checks", return_value=build_clean_reporter()), mock.patch.object(
                approve_task.collapse_check,
                "build_report",
                return_value=build_clean_collapse_report(),
            ):
                payload = approve_task.build_report(
                    task_dir,
                    zip_path,
                    job_dir,
                    verifier_health_path=verifier_health_path,
                )

        self.assertTrue(payload["approved"], payload["blocking_failures"])

    def test_zip_source_mismatch_blocks_approval(self) -> None:
        fixture = FIXTURE_TASKS_DIR / "implicit-step-restart"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            task_dir = tmp_root / fixture.name
            shutil.copytree(fixture, task_dir)
            zip_path = tmp_root / f"{fixture.name}.zip"
            write_zip_from_source(task_dir, zip_path)
            job_dir = tmp_root / "jobs" / "2026-04-15__approve-mismatch"
            write_synthetic_job(job_dir, fixture.name, task_dir)
            verifier_health_path = tmp_root / "verifier-health.json"
            write_verifier_health_report(verifier_health_path, task_dir)

            (task_dir / "instruction.md").write_text("changed after packaging\n", encoding="utf-8")

            with mock.patch.object(approve_task.run_static_checks, "run_checks", return_value=build_clean_reporter()), mock.patch.object(
                approve_task.collapse_check,
                "build_report",
                return_value=build_clean_collapse_report(),
            ):
                payload = approve_task.build_report(
                    task_dir,
                    zip_path,
                    job_dir,
                    verifier_health_path=verifier_health_path,
                )

        self.assertFalse(payload["approved"])
        self.assertTrue(
            any(message.startswith("zip/source mismatch: content differs for instruction.md") for message in payload["blocking_failures"])
        )

    def test_missing_verifier_health_report_blocks_approval(self) -> None:
        fixture = FIXTURE_TASKS_DIR / "implicit-step-restart"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            task_dir = tmp_root / fixture.name
            shutil.copytree(fixture, task_dir)
            zip_path = tmp_root / f"{fixture.name}.zip"
            write_zip_from_source(task_dir, zip_path)
            job_dir = tmp_root / "jobs" / "2026-04-15__approve-missing-health"
            write_synthetic_job(job_dir, fixture.name, task_dir)

            with mock.patch.object(approve_task.run_static_checks, "run_checks", return_value=build_clean_reporter()), mock.patch.object(
                approve_task.collapse_check,
                "build_report",
                return_value=build_clean_collapse_report(),
            ):
                payload = approve_task.build_report(task_dir, zip_path, job_dir)

        self.assertFalse(payload["approved"])
        self.assertIn(
            "verifier health failed: missing verifier-health report: run verifier_health.py and pass --verifier-health",
            payload["blocking_failures"],
        )

    def test_verifier_health_failure_blocks_approval(self) -> None:
        fixture = FIXTURE_TASKS_DIR / "implicit-step-restart"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            task_dir = tmp_root / fixture.name
            shutil.copytree(fixture, task_dir)
            zip_path = tmp_root / f"{fixture.name}.zip"
            write_zip_from_source(task_dir, zip_path)
            job_dir = tmp_root / "jobs" / "2026-04-15__approve-health-fail"
            write_synthetic_job(job_dir, fixture.name, task_dir)
            verifier_health_path = tmp_root / "verifier-health.json"
            write_verifier_health_report(
                verifier_health_path,
                task_dir,
                healthy=False,
                blocking_failures=["partial_oracle: no behavioral verifier failure"],
            )

            with mock.patch.object(approve_task.run_static_checks, "run_checks", return_value=build_clean_reporter()), mock.patch.object(
                approve_task.collapse_check,
                "build_report",
                return_value=build_clean_collapse_report(),
            ):
                payload = approve_task.build_report(
                    task_dir,
                    zip_path,
                    job_dir,
                    verifier_health_path=verifier_health_path,
                )

        self.assertFalse(payload["approved"])
        self.assertIn(
            "verifier health failed: partial_oracle: no behavioral verifier failure",
            payload["blocking_failures"],
        )

    def test_cli_json_reports_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier_health_path = Path(tmpdir) / "verifier-health.json"
            write_verifier_health_report(
                verifier_health_path,
                FIXTURE_TASKS_DIR / "lsm-snapshot-recovery",
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = approve_task.main(
                    [
                        "--task-dir",
                        str(FIXTURE_TASKS_DIR / "lsm-snapshot-recovery"),
                        "--zip",
                        str(SUBMISSION_DIR / "lsm-snapshot-recovery.zip"),
                        "--job-dir",
                        str(JOB_DIR),
                        "--verifier-health",
                        str(verifier_health_path),
                        "--json",
                    ]
                )
        self.assertEqual(exit_code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["decision"], "FAIL")
        self.assertIn(
            "default hard gate requires 0 full-suite passes, found 2",
            payload["blocking_failures"],
        )

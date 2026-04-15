#!/usr/bin/env python3
"""
Single hard-task approval gate for Terminal-Bench 3 Edition 2.

Usage:
    python3 approve_task.py --task-dir tasks/<task-name> \
        --zip Task_Ready_To_Submit/<task-name>.zip \
        --job-dir jobs/<job-dir> \
        --verifier-health /tmp/<task-name>-verifier-health.json
    python3 approve_task.py ... --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import analyze_trials
import collapse_check
import run_static_checks
import validate_submission_zip


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_HARD_MODEL = "anthropic/claude-opus-4-6"
MIN_VERIFIER_BACKED_TRIALS = 5


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the repo's single hard-task approval gate across static checks, collapse audit, "
            "submission zip validation, archived trial analysis, and cross-artifact consistency."
        )
    )
    parser.add_argument("--task-dir", type=Path, required=True, help="Task directory under tasks/")
    parser.add_argument("--zip", dest="zip_path", type=Path, required=True, help="Submission zip path")
    parser.add_argument("--job-dir", type=Path, required=True, help="Harbor job directory for agent trials")
    parser.add_argument(
        "--verifier-health",
        dest="verifier_health_path",
        type=Path,
        help="JSON report emitted by verifier_health.py",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args(argv)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def should_skip_packaged_path(path: PurePosixPath) -> bool:
    parts = path.parts
    if any(part == "__pycache__" for part in parts):
        return True
    if any(part.startswith(".") for part in parts):
        return True
    return path.suffix == ".pyc"


def build_source_package_manifest(task_dir: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in sorted(task_dir.rglob("*")):
        if not path.is_file():
            continue
        rel_path = PurePosixPath(path.relative_to(task_dir).as_posix())
        if should_skip_packaged_path(rel_path):
            continue
        manifest[rel_path.as_posix()] = sha256_bytes(path.read_bytes())
    return manifest


def build_zip_manifest(zip_path: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            parts = validate_submission_zip.normalize_member_name(info.filename)
            if not parts:
                continue
            rel_path = PurePosixPath("/".join(parts))
            manifest[rel_path.as_posix()] = sha256_bytes(archive.read(info))
    return manifest


def empty_trial_report(job_dir: Path, error: str) -> dict[str, Any]:
    return {
        "job_dir": str(job_dir.resolve()),
        "task_name": None,
        "agent_name": None,
        "model_id": None,
        "model_label": None,
        "requested_trials": 0,
        "found_trial_dirs": 0,
        "verifier_backed_trials": 0,
        "infra_error_count": 0,
        "mean_reward": None,
        "full_suite_passes": 0,
        "full_suite_pass_rate": None,
        "zero_pass_tests": [],
        "artifact_issues": [error],
        "trials": [],
        "infra_errors": [],
        "tests": [],
    }


def empty_verifier_health_report(
    verifier_health_path: Path | None,
    error: str,
) -> dict[str, Any]:
    return {
        "path": str(verifier_health_path.resolve()) if verifier_health_path else None,
        "healthy": False,
        "decision": "FAIL",
        "blocking_failures": [error],
        "warnings": [],
        "checks": {},
    }


def load_toml_bytes(path: Path) -> dict[str, Any]:
    return run_static_checks.load_toml_file(path)


def load_zip_toml(zip_path: Path, member_name: str) -> dict[str, Any]:
    with zipfile.ZipFile(zip_path) as archive:
        content = archive.read(member_name).decode("utf-8")
    if run_static_checks.tomllib is not None:
        return run_static_checks.tomllib.loads(content)
    return run_static_checks.parse_minimal_toml(content)


def resolve_job_task_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


def verify_manifest_alignment(
    task_dir: Path,
    zip_path: Path,
    job_dir: Path,
    trial_payload: dict[str, Any],
) -> dict[str, Any]:
    passes: list[str] = []
    failures: list[str] = []
    source_manifest_path = task_dir / "task.toml"
    zip_manifest_name = "task.toml"
    source_manifest: dict[str, Any] | None = None
    zip_manifest: dict[str, Any] | None = None

    if source_manifest_path.exists():
        try:
            source_manifest = load_toml_bytes(source_manifest_path)
            passes.append("source task.toml present and parseable")
        except Exception as exc:
            failures.append(f"source task.toml could not be parsed: {exc}")
    else:
        failures.append(f"source task manifest missing: {source_manifest_path}")

    zip_report = validate_submission_zip.build_report(zip_path)
    if zip_manifest_name in zip_report["root_files"]:
        try:
            zip_manifest = load_zip_toml(zip_path, zip_manifest_name)
            passes.append("zip task.toml present and parseable")
        except Exception as exc:
            failures.append(f"zip task.toml could not be parsed: {exc}")
    else:
        failures.append("zip task manifest missing at archive root: task.toml")

    if source_manifest is not None and zip_manifest is not None:
        if source_manifest == zip_manifest:
            passes.append("source and zip task.toml manifests match")
        else:
            failures.append("source and zip task.toml manifests differ")

    if zip_path.stem == task_dir.name:
        passes.append("zip filename matches task directory name")
    else:
        failures.append(
            f"zip filename must match task directory name: {zip_path.stem} != {task_dir.name}"
        )

    job_config_path = job_dir / "config.json"
    if not job_config_path.exists():
        failures.append(f"job config missing: {job_config_path}")
        job_task_path = None
        job_model_name = None
    else:
        try:
            job_config = json.loads(job_config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"job config is not valid JSON: {exc}")
            job_task_path = None
            job_model_name = None
        else:
            tasks = job_config.get("tasks")
            if not isinstance(tasks, list) or len(tasks) != 1:
                failures.append("job config must reference exactly one task in config.json")
                job_task_path = None
            else:
                raw_task_path = tasks[0].get("path")
                if not isinstance(raw_task_path, str) or not raw_task_path.strip():
                    failures.append("job config task entry must include a non-empty tasks[0].path")
                    job_task_path = None
                else:
                    job_task_path = resolve_job_task_path(raw_task_path)
                    if job_task_path == task_dir.resolve():
                        passes.append("job config task path matches --task-dir")
                    else:
                        failures.append(
                            "job config task path does not match --task-dir: "
                            f"{job_task_path} != {task_dir.resolve()}"
                        )

            agents = job_config.get("agents")
            if not isinstance(agents, list) or len(agents) != 1:
                failures.append("job config must define exactly one agent for the default hard gate")
                job_model_name = None
            else:
                job_model_name = agents[0].get("model_name")
                if job_model_name == DEFAULT_HARD_MODEL:
                    passes.append("job config model matches the default Claude Opus 4.6 gate")
                else:
                    failures.append(
                        "job config model must be anthropic/claude-opus-4-6 for the default hard gate, "
                        f"found {job_model_name!r}"
                    )

    analyzed_task_name = trial_payload.get("task_name")
    if analyzed_task_name == task_dir.name:
        passes.append("trial artifacts report the same task name as --task-dir")
    else:
        failures.append(
            "trial artifacts do not match --task-dir: "
            f"{analyzed_task_name!r} != {task_dir.name!r}"
        )

    analyzed_model_id = trial_payload.get("model_id")
    if analyzed_model_id == DEFAULT_HARD_MODEL:
        passes.append("trial artifacts report the default Claude Opus 4.6 model")
    else:
        failures.append(
            "trial artifacts must come from anthropic/claude-opus-4-6 for the default hard gate, "
            f"found {analyzed_model_id!r}"
        )

    return {
        "valid": not failures,
        "passes": passes,
        "failures": failures,
        "task_dir_name": task_dir.name,
        "zip_basename": zip_path.stem,
        "job_dir": str(job_dir.resolve()),
        "analyzed_task_name": analyzed_task_name,
        "analyzed_model_id": analyzed_model_id,
    }


def compare_source_and_zip(task_dir: Path, zip_path: Path) -> dict[str, Any]:
    try:
        source_manifest = build_source_package_manifest(task_dir)
    except OSError as exc:
        return {
            "valid": False,
            "missing_in_zip": [],
            "extra_in_zip": [],
            "content_mismatches": [],
            "source_file_count": 0,
            "zip_file_count": 0,
            "error": f"could not read source task files: {exc}",
        }

    try:
        zip_manifest = build_zip_manifest(zip_path)
    except (OSError, zipfile.BadZipFile) as exc:
        return {
            "valid": False,
            "missing_in_zip": [],
            "extra_in_zip": [],
            "content_mismatches": [],
            "source_file_count": len(source_manifest),
            "zip_file_count": 0,
            "error": f"could not read submission zip: {exc}",
        }

    source_paths = set(source_manifest)
    zip_paths = set(zip_manifest)

    missing_in_zip = sorted(source_paths - zip_paths)
    extra_in_zip = sorted(zip_paths - source_paths)
    content_mismatches = sorted(
        path for path in (source_paths & zip_paths) if source_manifest[path] != zip_manifest[path]
    )

    return {
        "valid": not (missing_in_zip or extra_in_zip or content_mismatches),
        "missing_in_zip": missing_in_zip,
        "extra_in_zip": extra_in_zip,
        "content_mismatches": content_mismatches,
        "source_file_count": len(source_manifest),
        "zip_file_count": len(zip_manifest),
        "error": None,
    }


def load_verifier_health_report(
    task_dir: Path,
    verifier_health_path: Path | None,
) -> dict[str, Any]:
    if verifier_health_path is None:
        return empty_verifier_health_report(
            verifier_health_path,
            "missing verifier-health report: run verifier_health.py and pass --verifier-health",
        )

    verifier_health_path = verifier_health_path.expanduser().resolve()
    try:
        payload = json.loads(verifier_health_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return empty_verifier_health_report(
            verifier_health_path,
            f"verifier-health report does not exist: {verifier_health_path}",
        )
    except json.JSONDecodeError as exc:
        return empty_verifier_health_report(
            verifier_health_path,
            f"verifier-health report is not valid JSON: {exc}",
        )

    blocking_failures = payload.get("blocking_failures")
    warnings = payload.get("warnings")
    checks = payload.get("checks")
    raw_task_dir = payload.get("task_dir")
    healthy = payload.get("healthy")
    decision = payload.get("decision")

    report = {
        "path": str(verifier_health_path),
        "healthy": bool(healthy),
        "decision": decision if isinstance(decision, str) else ("PASS" if healthy else "FAIL"),
        "blocking_failures": blocking_failures if isinstance(blocking_failures, list) else [],
        "warnings": warnings if isinstance(warnings, list) else [],
        "checks": checks if isinstance(checks, dict) else {},
    }

    validation_failures: list[str] = []
    if not isinstance(raw_task_dir, str) or not raw_task_dir.strip():
        validation_failures.append("verifier-health report missing task_dir")
    elif Path(raw_task_dir).expanduser().resolve() != task_dir.resolve():
        validation_failures.append(
            "verifier-health report task_dir does not match --task-dir: "
            f"{Path(raw_task_dir).expanduser().resolve()} != {task_dir.resolve()}"
        )

    required_checks = {"repeat_oracle", "randomized_order", "partial_oracle"}
    missing_checks = sorted(required_checks - set(report["checks"]))
    if missing_checks:
        validation_failures.append(
            "verifier-health report missing required checks: " + ", ".join(missing_checks)
        )

    if validation_failures:
        return {
            **report,
            "healthy": False,
            "decision": "FAIL",
            "blocking_failures": report["blocking_failures"] + validation_failures,
        }

    return report


def build_report(
    task_dir: Path,
    zip_path: Path,
    job_dir: Path,
    verifier_health_path: Path | None = None,
) -> dict[str, Any]:
    task_dir = task_dir.expanduser().resolve()
    zip_path = zip_path.expanduser().resolve()
    job_dir = job_dir.expanduser().resolve()

    if task_dir.is_dir():
        static_reporter = run_static_checks.run_checks(task_dir)
        static_report = static_reporter.as_dict()
        collapse_report = collapse_check.build_report(task_dir)
        collapse_status = (
            "FAIL" if collapse_report["fails"] else "WARN" if collapse_report["warns"] else "PASS"
        )
    else:
        static_report = {
            "passes": [],
            "warnings": [],
            "failures": [f"task directory does not exist: {task_dir}"],
        }
        collapse_report = {
            "oracle_targets": [],
            "oracle_loc_non_boilerplate": 0,
            "touched_roots": [],
            "frontier_concentration": {
                "total_targets": 0,
                "unique_roots": 0,
                "dominant_root": None,
                "dominant_root_count": 0,
                "dominant_root_share": 0.0,
                "roots": [],
            },
            "results": [],
            "fails": 1,
            "warns": 0,
        }
        collapse_status = "FAIL"

    zip_report = validate_submission_zip.build_report(zip_path)
    try:
        trial_report = analyze_trials.analyze_job_dir(job_dir)
    except SystemExit as exc:
        trial_report = empty_trial_report(job_dir, str(exc))
    verifier_health_report = load_verifier_health_report(task_dir, verifier_health_path)
    manifest_report = verify_manifest_alignment(task_dir, zip_path, job_dir, trial_report)
    source_zip_report = compare_source_and_zip(task_dir, zip_path)

    warnings: list[str] = []
    blocking_failures: list[str] = []

    if static_report["warnings"]:
        warnings.extend(f"static check warning: {message}" for message in static_report["warnings"])
    if static_report["failures"]:
        blocking_failures.extend(
            f"static check failed: {message}" for message in static_report["failures"]
        )

    if collapse_report["warns"]:
        warnings.append(
            f"collapse_check.py returned WARN with {collapse_report['warns']} signal(s) that still need justification"
        )
    if collapse_report["fails"]:
        blocking_failures.append(
            f"collapse_check.py returned FAIL with {collapse_report['fails']} blocking signal(s)"
        )

    if not zip_report["valid"]:
        blocking_failures.extend(
            f"submission zip invalid: {message}" for message in zip_report["failures"]
        )

    if not manifest_report["valid"]:
        blocking_failures.extend(
            f"manifest verification failed: {message}" for message in manifest_report["failures"]
        )

    if not source_zip_report["valid"]:
        if source_zip_report.get("error"):
            blocking_failures.append(
                "zip/source mismatch: " + str(source_zip_report["error"])
            )
        if source_zip_report["missing_in_zip"]:
            blocking_failures.append(
                "zip/source mismatch: missing in zip: "
                + ", ".join(source_zip_report["missing_in_zip"])
            )
        if source_zip_report["extra_in_zip"]:
            blocking_failures.append(
                "zip/source mismatch: extra in zip: "
                + ", ".join(source_zip_report["extra_in_zip"])
            )
        if source_zip_report["content_mismatches"]:
            blocking_failures.append(
                "zip/source mismatch: content differs for "
                + ", ".join(source_zip_report["content_mismatches"])
            )

    if verifier_health_report["warnings"]:
        warnings.extend(
            f"verifier health warning: {message}"
            for message in verifier_health_report["warnings"]
        )
    if not verifier_health_report["healthy"]:
        blocking_failures.extend(
            f"verifier health failed: {message}"
            for message in verifier_health_report["blocking_failures"]
        )

    verifier_backed_trials = trial_report.get("verifier_backed_trials") or 0
    if verifier_backed_trials < MIN_VERIFIER_BACKED_TRIALS:
        blocking_failures.append(
            f"missing verifier-backed trials: found {verifier_backed_trials}, need at least {MIN_VERIFIER_BACKED_TRIALS}"
        )

    full_suite_passes = trial_report.get("full_suite_passes") or 0
    if full_suite_passes > 0:
        blocking_failures.append(
            f"default hard gate requires 0 full-suite passes, found {full_suite_passes}"
        )

    zero_pass_tests = trial_report.get("zero_pass_tests") or []
    if zero_pass_tests:
        blocking_failures.append(
            "per-test pass matrix contains 0/N tests: " + ", ".join(zero_pass_tests)
        )

    artifact_issues = trial_report.get("artifact_issues") or []
    if artifact_issues:
        blocking_failures.append(
            "trial artifact issues present: " + "; ".join(artifact_issues)
        )

    infra_error_count = trial_report.get("infra_error_count") or 0
    if infra_error_count:
        warnings.append(
            f"trial analysis reported {infra_error_count} infra error(s); inspect before trusting borderline evidence"
        )

    approved = not blocking_failures

    return {
        "task_dir": str(task_dir),
        "zip_path": str(zip_path),
        "job_dir": str(job_dir),
        "approved": approved,
        "decision": "PASS" if approved else "FAIL",
        "blocking_failures": blocking_failures,
        "warnings": warnings,
        "static_checks": static_report,
        "collapse_check": {
            "status": collapse_status,
            "report": collapse_report,
        },
        "zip_validation": zip_report,
        "manifest_verification": manifest_report,
        "source_zip_verification": source_zip_report,
        "trial_analysis": trial_report,
        "verifier_health": verifier_health_report,
    }


def format_text_report(payload: dict[str, Any]) -> str:
    lines = [
        f"Approval gate: {payload['decision']}",
        f"Task dir: {payload['task_dir']}",
        f"Submission zip: {payload['zip_path']}",
        f"Job dir: {payload['job_dir']}",
        "",
        "Check summary:",
        "  - static checks: "
        + ("FAIL" if payload["static_checks"]["failures"] else "WARN" if payload["static_checks"]["warnings"] else "PASS"),
        f"  - collapse_check.py: {payload['collapse_check']['status']}",
        "  - validate_submission_zip.py: " + ("PASS" if payload["zip_validation"]["valid"] else "FAIL"),
        "  - manifest verification: " + ("PASS" if payload["manifest_verification"]["valid"] else "FAIL"),
        "  - source/zip match: " + ("PASS" if payload["source_zip_verification"]["valid"] else "FAIL"),
        "  - verifier_health.py: " + ("PASS" if payload["verifier_health"]["healthy"] else "FAIL"),
        "  - analyze_trials.py: "
        + (
            f"{payload['trial_analysis']['verifier_backed_trials']} verifier-backed trials, "
            f"{payload['trial_analysis']['full_suite_passes']} full-suite pass(es), "
            f"{len(payload['trial_analysis']['zero_pass_tests'])} zero-pass test(s), "
            f"{len(payload['trial_analysis']['artifact_issues'])} artifact issue(s)"
        ),
    ]

    if payload["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"  - {warning}" for warning in payload["warnings"])

    if payload["blocking_failures"]:
        lines.extend(["", "Blocking failures:"])
        lines.extend(f"  - {failure}" for failure in payload["blocking_failures"])
    else:
        lines.extend(["", "Blocking failures:", "  - none"])

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_report(
        args.task_dir,
        args.zip_path,
        args.job_dir,
        verifier_health_path=args.verifier_health_path,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_text_report(payload))
    return 0 if payload["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

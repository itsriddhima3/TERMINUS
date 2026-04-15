#!/usr/bin/env python3
"""
Summarize Harbor trial artifacts from a single job directory.

Usage:
    python3 analyze_trials.py jobs/<job-dir>
    python3 analyze_trials.py jobs/<job-dir> --json
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze one Harbor job directory using the repo's real artifact layout: "
            "<job-dir>/result.json plus <job-dir>/<trial>/result.json and "
            "<job-dir>/<trial>/verifier/ctrf.json."
        )
    )
    parser.add_argument("job_dir", type=Path, help="Harbor job directory under jobs/")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args(argv)


def is_trial_dir(path: Path) -> bool:
    return path.is_dir() and (path / "result.json").exists()


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_numeric_token(token: str) -> bool:
    return token.replace(".", "", 1).isdigit()


def humanize_model_name(name: str | None) -> str | None:
    if not name:
        return None
    tokens = name.replace("_", "-").split("-")
    words: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        lower = token.lower()
        if token.isdigit() and i + 1 < len(tokens) and tokens[i + 1].isdigit():
            words.append(f"{token}.{tokens[i + 1]}")
            i += 2
            continue
        if is_numeric_token(token):
            words.append(token)
        elif lower == "gpt":
            words.append("GPT")
        else:
            words.append(token.capitalize())
        i += 1
    return " ".join(words)


def short_trial_label(trial_name: str) -> str:
    if "__" in trial_name:
        return trial_name.rsplit("__", 1)[1]
    return trial_name


def truncate(text: str, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def format_reward(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    if "." not in text:
        return f"{text}.0"
    return text


def matrix_cell(status: str | None) -> str:
    if status == "passed":
        return "PASS"
    if not status:
        return "-"
    return status.upper()


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def render_row(row: list[str]) -> str:
        return "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))

    rendered = [render_row(headers), render_row(["-" * width for width in widths])]
    rendered.extend(render_row(row) for row in rows)
    return "\n".join(rendered)


def analyze_job_dir(job_dir: Path) -> dict[str, Any]:
    job_dir = job_dir.expanduser().resolve()
    if not job_dir.is_dir():
        raise SystemExit(f"Job directory does not exist: {job_dir}")

    root_result = load_json(job_dir / "result.json")
    trial_dirs = sorted(path for path in job_dir.iterdir() if is_trial_dir(path))
    if not trial_dirs:
        raise SystemExit(f"No trial directories with result.json found under {job_dir}")

    trial_rows: list[dict[str, Any]] = []
    infra_errors: list[dict[str, str]] = []
    artifact_issues: list[str] = []
    ordered_tests: OrderedDict[str, None] = OrderedDict()

    for trial_dir in trial_dirs:
        result = load_json(trial_dir / "result.json")
        trial_name = result.get("trial_name") or trial_dir.name
        verifier_result = result.get("verifier_result") or {}
        reward = (verifier_result.get("rewards") or {}).get("reward")
        exception_info = result.get("exception_info") or {}
        ctrf_path = trial_dir / "verifier" / "ctrf.json"
        test_statuses: dict[str, str] = {}

        if exception_info:
            infra_errors.append(
                {
                    "trial": trial_name,
                    "type": exception_info.get("exception_type", "UnknownError"),
                    "message": truncate(
                        exception_info.get("exception_message", "No exception message recorded.")
                    ),
                }
            )
        elif ctrf_path.exists():
            ctrf = load_json(ctrf_path)
            for test in ctrf.get("results", {}).get("tests", []):
                test_name = test.get("name")
                if not test_name:
                    continue
                ordered_tests.setdefault(test_name, None)
                test_statuses[test_name] = test.get("status", "unknown")
        else:
            artifact_issues.append(
                f"{trial_name}: missing verifier artifact {ctrf_path.relative_to(job_dir)}"
            )

        if reward is None and not exception_info:
            artifact_issues.append(f"{trial_name}: missing verifier_result.rewards.reward in result.json")

        model_info = result.get("agent_info", {}).get("model_info") or {}
        config_model = result.get("config", {}).get("agent", {}).get("model_name")
        provider = model_info.get("provider")
        model_name = model_info.get("name")
        model_id = config_model or (f"{provider}/{model_name}" if provider and model_name else None)

        trial_rows.append(
            {
                "trial": trial_name,
                "short_label": short_trial_label(trial_name),
                "task_name": result.get("task_name"),
                "agent_name": result.get("agent_info", {}).get("name"),
                "model_id": model_id,
                "model_label": humanize_model_name(model_name) if model_name else None,
                "reward": float(reward) if is_number(reward) else None,
                "test_statuses": test_statuses,
                "has_exception": bool(exception_info),
            }
        )

    task_names = {row["task_name"] for row in trial_rows if row["task_name"]}
    agent_names = {row["agent_name"] for row in trial_rows if row["agent_name"]}
    model_ids = {row["model_id"] for row in trial_rows if row["model_id"]}
    model_labels = {row["model_label"] for row in trial_rows if row["model_label"]}

    rewards = [row["reward"] for row in trial_rows if row["reward"] is not None]
    verifier_trials = [row for row in trial_rows if row["reward"] is not None]
    full_suite_passes = sum(1 for reward in rewards if math.isclose(reward, 1.0))
    zero_pass_tests = [
        test_name
        for test_name in ordered_tests
        if sum(
            1
            for row in verifier_trials
            if row["test_statuses"].get(test_name) == "passed"
        )
        == 0
    ]

    mean_reward = statistics.mean(rewards) if rewards else None
    requested_trials = root_result.get("n_total_trials", len(trial_dirs))

    return {
        "job_dir": str(job_dir),
        "task_name": next(iter(sorted(task_names)), None),
        "agent_name": next(iter(sorted(agent_names)), None),
        "model_id": next(iter(sorted(model_ids)), None),
        "model_label": next(iter(sorted(model_labels)), None),
        "requested_trials": requested_trials,
        "found_trial_dirs": len(trial_dirs),
        "verifier_backed_trials": len(verifier_trials),
        "infra_error_count": len(infra_errors),
        "mean_reward": mean_reward,
        "full_suite_passes": full_suite_passes,
        "full_suite_pass_rate": (
            full_suite_passes / len(verifier_trials) if verifier_trials else None
        ),
        "zero_pass_tests": zero_pass_tests,
        "artifact_issues": artifact_issues,
        "trials": [
            {
                "trial": row["trial"],
                "reward": row["reward"],
                "test_statuses": row["test_statuses"],
                "has_exception": row["has_exception"],
            }
            for row in trial_rows
        ],
        "infra_errors": infra_errors,
        "tests": [
            {
                "name": test_name,
                "passes": sum(
                    1
                    for row in verifier_trials
                    if row["test_statuses"].get(test_name) == "passed"
                ),
                "verifier_trials": len(verifier_trials),
                "by_trial": {
                    row["trial"]: row["test_statuses"].get(test_name)
                    for row in verifier_trials
                },
            }
            for test_name in ordered_tests
        ],
    }

def format_analysis_report(payload: dict[str, Any]) -> str:
    analysis_label = (
        payload["model_label"]
        or payload["model_id"]
        or payload["agent_name"]
        or "unknown run"
    )
    model_details = (
        f"{payload['model_label']} ({payload['model_id']})"
        if payload["model_label"] and payload["model_id"]
        else payload["model_id"] or "n/a"
    )
    verifier_trials = [row for row in payload["trials"] if row["reward"] is not None]
    requested_trials = payload["requested_trials"]
    mean_reward = payload["mean_reward"]
    full_suite_passes = payload["full_suite_passes"]
    infra_errors = payload["infra_errors"]
    zero_pass_tests = payload["zero_pass_tests"]
    artifact_issues = payload["artifact_issues"]
    lines = [f"Job: {payload['job_dir']}"]
    if payload["task_name"]:
        lines.append(f"Task: {payload['task_name']}")
    if payload["agent_name"]:
        lines.append(f"Agent: {payload['agent_name']}")
    lines.append(f"Model: {model_details}")
    lines.append(f"Requested trials: {requested_trials}")
    lines.append(f"Found trial directories: {payload['found_trial_dirs']}")
    lines.append(f"Trials analyzed: {len(verifier_trials)} {analysis_label} trials")
    lines.append(f"Infra errors: {len(infra_errors)}")
    if mean_reward is None:
        lines.append("Mean reward: n/a")
        lines.append("Full-suite pass rate: n/a")
    else:
        lines.append(f"Mean reward: {format_reward(mean_reward)}")
        lines.append(
            "Full-suite pass rate: "
            f"{full_suite_passes}/{len(verifier_trials)} "
            f"({full_suite_passes / len(verifier_trials):.1%})"
        )

    lines.append("")
    lines.append("Per-trial rewards:")
    for row in payload["trials"]:
        if row["has_exception"]:
            continue
        reward_text = "n/a" if row["reward"] is None else format_reward(row["reward"])
        lines.append(f"- {row['trial']}: {reward_text}")

    if payload["tests"]:
        headers = ["Test"] + [short_trial_label(row["trial"]) for row in verifier_trials] + ["Passes"]
        rows = []
        for test_entry in payload["tests"]:
            test_name = test_entry["name"]
            pass_count = test_entry["passes"]
            rows.append(
                [test_name]
                + [matrix_cell(test_entry["by_trial"].get(row["trial"])) for row in verifier_trials]
                + [f"{pass_count}/{len(verifier_trials)}"]
            )
        lines.append("")
        lines.append("Per-test pass matrix:")
        lines.append(render_table(headers, rows))
    else:
        lines.append("")
        lines.append("Per-test pass matrix:")
        lines.append("No verifier-backed CTRF artifacts found.")

    lines.append("")
    lines.append("Zero-pass tests:")
    if zero_pass_tests:
        for test_name in zero_pass_tests:
            lines.append(f"- {test_name}")
    elif verifier_trials:
        lines.append(f"No individual test at 0/{len(verifier_trials)}.")
    else:
        lines.append("No verifier-backed trials to analyze.")

    lines.append("")
    lines.append("Infra errors:")
    if infra_errors:
        for error in infra_errors:
            lines.append(f"- {error['trial']}: {error['type']} - {error['message']}")
    else:
        lines.append("None.")

    if artifact_issues:
        lines.append("")
        lines.append("Artifact issues:")
        for issue in artifact_issues:
            lines.append(f"- {issue}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = analyze_job_dir(args.job_dir)
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print(format_analysis_report(payload))

    return 0


if __name__ == "__main__":
    sys.exit(main())

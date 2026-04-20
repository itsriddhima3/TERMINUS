#!/usr/bin/env python3
"""
Validation loop state machine for Terminal-Bench 3 task ideas.

Cursor calls this script after each validation attempt. The script tracks
state, validates structured Step 2a evidence, decides the next action, and
outputs machine-readable directives that Cursor reads to decide what to do next.

Usage (called by Cursor during Step 2a):
    python validate_loop.py init <task-name>
    python validate_loop.py record <task-name> --evidence /tmp/<task-name>-validation-evidence.json
    python validate_loop.py select <task-name> --winner N|specs/<task-name>.md
    python validate_loop.py status <task-name>
    python validate_loop.py reset <task-name>

Output format (last lines, machine-readable):
    ACTION: CONTINUE | SELECT | GO | STOP
    SAVE_TO: specs/<authoring-path>
    REVIEWER_SAVE_TO: specs/<reviewer-path>
    REASON: <why>
    CANDIDATES: <comma-separated attempt=authoring|reviewer entries>  (only for SELECT)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import exceptions as jsonschema_exceptions
    from jsonschema import validators as jsonschema_validators
except ModuleNotFoundError:
    jsonschema_exceptions = None
    jsonschema_validators = None

SPECS_DIR = Path("specs")
SCHEMA_PATH = SPECS_DIR / "validation_schema.json"
MAX_ATTEMPTS = 5
PLATEAU_THRESHOLD = 2
MIN_DISCOVERY_BUDGET_ITEMS = 3
VALID_VERDICTS = {"PASS", "WARN", "FAIL"}
VALID_SPECIFICITY_LEVELS = {
    "spec-complete",
    "cause-revealing",
    "symptoms-only",
}

HARDNESS_AXES = {
    "discover": "Discover",
    "synthesize": "Synthesize",
    "diagnose": "Diagnose",
    "navigate_coupling": "Navigate coupling",
    "reason_beyond_training": "Reason beyond training",
}

RUBRIC_AXES = {
    "verifiable": "Verifiable",
    "well_specified": "Well-specified",
    "solvable": "Solvable",
    "difficult": "Difficult",
    "interesting": "Interesting",
    "outcome_verified": "Outcome-verified",
}

ANTI_TRIVIALIZATION_CHECKS = {
    "disclosure_collapse": "Disclosure-collapse",
    "hidden_instance": "Hidden-instance",
    "single_artifact_repair": "Single-artifact repair",
    "generalization": "Generalization",
    "prompt_honesty": "Prompt-honesty",
    "cheating_vs_difficulty": "Cheating-vs-difficulty",
    "mechanical_fix_filter": "Mechanical-fix filter",
    "localized_fix": "Localized-fix",
    "oracle_locality": "Oracle-locality",
    "small_declarative_cluster": "Small declarative-cluster",
    "grep_collapse": "Grep-collapse",
    "pre_factored_helper": "Pre-factored-helper",
    "recipe_discount": "Recipe-discount",
    "security_aura_discount": "Security-aura discount",
    "orthogonal_checklist": "Orthogonal-checklist",
    "harness_discount": "Harness-discount",
    "one_pass_solvability": "One-pass solvability",
    "hard_only_gate": "Hard-only gate",
    "discovery_budget_test": "Discovery budget test",
    "instruction_specificity_test": "Instruction specificity test",
}


def state_path(task_name: str) -> Path:
    return SPECS_DIR / f".{task_name}-state.json"


def attempt_evidence_path(task_name: str, attempt: int) -> Path:
    return SPECS_DIR / f"{task_name}-attempt-{attempt}-evidence.json"


def authoring_spec_path(task_name: str, candidate_n: int | None = None) -> Path:
    if candidate_n is None:
        return SPECS_DIR / f"{task_name}.md"
    return SPECS_DIR / f"{task_name}-candidate-{candidate_n}.md"


def reviewer_spec_path(task_name: str, candidate_n: int | None = None) -> Path:
    if candidate_n is None:
        return SPECS_DIR / f"{task_name}-reviewer.md"
    return SPECS_DIR / f"{task_name}-candidate-{candidate_n}-reviewer.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_state(task_name: str) -> dict[str, Any]:
    sp = state_path(task_name)
    if not sp.exists():
        print(f"ERROR: No active loop for '{task_name}'. Run init first.")
        sys.exit(1)
    return load_json(sp)


def save_state(task_name: str, state: dict[str, Any]) -> None:
    state_path(task_name).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_named_verdict_entries(
    evidence: dict[str, Any],
    field_name: str,
    expected: dict[str, str],
    errors: list[str],
    counts: dict[str, int],
) -> list[dict[str, str]]:
    entries = evidence.get(field_name)
    if not isinstance(entries, list):
        errors.append(f"{field_name} must be a list.")
        return []

    normalized: dict[str, dict[str, str]] = {}
    for index, entry in enumerate(entries, start=1):
        prefix = f"{field_name}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object.")
            continue

        entry_id = entry.get("id")
        if not _is_non_empty_string(entry_id):
            errors.append(f"{prefix}.id must be a non-empty string.")
            continue
        entry_id = entry_id.strip()

        if entry_id in normalized:
            errors.append(f"{field_name} has duplicate id {entry_id!r}.")
            continue

        name = entry.get("name")
        verdict = entry.get("verdict")
        reasoning = entry.get("reasoning")

        if not _is_non_empty_string(name):
            errors.append(f"{prefix}.name must be a non-empty string.")
            continue
        if verdict not in VALID_VERDICTS:
            errors.append(f"{prefix}.verdict must be one of {sorted(VALID_VERDICTS)}.")
            continue
        if not _is_non_empty_string(reasoning):
            errors.append(f"{prefix}.reasoning must be a non-empty string.")
            continue

        normalized[entry_id] = {
            "id": entry_id,
            "name": name.strip(),
            "verdict": verdict,
            "reasoning": reasoning.strip(),
        }

    missing = [entry_id for entry_id in expected if entry_id not in normalized]
    extra = [entry_id for entry_id in normalized if entry_id not in expected]
    if missing:
        errors.append(f"{field_name} is missing required ids: {', '.join(missing)}.")
    if extra:
        errors.append(f"{field_name} contains unexpected ids: {', '.join(extra)}.")

    ordered: list[dict[str, str]] = []
    for entry_id, expected_name in expected.items():
        entry = normalized.get(entry_id)
        if entry is None:
            continue
        if entry["name"] != expected_name:
            errors.append(
                f"{field_name} entry {entry_id!r} must use name {expected_name!r}, found {entry['name']!r}."
            )
            continue
        counts[entry["verdict"]] += 1
        ordered.append(entry)

    return ordered


def _validate_verdict_block(
    evidence: dict[str, Any],
    field_name: str,
    errors: list[str],
    counts: dict[str, int],
) -> dict[str, str]:
    value = evidence.get(field_name)
    if not isinstance(value, dict):
        errors.append(f"{field_name} must be an object.")
        return {}

    verdict = value.get("verdict")
    reasoning = value.get("reasoning")
    if verdict not in VALID_VERDICTS:
        errors.append(f"{field_name}.verdict must be one of {sorted(VALID_VERDICTS)}.")
        return {}
    if not _is_non_empty_string(reasoning):
        errors.append(f"{field_name}.reasoning must be a non-empty string.")
        return {}

    counts[verdict] += 1
    return {"verdict": verdict, "reasoning": reasoning.strip()}


def _validate_instruction_specificity(
    evidence: dict[str, Any],
    errors: list[str],
    hard_fail_reasons: list[str],
) -> dict[str, str]:
    value = evidence.get("instruction_specificity")
    if not isinstance(value, dict):
        errors.append("instruction_specificity must be an object.")
        return {}

    level = value.get("level")
    reasoning = value.get("reasoning")
    if level not in VALID_SPECIFICITY_LEVELS:
        errors.append(
            "instruction_specificity.level must be one of "
            f"{sorted(VALID_SPECIFICITY_LEVELS)}."
        )
        return {}
    if not _is_non_empty_string(reasoning):
        errors.append("instruction_specificity.reasoning must be a non-empty string.")
        return {}

    normalized = {"level": level, "reasoning": reasoning.strip()}
    if level != "symptoms-only":
        hard_fail_reasons.append(
            "instruction_specificity.level must be 'symptoms-only' for the default hard-only Step 2a workflow."
        )
    return normalized


def _validate_analysis_block(
    evidence: dict[str, Any],
    field_name: str,
    errors: list[str],
) -> dict[str, str]:
    value = evidence.get(field_name)
    if not isinstance(value, dict):
        errors.append(f"{field_name} must be an object.")
        return {}

    summary = value.get("summary")
    reasoning = value.get("reasoning")
    if not _is_non_empty_string(summary):
        errors.append(f"{field_name}.summary must be a non-empty string.")
        return {}
    if not _is_non_empty_string(reasoning):
        errors.append(f"{field_name}.reasoning must be a non-empty string.")
        return {}

    return {"summary": summary.strip(), "reasoning": reasoning.strip()}


def _validate_discovery_budget(
    evidence: dict[str, Any],
    errors: list[str],
    hard_fail_reasons: list[str],
) -> list[dict[str, str]]:
    value = evidence.get("discovery_budget")
    if not isinstance(value, list):
        errors.append("discovery_budget must be a list.")
        return []

    normalized: list[dict[str, str]] = []
    for index, item in enumerate(value, start=1):
        prefix = f"discovery_budget[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object.")
            continue

        discovery = item.get("discovery")
        planned_location = item.get("planned_location")
        why_instruction_must_not_reveal = item.get("why_instruction_must_not_reveal")
        if not _is_non_empty_string(discovery):
            errors.append(f"{prefix}.discovery must be a non-empty string.")
            continue
        if not _is_non_empty_string(planned_location):
            errors.append(f"{prefix}.planned_location must be a non-empty string.")
            continue
        if not _is_non_empty_string(why_instruction_must_not_reveal):
            errors.append(
                f"{prefix}.why_instruction_must_not_reveal must be a non-empty string."
            )
            continue

        normalized.append(
            {
                "discovery": discovery.strip(),
                "planned_location": planned_location.strip(),
                "why_instruction_must_not_reveal": why_instruction_must_not_reveal.strip(),
            }
        )

    if len(normalized) < MIN_DISCOVERY_BUDGET_ITEMS:
        hard_fail_reasons.append(
            "discovery_budget must contain at least 3 non-trivial solver discoveries "
            "that the finished task will force from the codebase."
        )

    return normalized


def _validate_collapse_audit(
    evidence: dict[str, Any],
    errors: list[str],
    counts: dict[str, int],
) -> dict[str, Any]:
    value = evidence.get("collapse_audit")
    if not isinstance(value, dict):
        errors.append("collapse_audit must be an object.")
        return {}

    verdict = value.get("verdict")
    reasoning = value.get("reasoning")
    residual_hardness = value.get("residual_hardness")
    red_flags = value.get("red_flags", [])

    if verdict not in VALID_VERDICTS:
        errors.append(f"collapse_audit.verdict must be one of {sorted(VALID_VERDICTS)}.")
        return {}
    if not _is_non_empty_string(reasoning):
        errors.append("collapse_audit.reasoning must be a non-empty string.")
        return {}
    if not _is_non_empty_string(residual_hardness):
        errors.append("collapse_audit.residual_hardness must be a non-empty string.")
        return {}
    if not isinstance(red_flags, list) or any(not _is_non_empty_string(flag) for flag in red_flags):
        errors.append("collapse_audit.red_flags must be a list of non-empty strings when provided.")
        return {}

    counts[verdict] += 1
    return {
        "verdict": verdict,
        "reasoning": reasoning.strip(),
        "residual_hardness": residual_hardness.strip(),
        "red_flags": [flag.strip() for flag in red_flags],
    }


def _load_validation_schema() -> tuple[dict[str, Any] | None, list[str]]:
    if jsonschema_exceptions is None or jsonschema_validators is None:
        return None, [
            "jsonschema is required to validate Step 2a evidence against "
            f"{SCHEMA_PATH.as_posix()}."
        ]

    if not SCHEMA_PATH.exists():
        return None, [f"Schema file {SCHEMA_PATH.as_posix()} is missing from the repo."]

    try:
        schema = load_json(SCHEMA_PATH)
    except json.JSONDecodeError as exc:
        return None, [f"Schema file {SCHEMA_PATH.as_posix()} is not valid JSON: {exc}"]

    if not isinstance(schema, dict):
        return None, [f"Schema file {SCHEMA_PATH.as_posix()} must contain a JSON object."]

    try:
        validator_cls, runtime_schema = _schema_validator(schema)
        validator_cls.check_schema(runtime_schema)
    except jsonschema_exceptions.SchemaError as exc:
        return None, [f"Schema file {SCHEMA_PATH.as_posix()} is not a valid JSON Schema: {exc.message}"]

    return runtime_schema, []


def _format_json_path(path: Any) -> str:
    if not path:
        return "$"

    parts = ["$"]
    for component in path:
        if isinstance(component, int):
            parts.append(f"[{component}]")
        else:
            parts.append(f".{component}")
    return "".join(parts)


def _validate_schema(raw_evidence: Any) -> list[str]:
    schema, schema_load_errors = _load_validation_schema()
    if schema is None:
        return schema_load_errors

    validator_cls, runtime_schema = _schema_validator(schema)
    validator = validator_cls(runtime_schema)
    errors = sorted(
        validator.iter_errors(raw_evidence),
        key=lambda error: (_format_json_path(error.absolute_path), error.message),
    )
    return [
        f"Schema validation failed at {_format_json_path(error.absolute_path)}: {error.message}"
        for error in errors
    ]


def _schema_validator(schema: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    draft_2020_12 = getattr(jsonschema_validators, "Draft202012Validator", None)
    if draft_2020_12 is not None:
        return draft_2020_12, schema
    return jsonschema_validators.Draft7Validator, _draft7_compatible_schema(schema)


def _draft7_compatible_schema(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = "definitions" if key == "$defs" else key
            normalized_value = _draft7_compatible_schema(item)
            if key == "$ref" and isinstance(normalized_value, str):
                normalized_value = normalized_value.replace("#/$defs/", "#/definitions/")
            normalized[normalized_key] = normalized_value
        return normalized

    if isinstance(value, list):
        return [_draft7_compatible_schema(item) for item in value]

    return value


def validate_evidence(raw_evidence: Any) -> dict[str, Any]:
    schema_errors = _validate_schema(raw_evidence)
    if schema_errors:
        return {
            "normalized": {},
            "errors": schema_errors,
            "hard_fail_reasons": schema_errors,
            "score": [len(schema_errors), 0],
        }

    errors: list[str] = []
    hard_fail_reasons: list[str] = []
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}

    normalized: dict[str, Any] = {}
    normalized["hardness_axes"] = _validate_named_verdict_entries(
        raw_evidence, "hardness_axes", HARDNESS_AXES, errors, counts
    )
    normalized["anti_trivialization_checks"] = _validate_named_verdict_entries(
        raw_evidence, "anti_trivialization_checks", ANTI_TRIVIALIZATION_CHECKS, errors, counts
    )
    normalized["rubric_axes"] = _validate_named_verdict_entries(
        raw_evidence, "rubric_axes", RUBRIC_AXES, errors, counts
    )
    normalized["instruction_completeness_test"] = _validate_verdict_block(
        raw_evidence, "instruction_completeness_test", errors, counts
    )
    normalized["discovery_budget"] = _validate_discovery_budget(
        raw_evidence, errors, hard_fail_reasons
    )
    normalized["instruction_specificity"] = _validate_instruction_specificity(
        raw_evidence, errors, hard_fail_reasons
    )
    normalized["attack_path"] = _validate_analysis_block(raw_evidence, "attack_path", errors)
    normalized["smallest_plausible_patch"] = _validate_analysis_block(
        raw_evidence, "smallest_plausible_patch", errors
    )
    normalized["collapse_audit"] = _validate_collapse_audit(raw_evidence, errors, counts)

    anti_map = {
        entry["id"]: entry for entry in normalized["anti_trivialization_checks"] if isinstance(entry, dict)
    }
    discovery_budget_check = anti_map.get("discovery_budget_test")
    if (
        discovery_budget_check
        and discovery_budget_check["verdict"] == "PASS"
        and len(normalized["discovery_budget"]) < MIN_DISCOVERY_BUDGET_ITEMS
    ):
        errors.append(
            "anti_trivialization_checks marks discovery_budget_test PASS, but "
            "discovery_budget has fewer than 3 items."
        )

    specificity_check = anti_map.get("instruction_specificity_test")
    specificity_level = normalized["instruction_specificity"].get("level")
    if specificity_check and specificity_check["verdict"] == "PASS" and specificity_level != "symptoms-only":
        errors.append(
            "anti_trivialization_checks marks instruction_specificity_test PASS, but instruction_specificity.level is not 'symptoms-only'."
        )

    hard_fail_reasons = list(dict.fromkeys(hard_fail_reasons + errors))
    score = [counts["FAIL"] + len(hard_fail_reasons), counts["WARN"]]
    return {
        "normalized": normalized,
        "errors": errors,
        "hard_fail_reasons": hard_fail_reasons,
        "score": score,
    }


def cmd_init(args: argparse.Namespace) -> None:
    task_name = args.task_name
    SPECS_DIR.mkdir(exist_ok=True)

    sp = state_path(task_name)
    if sp.exists():
        print("Loop already active. Run 'reset' first to start over.")
        sys.exit(1)

    state = {
        "task_name": task_name,
        "attempt": 0,
        "best_score": [999, 999],
        "best_attempt": 0,
        "plateau_count": 0,
        "candidates": [],
        "history": [],
        "schema_path": SCHEMA_PATH.as_posix(),
    }
    save_state(task_name, state)

    log = SPECS_DIR / f"{task_name}-validation-log.md"
    log.write_text(f"# Validation Log: {task_name}\n\n", encoding="utf-8")

    print(f"Initialized loop for '{task_name}'.")
    print(f"Evidence schema: {SCHEMA_PATH.as_posix()}")
    print("ACTION: CONTINUE")
    print(f"SAVE_TO: {authoring_spec_path(task_name).as_posix()}")
    print(f"REVIEWER_SAVE_TO: {reviewer_spec_path(task_name).as_posix()}")
    print("REASON: First attempt — run CHECK on the idea and record structured evidence.")


def cmd_record(args: argparse.Namespace) -> None:
    task_name = args.task_name
    state = load_state(task_name)

    if (args.fails is None) != (args.warns is None):
        print("ERROR: --fails and --warns must be provided together if you provide either one.")
        sys.exit(1)

    evidence_input_path = Path(args.evidence)
    if not evidence_input_path.is_absolute():
        evidence_input_path = Path.cwd() / evidence_input_path
    if not evidence_input_path.exists():
        print(f"ERROR: Evidence file {evidence_input_path} does not exist.")
        sys.exit(1)

    try:
        raw_evidence = load_json(evidence_input_path)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Evidence file {evidence_input_path} is not valid JSON: {exc}")
        sys.exit(1)

    attempt = state["attempt"] + 1
    validation = validate_evidence(raw_evidence)
    fails, warns = validation["score"]
    provided_score = None
    provided_score_mismatch = None
    if args.fails is not None and args.warns is not None:
        provided_score = [args.fails, args.warns]
        if provided_score != [fails, warns]:
            provided_score_mismatch = (
                f"Provided score was {args.fails}F/{args.warns}W but the loop derived "
                f"{fails}F/{warns}W from structured evidence."
            )

    stored_evidence_path = attempt_evidence_path(task_name, attempt)
    stored_evidence_path.write_text(
        json.dumps(validation["normalized"], indent=2) + "\n",
        encoding="utf-8",
    )

    state["attempt"] = attempt
    history_entry = {
        "attempt": attempt,
        "fails": fails,
        "warns": warns,
        "evidence_path": stored_evidence_path.as_posix(),
        "evidence": validation["normalized"],
        "evidence_errors": validation["errors"],
        "blocking_failures": validation["hard_fail_reasons"],
    }
    if provided_score is not None:
        history_entry["provided_score"] = provided_score
    if provided_score_mismatch is not None:
        history_entry["provided_score_mismatch"] = provided_score_mismatch
    state["history"].append(history_entry)

    log = SPECS_DIR / f"{task_name}-validation-log.md"
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(f"## Attempt {attempt}\n")
        handle.write(f"- Derived score: {fails} FAILs, {warns} WARNs\n")
        handle.write(f"- Evidence: {stored_evidence_path.name}\n")
        if provided_score is not None:
            handle.write(f"- Provided score: {provided_score[0]} FAILs, {provided_score[1]} WARNs\n")
        if provided_score_mismatch is not None:
            handle.write(f"- Score mismatch: {provided_score_mismatch}\n")
        if validation["errors"]:
            handle.write("- Evidence errors:\n")
            for issue in validation["errors"]:
                handle.write(f"  - {issue}\n")
        if validation["hard_fail_reasons"]:
            handle.write("- Blocking evidence failures:\n")
            for issue in validation["hard_fail_reasons"]:
                handle.write(f"  - {issue}\n")
        handle.write("\n")

    best = state["best_score"]
    improved = (fails, warns) < (best[0], best[1])
    same_score = [fails, warns] == best

    if fails == 0 and warns == 0:
        state["best_score"] = [fails, warns]
        state["best_attempt"] = attempt
        _cleanup_candidate_files(task_name, state)
        state["candidates"] = []
        save_state(task_name, state)
        print(f"Attempt {attempt}: {fails}F, {warns}W — PERFECT")
        if provided_score_mismatch is not None:
            print(f"NOTE: {provided_score_mismatch}")
        print("ACTION: GO")
        print(f"SAVE_TO: {authoring_spec_path(task_name).as_posix()}")
        print(f"REVIEWER_SAVE_TO: {reviewer_spec_path(task_name).as_posix()}")
        print("REASON: Structured evidence is complete and every scored check passed.")
        return

    if improved:
        state["best_score"] = [fails, warns]
        state["best_attempt"] = attempt
        state["plateau_count"] = 0
        _cleanup_candidate_files(task_name, state)
        state["candidates"] = []
        save_to = authoring_spec_path(task_name).as_posix()
        reviewer_save_to = reviewer_spec_path(task_name).as_posix()
        print(f"Attempt {attempt}: {fails}F, {warns}W — IMPROVED (was {best[0]}F, {best[1]}W)")
    elif same_score:
        state["plateau_count"] += 1
        candidate_n = len(state["candidates"]) + 1
        state["candidates"].append(
            {
                "attempt": attempt,
                "candidate_n": candidate_n,
                "score": [fails, warns],
                "evidence_path": stored_evidence_path.as_posix(),
            }
        )
        save_to = authoring_spec_path(task_name, candidate_n).as_posix()
        reviewer_save_to = reviewer_spec_path(task_name, candidate_n).as_posix()
        print(
            f"Attempt {attempt}: {fails}F, {warns}W — PLATEAU "
            f"({state['plateau_count']}/{PLATEAU_THRESHOLD})"
        )
    else:
        save_to = "DISCARD"
        reviewer_save_to = "DISCARD"
        print(
            f"Attempt {attempt}: {fails}F, {warns}W — REGRESSION "
            f"(best is {best[0]}F, {best[1]}W, discarding)"
        )

    if provided_score_mismatch is not None:
        print(f"NOTE: {provided_score_mismatch}")

    if validation["hard_fail_reasons"]:
        print("Blocking evidence issues:")
        for issue in validation["hard_fail_reasons"]:
            print(f"  - {issue}")

    if state["plateau_count"] >= PLATEAU_THRESHOLD:
        save_state(task_name, state)
        if state["best_score"][0] > 0:
            print("ACTION: STOP")
            print(f"SAVE_TO: {save_to}")
            print(f"REVIEWER_SAVE_TO: {reviewer_save_to}")
            print("REASON: Plateau with FAILs remaining. Idea family cannot be saved.")
        else:
            print("ACTION: SELECT")
            print(f"SAVE_TO: {save_to}")
            print(f"REVIEWER_SAVE_TO: {reviewer_save_to}")
            print("REASON: Plateau reached. Compare candidates via collapse audit and stored evidence.")
            print(f"CANDIDATES: {_candidate_directive(task_name, state)}")
        return

    if attempt >= 3:
        last_3 = state["history"][-3:]
        no_improvement = all(
            current["fails"] >= previous["fails"] and current["warns"] >= previous["warns"]
            for previous, current in zip(last_3, last_3[1:])
        ) and last_3[-1]["fails"] > 0
        if no_improvement:
            save_state(task_name, state)
            print("ACTION: STOP")
            print(f"SAVE_TO: {save_to}")
            print(f"REVIEWER_SAVE_TO: {reviewer_save_to}")
            print(
                f"REASON: No score improvement across 3 consecutive attempts "
                f"(still {fails}F). Idea family cannot be saved."
            )
            return

    if attempt >= MAX_ATTEMPTS:
        save_state(task_name, state)
        if state["best_score"][0] == 0:
            if state["candidates"]:
                print("ACTION: SELECT")
                print(f"SAVE_TO: {save_to}")
                print(f"REVIEWER_SAVE_TO: {reviewer_save_to}")
                print("REASON: Max attempts reached. Compare candidates via collapse audit and stored evidence.")
                print(f"CANDIDATES: {_candidate_directive(task_name, state)}")
            else:
                print("ACTION: GO")
                print(f"SAVE_TO: {authoring_spec_path(task_name).as_posix()}")
                print(f"REVIEWER_SAVE_TO: {reviewer_spec_path(task_name).as_posix()}")
                print("REASON: Max attempts reached. Best variant has 0 FAILs with complete structured evidence.")
        else:
            print("ACTION: STOP")
            print(f"SAVE_TO: {save_to}")
            print(f"REVIEWER_SAVE_TO: {reviewer_save_to}")
            print("REASON: Max attempts with FAILs remaining.")
        return

    save_state(task_name, state)
    print("ACTION: CONTINUE")
    print(f"SAVE_TO: {save_to}")
    print(f"REVIEWER_SAVE_TO: {reviewer_save_to}")
    if validation["hard_fail_reasons"]:
        print("REASON: Structured evidence is incomplete or blocking checks still fail.")
    else:
        print(f"REASON: {'Improved — fix remaining WARNs.' if improved else 'Plateau — try different fixes.'}")


def _cleanup_candidate_files(task_name: str, state: dict[str, Any]) -> None:
    for candidate in state.get("candidates", []):
        for path in (
            authoring_spec_path(task_name, candidate["candidate_n"]),
            reviewer_spec_path(task_name, candidate["candidate_n"]),
        ):
            if path.exists():
                path.unlink()


def _candidate_specs(task_name: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        {
            "attempt": state["best_attempt"],
            "candidate_n": None,
            "authoring_path": authoring_spec_path(task_name).as_posix(),
            "reviewer_path": reviewer_spec_path(task_name).as_posix(),
        }
    ]
    for candidate in state.get("candidates", []):
        candidates.append(
            {
                "attempt": candidate["attempt"],
                "candidate_n": candidate["candidate_n"],
                "authoring_path": authoring_spec_path(task_name, candidate["candidate_n"]).as_posix(),
                "reviewer_path": reviewer_spec_path(task_name, candidate["candidate_n"]).as_posix(),
            }
        )
    return candidates


def _candidate_directive(task_name: str, state: dict[str, Any]) -> str:
    return ",".join(
        f"{candidate['attempt']}={candidate['authoring_path']}|{candidate['reviewer_path']}"
        for candidate in _candidate_specs(task_name, state)
    )


def _candidate_choices(task_name: str, state: dict[str, Any]) -> str:
    return ", ".join(
        f"attempt {candidate['attempt']} -> {candidate['authoring_path']} | {candidate['reviewer_path']}"
        for candidate in _candidate_specs(task_name, state)
    )


def _resolve_winner(task_name: str, state: dict[str, Any], winner: str) -> dict[str, Any] | None:
    winner = winner.strip()
    if not winner:
        return None

    for candidate in _candidate_specs(task_name, state):
        if (
            winner == str(candidate["attempt"])
            or winner == candidate["authoring_path"]
            or winner == candidate["reviewer_path"]
        ):
            return candidate

    winner_path = Path(winner)
    resolved_winner = (winner_path if winner_path.is_absolute() else Path.cwd() / winner_path).resolve()
    for candidate in _candidate_specs(task_name, state):
        for path_key in ("authoring_path", "reviewer_path"):
            candidate_path = Path(candidate[path_key])
            resolved_candidate = (Path.cwd() / candidate_path).resolve()
            if resolved_winner == resolved_candidate:
                return candidate

    return None


def cmd_select(args: argparse.Namespace) -> None:
    task_name = args.task_name
    state = load_state(task_name)
    winner = _resolve_winner(task_name, state, args.winner)

    if winner is None:
        print(
            f"ERROR: --winner {args.winner!r} is not a valid candidate. "
            f"Valid choices: {_candidate_choices(task_name, state)}"
        )
        sys.exit(1)

    winner_attempt = winner["attempt"]
    previous_best = state["best_attempt"]
    canonical_authoring = authoring_spec_path(task_name)
    canonical_reviewer = reviewer_spec_path(task_name)
    if winner_attempt == previous_best:
        missing = [
            path.as_posix()
            for path in (canonical_authoring, canonical_reviewer)
            if not path.exists()
        ]
        if missing:
            print(f"ERROR: Canonical spec files are missing: {', '.join(missing)}")
            sys.exit(1)
        print(
            f"Winner is the pre-plateau best (attempt {winner_attempt}), "
            f"already at {canonical_authoring.name} and {canonical_reviewer.name}."
        )
    else:
        winner_authoring = authoring_spec_path(task_name, winner["candidate_n"])
        winner_reviewer = reviewer_spec_path(task_name, winner["candidate_n"])
        missing = [
            path.as_posix()
            for path in (winner_authoring, winner_reviewer)
            if not path.exists()
        ]
        if missing:
            print(
                f"ERROR: Candidate files for attempt {winner_attempt} not found on disk: "
                f"{', '.join(missing)}"
            )
            sys.exit(1)

        canonical_authoring.write_text(
            winner_authoring.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        canonical_reviewer.write_text(
            winner_reviewer.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        print(
            f"Promoted {winner_authoring.name} -> {canonical_authoring.name} and "
            f"{winner_reviewer.name} -> {canonical_reviewer.name}"
        )

    state["best_attempt"] = winner_attempt
    _cleanup_candidate_files(task_name, state)
    state["candidates"] = []
    save_state(task_name, state)

    print(
        f"Winner: attempt {winner_attempt} "
        f"({winner['authoring_path']} | {winner['reviewer_path']})"
    )
    print("ACTION: GO")
    print(f"SAVE_TO: {canonical_authoring.as_posix()}")
    print(f"REVIEWER_SAVE_TO: {canonical_reviewer.as_posix()}")
    print("REASON: Candidate selected and promoted. Spec is final.")


def cmd_status(args: argparse.Namespace) -> None:
    state = load_state(args.task_name)
    print(json.dumps(state, indent=2))


def cmd_reset(args: argparse.Namespace) -> None:
    task_name = args.task_name
    for path in SPECS_DIR.glob(f"{task_name}*"):
        path.unlink()
    for path in SPECS_DIR.glob(f".{task_name}*"):
        path.unlink()
    print(f"Reset '{task_name}'.")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    init_parser = sub.add_parser("init")
    init_parser.add_argument("task_name")

    record_parser = sub.add_parser("record")
    record_parser.add_argument("task_name")
    record_parser.add_argument("--evidence", required=True)
    record_parser.add_argument("--fails", type=int)
    record_parser.add_argument("--warns", type=int)

    select_parser = sub.add_parser("select")
    select_parser.add_argument("task_name")
    select_parser.add_argument("--winner", required=True)

    status_parser = sub.add_parser("status")
    status_parser.add_argument("task_name")

    reset_parser = sub.add_parser("reset")
    reset_parser.add_argument("task_name")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {
        "init": cmd_init,
        "record": cmd_record,
        "select": cmd_select,
        "status": cmd_status,
        "reset": cmd_reset,
    }[args.command](args)


if __name__ == "__main__":
    main()

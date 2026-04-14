#!/usr/bin/env python3
"""
Validation loop state machine for Terminal-Bench 3 task ideas.

Cursor calls this script after each validation attempt. The script tracks
state, decides the next action, and outputs a machine-readable directive
that Cursor reads to decide what to do next.

Usage (called by Cursor during Step 2a):
    python validate_loop.py init <task-name>
    python validate_loop.py record <task-name> --fails N --warns N
    python validate_loop.py select <task-name> --winner N
    python validate_loop.py status <task-name>
    python validate_loop.py reset <task-name>

Output format (last line, machine-readable):
    ACTION: CONTINUE | SELECT | GO | STOP
    SAVE_TO: specs/<path>
    REASON: <why>
    CANDIDATES: <comma-separated paths>  (only for SELECT)
"""

import argparse
import json
import sys
from pathlib import Path

SPECS_DIR = Path("specs")
MAX_ATTEMPTS = 5
PLATEAU_THRESHOLD = 2


def state_path(task_name: str) -> Path:
    return SPECS_DIR / f".{task_name}-state.json"

def load_state(task_name: str) -> dict:
    sp = state_path(task_name)
    if not sp.exists():
        print(f"ERROR: No active loop for '{task_name}'. Run init first.")
        sys.exit(1)
    return json.loads(sp.read_text())

def save_state(task_name: str, state: dict):
    state_path(task_name).write_text(json.dumps(state, indent=2) + "\n")


def cmd_init(args):
    task_name = args.task_name
    SPECS_DIR.mkdir(exist_ok=True)

    sp = state_path(task_name)
    if sp.exists():
        print(f"Loop already active. Run 'reset' first to start over.")
        sys.exit(1)

    state = {
        "task_name": task_name,
        "attempt": 0,
        "best_score": [999, 999],
        "best_attempt": 0,
        "plateau_count": 0,
        "candidates": [],
        "history": [],
    }
    save_state(task_name, state)

    # Init log
    log = SPECS_DIR / f"{task_name}-validation-log.md"
    log.write_text(f"# Validation Log: {task_name}\n\n")

    print(f"Initialized loop for '{task_name}'.")
    print(f"ACTION: CONTINUE")
    print(f"SAVE_TO: specs/{task_name}.md")
    print(f"REASON: First attempt — run CHECK on the idea.")


def cmd_record(args):
    task_name = args.task_name
    state = load_state(task_name)

    fails = args.fails
    warns = args.warns
    attempt = state["attempt"] + 1
    score = [fails, warns]

    state["attempt"] = attempt
    state["history"].append({"attempt": attempt, "fails": fails, "warns": warns})

    # Log
    log = SPECS_DIR / f"{task_name}-validation-log.md"
    with open(log, "a") as f:
        f.write(f"## Attempt {attempt}\n- FAILs: {fails}\n- WARNs: {warns}\n\n")

    best = state["best_score"]
    improved = (fails, warns) < (best[0], best[1])
    same_score = [fails, warns] == best

    # ── Perfect ──
    if fails == 0 and warns == 0:
        state["best_score"] = score
        state["best_attempt"] = attempt
        _cleanup_candidate_files(task_name, state)  # Delete files BEFORE clearing list
        state["candidates"] = []
        save_state(task_name, state)
        print(f"Attempt {attempt}: {fails}F, {warns}W — PERFECT")
        print(f"ACTION: GO")
        print(f"SAVE_TO: specs/{task_name}.md")
        print(f"REASON: Perfect score. Spec is final.")
        return

    # ── Improved ──
    if improved:
        state["best_score"] = score
        state["best_attempt"] = attempt
        state["plateau_count"] = 0
        # Clear stale candidates — they were from a worse score
        _cleanup_candidate_files(task_name, state)
        state["candidates"] = []
        save_to = f"specs/{task_name}.md"
        print(f"Attempt {attempt}: {fails}F, {warns}W — IMPROVED (was {best[0]}F, {best[1]}W)")
    elif same_score:
        # ── Plateau (same score as best) — save as candidate ──
        state["plateau_count"] += 1
        cn = len(state["candidates"]) + 1
        state["candidates"].append({"attempt": attempt, "candidate_n": cn, "score": score})
        save_to = f"specs/{task_name}-candidate-{cn}.md"
        print(f"Attempt {attempt}: {fails}F, {warns}W — PLATEAU ({state['plateau_count']}/{PLATEAU_THRESHOLD})")
    else:
        # ── Regression (worse than best) — discard, do not save or count ──
        save_to = "DISCARD"
        print(f"Attempt {attempt}: {fails}F, {warns}W — REGRESSION (best is {best[0]}F, {best[1]}W, discarding)")

    # ── Check stopping conditions ──

    # Plateau reached
    if state["plateau_count"] >= PLATEAU_THRESHOLD:
        save_state(task_name, state)
        if state["best_score"][0] > 0:
            print(f"ACTION: STOP")
            print(f"SAVE_TO: {save_to}")
            print(f"REASON: Plateau with FAILs remaining. Idea family cannot be saved.")
        else:
            candidates = [f"specs/{task_name}.md"]
            for c in state["candidates"]:
                candidates.append(f"specs/{task_name}-candidate-{c['candidate_n']}.md")
            print(f"ACTION: SELECT")
            print(f"SAVE_TO: {save_to}")
            print(f"REASON: Plateau reached. Compare candidates via collapse audit.")
            print(f"CANDIDATES: {','.join(candidates)}")
        return

    # Unfixable: 3+ consecutive attempts with no improvement in either FAILs or WARNs
    if attempt >= 3:
        last_3 = state["history"][-3:]
        no_improvement = all(
            curr["fails"] >= prev["fails"] and curr["warns"] >= prev["warns"]
            for prev, curr in zip(last_3, last_3[1:])
        ) and last_3[-1]["fails"] > 0
        if no_improvement:
            save_state(task_name, state)
            print(f"ACTION: STOP")
            print(f"SAVE_TO: {save_to}")
            print(f"REASON: No score improvement across 3 consecutive attempts (still {fails}F). Idea family cannot be saved.")
            return

    # Max attempts
    if attempt >= MAX_ATTEMPTS:
        save_state(task_name, state)
        if state["best_score"][0] == 0:
            if state["candidates"]:
                candidates = [f"specs/{task_name}.md"]
                for c in state["candidates"]:
                    candidates.append(f"specs/{task_name}-candidate-{c['candidate_n']}.md")
                print(f"ACTION: SELECT")
                print(f"SAVE_TO: {save_to}")
                print(f"REASON: Max attempts reached. Compare candidates via collapse audit.")
                print(f"CANDIDATES: {','.join(candidates)}")
            else:
                print(f"ACTION: GO")
                print(f"SAVE_TO: specs/{task_name}.md")
                print(f"REASON: Max attempts reached. Best variant has 0 FAILs.")
        else:
            print(f"ACTION: STOP")
            print(f"SAVE_TO: {save_to}")
            print(f"REASON: Max attempts with FAILs remaining.")
        return

    # ── Continue ──
    save_state(task_name, state)
    print(f"ACTION: CONTINUE")
    print(f"SAVE_TO: {save_to}")
    print(f"REASON: {'Improved — fix remaining WARNs.' if improved else 'Plateau — try different fixes.'}")


def _cleanup_candidate_files(task_name: str, state: dict):
    """Remove candidate spec files from disk."""
    for c in state.get("candidates", []):
        cf = SPECS_DIR / f"{task_name}-candidate-{c['candidate_n']}.md"
        if cf.exists():
            cf.unlink()


def cmd_select(args):
    task_name = args.task_name
    state = load_state(task_name)
    winner = args.winner

    # Validate winner is a real attempt
    prev_best = state["best_attempt"]
    valid_attempts = {prev_best}
    valid_attempts.update(c["attempt"] for c in state["candidates"])
    if winner not in valid_attempts:
        print(f"ERROR: --winner {winner} is not a valid candidate. Valid attempts: {sorted(valid_attempts)}")
        sys.exit(1)

    canonical = SPECS_DIR / f"{task_name}.md"

    if winner == prev_best:
        # Winner is the pre-plateau best — already in canonical spec
        if not canonical.exists():
            print(f"ERROR: Canonical spec {canonical} does not exist.")
            sys.exit(1)
        print(f"Winner is the pre-plateau best (attempt {winner}), already at {canonical.name}.")
    else:
        # Winner is a plateau candidate — find and promote its file
        winner_file = None
        for c in state["candidates"]:
            if c["attempt"] == winner:
                winner_file = SPECS_DIR / f"{task_name}-candidate-{c['candidate_n']}.md"
                break

        if winner_file is None or not winner_file.exists():
            print(f"ERROR: Candidate file for attempt {winner} not found on disk.")
            sys.exit(1)

        canonical.write_text(winner_file.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Promoted {winner_file.name} -> {canonical.name}")

    # Update state, clean up ALL candidate files
    state["best_attempt"] = winner
    _cleanup_candidate_files(task_name, state)
    state["candidates"] = []
    save_state(task_name, state)

    print(f"Winner: attempt {winner}")
    print(f"ACTION: GO")
    print(f"SAVE_TO: specs/{task_name}.md")
    print(f"REASON: Candidate selected and promoted. Spec is final.")


def cmd_status(args):
    state = load_state(args.task_name)
    print(json.dumps(state, indent=2))


def cmd_reset(args):
    task_name = args.task_name
    for f in SPECS_DIR.glob(f"{task_name}*"):
        f.unlink()
    for f in SPECS_DIR.glob(f".{task_name}*"):
        f.unlink()
    print(f"Reset '{task_name}'.")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("init")
    p.add_argument("task_name")

    p = sub.add_parser("record")
    p.add_argument("task_name")
    p.add_argument("--fails", type=int, required=True)
    p.add_argument("--warns", type=int, required=True)

    p = sub.add_parser("select")
    p.add_argument("task_name")
    p.add_argument("--winner", type=int, required=True)

    p = sub.add_parser("status")
    p.add_argument("task_name")

    p = sub.add_parser("reset")
    p.add_argument("task_name")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"init": cmd_init, "record": cmd_record, "select": cmd_select,
     "status": cmd_status, "reset": cmd_reset}[args.command](args)


if __name__ == "__main__":
    main()

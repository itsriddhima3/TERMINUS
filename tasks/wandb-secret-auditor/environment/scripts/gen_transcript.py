#!/usr/bin/env python3
"""Generate long-form, non-repetitive security review transcript files."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ACTORS = (
    "Morgan",
    "Priya",
    "Alex",
    "Jordan",
    "Sam",
    "Riley",
    "Casey",
    "Quinn",
    "Avery",
    "Drew",
)

THEMES = (
    "offline laptop capture hygiene",
    "nested log path normalization",
    "artifact digest recomputation",
    "approval envelope replay windows",
    "HMAC field ordering debates",
    "nonce format deprecation timelines",
    "redaction span preservation",
    "link prefix allow-lists",
    "draft policy retirement",
    "deterministic JSON key ordering",
    "fixture immutability expectations",
    "operator snippet context windows",
    "run metadata id stability",
    "sensitive token grep baselines",
    "relative file reference audits",
    "public artifact URI schemes",
    "private artifact rejection rationale",
    "transcript corpus fingerprinting",
    "multi-meeting policy tag history",
    "cross-team runner variance",
    "stdout versus nested trace logs",
    "approval JSON array versus object shapes",
    "invalid proof reason taxonomies",
    "exposure code vocabulary",
    "bench exposure roll-up semantics",
    "idempotent CLI re-run guarantees",
    "build script classpath layout",
    "Kotlin CLI packaging constraints",
    "security review action tracking",
    "post-incident sanitized output checks",
)

DETAILS = (
    "captured notes mention intermittent false positives on short tokens",
    "participants agreed to keep surrounding log context in snippets",
    "discussion referenced prior SR tags only for historical comparison",
    "team rejected widening private artifact prefixes in active policy",
    "consensus required per-line alerts instead of whole-file summaries",
    "reviewers stressed ascending sort for run identifiers from meta.json",
    "action item: verify proofs bind scope before run id before nonce",
    "open question on legacy nonce rejection messaging for operators",
    "noted symlink targets must stay inside the run directory root",
    "emphasized SHA-256 over sorted transcript bodies with newline glue",
    "reminder: draft blocks remain readable but must not change enforcement",
    "example cited api_key= style markers versus token: colon patterns",
    "highlighted need for stable totals fields in the aggregate object",
    "review board examined four sample exports with mixed approval validity",
    "participants compared laptop export timestamps across regions",
    "review board asked for explicit EXPOSED code on exposure rows",
    "security champions warned against bracket-style redaction placeholders",
    "operators requested clearer invalid-nonce reasons in approvals array",
    "SRE liaison confirmed offline mode forbids mutating input run trees",
    "data science lead asked for artifact byte counts beside digests",
)

DECISIONS = (
    "defer UI for this CLI",
    "keep lexicon as non-authoritative index",
    "document SNIPPET_MARK separately from transcript",
    "schedule follow-up on approval key rotation",
    "no change to active tag during this session",
    "archive rejected private prefix proposal",
    "align tests with recomputed digests only",
    "publish internal FAQ for auditors",
    "track false negative samples in spreadsheet",
    "pair with legal on retention windows",
)


def paragraph(meeting: int, index: int) -> str:
    actor = ACTORS[(meeting * 3 + index) % len(ACTORS)]
    theme = THEMES[(meeting * 11 + index * 5) % len(THEMES)]
    detail = DETAILS[(meeting + index * 7) % len(DETAILS)]
    decision = DECISIONS[(meeting * 17 + index) % len(DECISIONS)]
    batch = (meeting * 29 + index * 13) % 97
    digest_hint = hashlib.sha256(f"{meeting}:{index}:{theme}".encode()).hexdigest()[:12]
    return (
        f"§{index:03d} — {actor} on {theme} (batch {batch:02d}, ref {digest_hint}): "
        f"{detail}. Outcome noted: {decision}.\n"
    )


def render_meeting(meeting: int) -> str:
    lines: list[str] = [
        f"Security review transcript — working session {meeting:02d}\n",
        "Facilitator notes: this appendix is historical color only; enforcement follows the ACTIVE block elsewhere in the corpus.\n",
        "\n",
        "Agenda highlights:\n",
        f"- Review offline export {meeting:02d} anomalies\n",
        "- Compare redaction operator strings against the lexicon index\n",
        "- Capture open risks for deterministic reporting\n",
        "\n",
        "Discussion record:\n",
    ]
    for i in range(1, 185):
        lines.append(paragraph(meeting, i))
    lines.append("\n")
    lines.append("Closing actions:\n")
    for j in range(1, 16):
        owner = ACTORS[(meeting + j) % len(ACTORS)]
        topic = THEMES[(meeting * 2 + j) % len(THEMES)]
        lines.append(f"- {owner} will prototype checks for {topic} before sprint {j + meeting}.\n")
    if meeting % 7 == 0:
        lines.extend(
            [
                "\n",
                "Draft tag captured for archival comparison (not active):\n",
                "POLICY_TAG: SR-2026-05\n",
                "STATUS: DRAFT\n",
                "ALLOW_REF_PREFIX: artifact://private/\n",
                "NONCE_FMT: NNC-v3:<run>:<8hex>\n",
            ]
        )
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "out_dir",
        nargs="?",
        default="/app/docs/review",
        help="Directory for meeting_*.txt files",
    )
    args = parser.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for meeting in range(4, 36):
        path = out / f"meeting_{meeting:02d}.txt"
        path.write_text(render_meeting(meeting), encoding="utf-8")


if __name__ == "__main__":
    main()

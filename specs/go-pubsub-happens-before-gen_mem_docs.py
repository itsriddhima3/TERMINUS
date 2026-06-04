#!/usr/bin/env python3
"""Generate long-context memory-model reference under /app/docs/mem."""

from __future__ import annotations

import html
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "tasks/go-pubsub-happens-before/environment/docs/mem"
RNG = random.Random(0x6D656D)

LANES = (
    ("rendezvous lane", "rendezvous"),
    ("teardown lane", "teardown"),
    ("buffered fan-out lane", "buffered"),
    ("stop notification lane", "stop_notify"),
)

PART_FOCUS = {
    1: ("registry wiring", "peer registries acquiring lane handles during attach"),
    2: ("live publish cadence", "payload writes preceding rendezvous sends on live paths"),
    3: ("rendezvous visibility", "receiver visibility after rendezvous completion"),
    4: ("buffered decoupling", "non-zero lane capacity decoupling send from receive timing"),
    5: ("teardown ordering", "lane closure relative to payload writes and pending signals"),
    6: ("stop branch discipline", "draining pending data signals before storage reads on stop"),
    7: ("multi-peer fan-out", "monotonic revision labels across parallel peers"),
    8: ("race-enabled audits", "intermittent stale labels under load and race detection"),
}

WORKED = (
    ("Example 3", "buffered capacity masks tear in sequential runs while race audits still fail"),
    ("Example 7", "rendezvous lane with single peer — write, send, receive, then read storage"),
    ("Example 9", "triple fan-out requires monotonic labels after each rendezvous completes"),
    ("Example 11", "teardown closes data lane before final send — stale label observed at stop"),
    ("Example 14", "stop branch reads storage before draining buffered signals on notify lane"),
    ("Example 16", "late attach observes prior label when teardown lane closes early"),
    ("Example 18", "ack barrier requires per-peer rendezvous before shared teardown proceeds"),
    ("Example 21", "ring rotation publishes body bytes only after notify rendezvous completes"),
)

# Rotating vocabulary pools (org-specific, high lexical diversity).
ACTORS = (
    "dispatch goroutine",
    "handoff loop",
    "registry attach path",
    "fan-out coordinator",
    "payload slot writer",
    "subscriber select loop",
    "graceful shutdown handler",
    "peer detach hook",
)
SIGNALS = (
    "notify pulse",
    "stop sentinel",
    "lane closure edge",
    "rendezvous completion",
    "buffered enqueue",
    "pending signal backlog",
    "cross-peer barrier",
    "revision counter bump",
)
ARTIFACTS = (
    "sync audit row",
    "race stack frame",
    "coalesce trace window",
    "ring slot rotation",
    "metrics sidecar tap",
    "ack barrier tally",
    "body digest fingerprint",
    "slot index rotation",
)
OBSERVATIONS = (
    "stale revision label",
    "zero-value receive",
    "premature storage consult",
    "monotonicity break",
    "intermittent tear",
    "happens-before gap",
    "sequential false negative",
    "fan-out skew",
)
CONTEXTS = (
    "burst delivery rehearsal",
    "graceful stop drill",
    "late attach simulation",
    "backlog clearing exercise",
    "triple peer rehearsal",
    "branch toggle stress",
    "drain-zero edge replay",
    "package stress sweep",
)

TEMPLATES = (
    "During {ctx}, the {actor} may emit a {obs} when {signal} precedes {artifact} on the {lane}.",
    "Reviewers correlating {ctx} with {lane} timelines note {actor} activity around {signal} and {artifact}.",
    "Field telemetry from {ctx} often shows {obs} if {actor} consults storage before {signal} settles on the {lane}.",
    "Unlike mutex-only mitigations, {ctx} analysis ties {obs} to {lane} ordering between {signal} and {artifact}.",
    "Legacy runbooks for {lane} under {ctx} under-specify how {actor} interacts with {signal}; capture {artifact} spans.",
    "When {ctx} replays include {artifact}, compare {signal} ordering against {actor} traces on the {lane}.",
    "Histograms of {ctx} failures cluster near {obs} whenever {lane} closure races ahead of {signal}.",
    "Parallel {ctx} sweeps expose {obs} if {actor} ignores {signal} while {artifact} is still pending on the {lane}.",
    "Org vocabulary maps {lane} to channel semantics; during {ctx}, treat {signal} as the visibility gate before {artifact}.",
    "Audit diffs for {ctx} highlight {obs} when {actor} records {artifact} without a matching {signal} on the {lane}.",
)


def pick(pool: tuple[str, ...], *keys: int) -> str:
    return pool[sum(keys) % len(pool)]


def unique_paragraph(part: int, section: str, index: int, lane_title: str) -> str:
    sentence_a = TEMPLATES[(part + index) % len(TEMPLATES)].format(
        ctx=pick(CONTEXTS, part, index),
        actor=pick(ACTORS, index, part),
        obs=pick(OBSERVATIONS, part, index, 3),
        signal=pick(SIGNALS, index, part, 5),
        artifact=pick(ARTIFACTS, part, index, 7),
        lane=lane_title,
    )
    sentence_b = TEMPLATES[(part + index + 3) % len(TEMPLATES)].format(
        ctx=pick(CONTEXTS, index, part, 11),
        actor=pick(ACTORS, part, index, 13),
        obs=pick(OBSERVATIONS, index, part),
        signal=pick(SIGNALS, part, index),
        artifact=pick(ARTIFACTS, index, part, 17),
        lane=lane_title,
    )
    focus_title, focus_body = PART_FOCUS[part]
    sentence_c = (
        f"Part {part:02d} ({focus_title}) documents {focus_body}; "
        f"section {section} entry {index:03d} records lane-specific ordering constraints "
        f"for maintainers reconciling fan-out distribution semantics with internal audits."
    )
    return f"{sentence_a} {sentence_b} {sentence_c}"


def part_markdown(part: int) -> str:
    lane = LANES[(part - 1) % len(LANES)]
    focus_title, focus_body = PART_FOCUS[part]
    lines = [
        f"# Part {part:02d}: {lane[0]}",
        "",
        f"## {part}.0 Scope — {focus_title}",
        "",
        f"This chapter documents {focus_body}. Terminology intentionally reframes standard",
        "channel semantics for fan-out services combining live delivery and stop notification.",
        "",
    ]
    for section_idx, section in enumerate(
        ("baseline", "regression", "operations", "audit", "migration", "monitoring")
    ):
        lines.append(f"## {part}.{section_idx + 1} {section.title()} notes on {lane[0]}")
        lines.append("")
        for i in range(1, 121):
            lines.append(f"### {part}.{section_idx + 1}.{i:03d}")
            lines.append("")
            lines.append(unique_paragraph(part, section, i, lane[0]))
            lines.append("")
    return "\n".join(lines)


def example_trace(title: str, summary: str, trace_idx: int, example_idx: int) -> str:
    lane = LANES[(example_idx + trace_idx) % len(LANES)][0]
    opener = TEMPLATES[(trace_idx + example_idx) % len(TEMPLATES)].format(
        ctx=pick(CONTEXTS, trace_idx, example_idx),
        actor=pick(ACTORS, example_idx, trace_idx),
        obs=pick(OBSERVATIONS, trace_idx, example_idx),
        signal=pick(SIGNALS, example_idx, trace_idx),
        artifact=pick(ARTIFACTS, trace_idx, example_idx),
        lane=lane,
    )
    middle = (
        f"{title} documents: {summary}. Trace {trace_idx:03d} correlates publisher teardown "
        f"timelines with subscriber select outcomes on the {lane}."
    )
    closer = TEMPLATES[(trace_idx * 3 + example_idx + 5) % len(TEMPLATES)].format(
        ctx=pick(CONTEXTS, example_idx, trace_idx, 19),
        actor=pick(ACTORS, trace_idx, example_idx, 23),
        obs=pick(OBSERVATIONS, example_idx, trace_idx, 29),
        signal=pick(SIGNALS, trace_idx, example_idx, 31),
        artifact=pick(ARTIFACTS, example_idx, trace_idx, 37),
        lane=lane,
    )
    return f"{opener} {middle} {closer}"


def examples_markdown() -> str:
    lines = ["# Worked synchronization examples", ""]
    for ex_idx, (title, summary) in enumerate(WORKED):
        lines.append(f"## {title}")
        lines.append("")
        lines.append(summary + ".")
        lines.append("")
        for trace_idx in range(1, 81):
            lines.append(f"### {title} field note {trace_idx:03d}")
            lines.append("")
            lines.append(example_trace(title, summary, trace_idx, ex_idx))
            lines.append("")
    return "\n".join(lines)


def index_markdown() -> str:
    links = [f"- [Part {i:02d}](part_{i:02d}.md)" for i in range(1, 9)]
    links.append("- [Worked examples](examples.md)")
    return "# Memory model reference index\n\n" + "\n".join(links) + "\n"


def md_to_html(md_text: str, title: str) -> str:
    body = []
    for line in md_text.splitlines():
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.strip():
            body.append(f"<p>{html.escape(line.strip())}</p>")
    return (
        "<html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title></head><body>"
        + "\n".join(body)
        + "</body></html>"
    )


def write_corpus() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "INDEX.md").write_text(index_markdown(), encoding="utf-8")

    index_html = [
        "<html><head><meta charset='utf-8'><title>Memory Model Index</title></head><body>",
        "<h1>Internal synchronization reference</h1><ul>",
    ]
    for part in range(1, 9):
        md = part_markdown(part)
        md_name = f"part_{part:02d}.md"
        html_name = f"part_{part:02d}.html"
        (ROOT / md_name).write_text(md, encoding="utf-8")
        (ROOT / html_name).write_text(md_to_html(md, f"Part {part}"), encoding="utf-8")
        index_html.append(f'<li><a href="{html_name}">Part {part:02d}</a></li>')

    ex_md = examples_markdown()
    (ROOT / "examples.md").write_text(ex_md, encoding="utf-8")
    (ROOT / "examples.html").write_text(md_to_html(ex_md, "Examples"), encoding="utf-8")
    index_html.append('<li><a href="examples.html">Worked examples</a></li>')
    index_html.append("</ul></body></html>")
    (ROOT / "index.html").write_text("\n".join(index_html), encoding="utf-8")


if __name__ == "__main__":
    write_corpus()
    print(f"Wrote memory-model corpus under {ROOT}")

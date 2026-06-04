#!/usr/bin/env python3
"""Generate long-context boundary contract corpus for java-batch-lane-reconcile."""

from __future__ import annotations

import html
import random
from pathlib import Path

ROOT = (
    Path(__file__).resolve().parent.parent
    / "tasks/java-batch-lane-reconcile/environment/docs"
)
RNG = random.Random(0x4C414E45)

PARTS = {
    2: ("Observation frame alignment", "pool handoff and JDBC session semantics vs advertised profile"),
    3: ("Commit frame integrity", "atomic visibility of header and line slices within one business key"),
    4: ("Slice and rollup lanes", "application flush order versus trigger lock acquisition on partitions"),
    5: ("Stamp column placement", "numeric guards on aggregates that mutate under concurrent replay"),
    6: ("Post-success envelope", "coordinator retries that must not re-enter the ingest commit frame"),
    7: ("Partition family caps", "North-Shelf, East-Crate, and West-Bin active slot ceilings"),
    8: ("Audit matrix semantics", "scenario rows, ingest compliance, and stress summary fields"),
    9: ("Idempotent replay", "external business key collisions under pipelined workers"),
    10: ("Rollup monotonicity", "partition counters under quad bursts and sequential replays"),
    11: ("Read-after-write snapshots", "snapshot readers after successful slice persistence"),
    12: ("Interleave and tri-fanout", "mixed-family bursts without cross-taint on rollup totals"),
}

WORKED = (
    ("Example 1", "Solo worker on one family honors cap without rollup wobble"),
    ("Example 2", "Pair workers on North-Shelf contend within six active slots"),
    ("Example 3", "Quad workers on East-Crate stress rollup lane ordering"),
    ("Example 4", "Pool initializer downgrade breaks read-after-write snapshots"),
    ("Example 5", "Partial abort must leave zero accepted for the faulted chunk"),
    ("Example 6", "Exact depletion leaves stable totals without duplicate keys"),
    ("Example 7", "Pipelined backlog stays within family caps under burst"),
    ("Example 8", "Second connection on a handoff observes phantom rollup without frame alignment"),
    ("Example 9", "Interleaved posts across families must not bleed counters"),
    ("Example 10", "Sibling contention while another family runs solo ingest"),
    ("Example 11", "Post-success coordinator must run outside the ingest commit frame"),
    ("Example 12", "Tri-fanout burst across three families with simultaneous workers"),
)

ACTORS = (
    "slice lane writer",
    "rollup lane trigger",
    "pool handoff path",
    "post-success coordinator",
    "partition catalog reader",
    "lane audit harness",
    "chunk dispatch worker",
    "facility bootstrap hook",
)
SIGNALS = (
    "observation frame downgrade",
    "commit frame closure",
    "slice flush ordering",
    "rollup lock inversion",
    "stamp column drift",
    "post-success retry",
    "cap rejection edge",
    "ingest compliance flag",
)
ARTIFACTS = (
    "lane audit row",
    "partition counter",
    "line slice row",
    "header aggregate",
    "external business key",
    "scenario matrix cell",
    "stress summary tally",
    "ingest compliance bit",
)
OBSERVATIONS = (
    "lost row drift",
    "duplicate external key",
    "unstable rollup total",
    "line parity break",
    "read-after-write gap",
    "rollup non-monotone",
    "cross-family counter bleed",
    "phantom rollup snapshot",
)
CONTEXTS = (
    "quad burst rehearsal",
    "solo lane replay",
    "pool dual-connection drill",
    "tri-fanout stress",
    "idempotent rerun window",
    "partial abort simulation",
    "stamp diverge guard",
    "interleave AB exercise",
)
FAMILIES = ("North-Shelf", "East-Crate", "West-Bin")

TEMPLATES = (
    "During {ctx}, the {actor} may surface {obs} when {signal} precedes {artifact} on the {family} family.",
    "Reviewers correlating {ctx} with {family} timelines note {actor} activity around {signal} and {artifact}.",
    "Field telemetry from {ctx} often shows {obs} if {actor} consults storage before {signal} settles for {family}.",
    "Unlike pool-isolation-only mitigations, {ctx} analysis ties {obs} to ordering between {signal} and {artifact}.",
    "Legacy playbooks for {family} under {ctx} under-specify how {actor} interacts with {signal}; capture {artifact} spans.",
    "When {ctx} replays include {artifact}, compare {signal} ordering against {actor} traces on {family}.",
    "Histograms of {ctx} failures cluster near {obs} whenever rollup lane closure races ahead of {signal}.",
    "Parallel {ctx} sweeps expose {obs} if {actor} ignores {signal} while {artifact} is still pending on {family}.",
    "Org vocabulary maps slice lane to persistence order; during {ctx}, treat {signal} as the visibility gate before {artifact}.",
    "Audit diffs for {ctx} highlight {obs} when {actor} records {artifact} without a matching {signal} on {family}.",
)


def pick(pool: tuple[str, ...], *keys: int) -> str:
    return pool[sum(keys) % len(pool)]


def unique_paragraph(part: int, section: str, index: int) -> str:
    family = pick(FAMILIES, part, index)
    sentence_a = TEMPLATES[(part + index) % len(TEMPLATES)].format(
        ctx=pick(CONTEXTS, part, index),
        actor=pick(ACTORS, index, part),
        obs=pick(OBSERVATIONS, part, index, 3),
        signal=pick(SIGNALS, index, part, 5),
        artifact=pick(ARTIFACTS, part, index, 7),
        family=family,
    )
    sentence_b = TEMPLATES[(part + index + 3) % len(TEMPLATES)].format(
        ctx=pick(CONTEXTS, index, part, 11),
        actor=pick(ACTORS, part, index, 13),
        obs=pick(OBSERVATIONS, index, part),
        signal=pick(SIGNALS, part, index),
        artifact=pick(ARTIFACTS, index, part, 17),
        family=pick(FAMILIES, index, part, 19),
    )
    focus_title, focus_body = PARTS[part]
    sentence_c = (
        f"Part {part:02d} ({focus_title}) documents {focus_body}; "
        f"section {section} entry {index:03d} records boundary-contract constraints "
        f"for maintainers reconciling observation frame, commit frame, slice lane, "
        f"rollup lane, and post-success envelope semantics with facility audits."
    )
    return f"{sentence_a} {sentence_b} {sentence_c}"


def part_body(part: int) -> str:
    focus_title, focus_body = PARTS[part]
    lines = [
        f"<h1>Part {part:02d}: {html.escape(focus_title)}</h1>",
        f"<p>{html.escape(focus_body)}. Terminology intentionally reframes JDBC and "
        "persistence ordering for parallel chunk facilities without echoing public framework FAQs.</p>",
    ]
    for section_idx, section in enumerate(
        ("baseline", "regression", "operations", "audit", "migration", "monitoring")
    ):
        lines.append(f"<h2>{part}.{section_idx + 1} {html.escape(section.title())} notes</h2>")
        for i in range(1, 121):
            lines.append(f"<h3>{part}.{section_idx + 1}.{i:03d}</h3>")
            lines.append(f"<p>{html.escape(unique_paragraph(part, section, i))}</p>")
    return "\n".join(lines)


def example_trace(title: str, summary: str, trace_idx: int, example_idx: int) -> str:
    family = pick(FAMILIES, trace_idx, example_idx)
    opener = TEMPLATES[(trace_idx + example_idx) % len(TEMPLATES)].format(
        ctx=pick(CONTEXTS, trace_idx, example_idx),
        actor=pick(ACTORS, example_idx, trace_idx),
        obs=pick(OBSERVATIONS, trace_idx, example_idx),
        signal=pick(SIGNALS, example_idx, trace_idx),
        artifact=pick(ARTIFACTS, trace_idx, example_idx),
        family=family,
    )
    middle = (
        f"{title} documents: {summary}. Trace {trace_idx:03d} correlates lane audit rows "
        f"with {family} partition counters under concurrent workers."
    )
    closer = TEMPLATES[(trace_idx * 3 + example_idx + 5) % len(TEMPLATES)].format(
        ctx=pick(CONTEXTS, example_idx, trace_idx, 19),
        actor=pick(ACTORS, trace_idx, example_idx, 23),
        obs=pick(OBSERVATIONS, example_idx, trace_idx, 29),
        signal=pick(SIGNALS, trace_idx, example_idx, 31),
        artifact=pick(ARTIFACTS, example_idx, trace_idx, 37),
        family=pick(FAMILIES, example_idx, trace_idx, 41),
    )
    return f"{opener} {middle} {closer}"


def examples_body() -> str:
    lines = ["<h1>Worked boundary examples</h1>"]
    for ex_idx, (title, summary) in enumerate(WORKED):
        lines.append(f"<h2>{html.escape(title)}</h2>")
        lines.append(f"<p>{html.escape(summary)}.</p>")
        for trace_idx in range(1, 81):
            lines.append(f"<h3>{html.escape(title)} field note {trace_idx:03d}</h3>")
            lines.append(f"<p>{html.escape(example_trace(title, summary, trace_idx, ex_idx))}</p>")
    return "\n".join(lines)


def wrap_body(inner: str, title: str) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title></head><body>"
        + inner
        + "</body></html>"
    )


def index_html() -> str:
    links = ['<li><a href="index.html">Overview</a></li>']
    for part in sorted(PARTS):
        links.append(f'<li><a href="part_{part:02d}.html">Part {part:02d}</a></li>')
    links.append('<li><a href="examples.html">Worked examples</a></li>')
    links.append('<li><a href="glossary.md">Glossary</a></li>')
    body = (
        "<h1>Boundary contract index</h1>"
        "<p>Facility uploads must honor three partition families with independent caps. "
        "Readers and writers share a pool whose observation frame must match the "
        "production profile advertised in YAML.</p><ul>"
        + "".join(links)
        + "</ul>"
    )
    return wrap_body(body, "Boundary contract")


def glossary_md() -> str:
    terms = [
        ("Observation frame", "JDBC session semantics visible to readers within a transaction."),
        ("Commit frame", "Unit of work ending at transaction commit for one external business key."),
        ("Slice lane", "Application persistence order for header and line aggregates."),
        ("Rollup lane", "Database trigger path updating partition counters."),
        ("Post-success envelope", "Coordinator work that must not re-enter the ingest commit frame."),
    ]
    lines = ["# Glossary", ""]
    for term, definition in terms:
        lines.append(f"## {term}")
        lines.append("")
        lines.append(definition)
        lines.append("")
        for i in range(1, 41):
            family = pick(FAMILIES, i, hash(term) % 7)
            lines.append(
                f"Maintainer note {i:03d} on **{term}** ({family}): "
                + unique_paragraph(2 + (i % 5), "glossary", i)
            )
            lines.append("")
    return "\n".join(lines)


def bench_precedence_md() -> str:
    lines = [
        "# Bench precedence",
        "",
        "When operational playbooks disagree with the boundary contract corpus under "
        "`/app/docs/boundary_contract/`, the boundary contract wins.",
        "",
        "Resolution order:",
        "1. Boundary contract HTML parts and worked examples",
        "2. `operations_notes.md` (non-authoritative)",
        "3. `ingest_pipeline.md` (transport overview)",
        "",
    ]
    for i in range(1, 201):
        lines.append(f"## Precedence case {i:03d}")
        lines.append("")
        lines.append(unique_paragraph(7, "precedence", i))
        lines.append("")
    return "\n".join(lines)


def operations_notes_md() -> str:
    lines = [
        "# Operations notes",
        "",
        "Teams often bump default transaction isolation on the pool or add pessimistic "
        "locks on header repositories when parallel lane workers show drift. That can "
        "flatten flakes on single-worker replays without fixing mixed-family counters.",
        "",
        "Recommended experiments (often misleading):",
        "- Raise ORM isolation property without touching pool initializer SQL",
        "- Acquire pessimistic write locks on header repository before line inserts",
        "- Disable schema migration in staging only",
        "",
        "These changes are documented in decoy tuning advice for review only.",
        "",
    ]
    for i in range(1, 201):
        lines.append(f"## Ops rehearsal {i:03d}")
        lines.append("")
        lines.append(unique_paragraph(8, "operations", i))
        lines.append("")
    return "\n".join(lines)


def ingest_pipeline_md() -> str:
    lines = [
        "# Lane pipeline overview",
        "",
        "Workers POST JSON payloads to partition endpoints. The facility persists "
        "header and line slices, maintains rollup counters via database routines, and emits "
        "post-success coordination events.",
        "",
        "Audit harness: `/app/app/lane_audit.sh` writes `/app/output/lane_audit.json`.",
        "",
    ]
    for i in range(1, 201):
        lines.append(f"## Pipeline segment {i:03d}")
        lines.append("")
        lines.append(unique_paragraph(9, "pipeline", i))
        lines.append("")
    return "\n".join(lines)


def write_corpus() -> None:
    bc = ROOT / "boundary_contract"
    bc.mkdir(parents=True, exist_ok=True)

    (bc / "index.html").write_text(index_html(), encoding="utf-8")
    (bc / "glossary.md").write_text(glossary_md(), encoding="utf-8")
    (bc / "examples.html").write_text(
        wrap_body(examples_body(), "Worked examples"), encoding="utf-8"
    )

    for part in sorted(PARTS):
        title = PARTS[part][0]
        (bc / f"part_{part:02d}.html").write_text(
            wrap_body(part_body(part), title), encoding="utf-8"
        )

    (ROOT / "bench_precedence.md").write_text(bench_precedence_md(), encoding="utf-8")
    (ROOT / "operations_notes.md").write_text(operations_notes_md(), encoding="utf-8")
    (ROOT / "ingest_pipeline.md").write_text(ingest_pipeline_md(), encoding="utf-8")


if __name__ == "__main__":
    write_corpus()
    total = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    print(f"Wrote boundary corpus under {ROOT} ({total:,} bytes)")

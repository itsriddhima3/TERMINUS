#!/usr/bin/env python3
"""Authoring-time corpus builder. Run from repo root then delete — do not ship."""

from __future__ import annotations

import random
from pathlib import Path

OUT = (
    Path(__file__).resolve().parent.parent
    / "tasks/pg-join-statistics-correlation/environment/docs/planner_internals"
)

CHAPTER_7_3 = """
## 7.3 Correlation and column dependency

When a query applies predicates on two or more columns from the same table, the
planner multiplies their per-column selectivities unless it has evidence the
columns are not independent. For columns with functional dependency or strong
correlation—such as a logistics region identifier and its paired zone code—the
product of marginal selectivities can diverge sharply from the true joint
selectivity.

Consider a bridge table mapping facilities to zones. Each region identifier
determines a small subset of valid zone codes. Filtering on both columns with
independent statistics yields an estimated row count far below the rows the
executor eventually touches, because the planner assumes many more
combinations exist than the data allows. The cost model then skews toward
probe-heavy join implementations even when intermediate results are wide.

Symptoms in EXPLAIN output include probe-heavy joins on wide fact tables,
plan nodes whose "Plan Rows" diverge by an order of magnitude from reality on
filters that combine region and zone literals, and aggregate children whose
estimated cardinality stays at one despite multi-hundred-row counts. These
patterns often appear together on workloads documented in the correlation
registry. They do not, by themselves, identify which catalog objects are
missing—only that joint selectivity is wrong somewhere in the predicate graph.
""".strip()

CHAPTER_13_MAINT = """
# Chapter 13: Maintenance procedures for logistics replanning

Section 13.0 through 13.10 cover routine vacuum scheduling, statistics
retention, and plan invalidation hooks unrelated to join implementation
choice. Operators frequently misattribute spine latency to buffer cache or
seq_page_cost sweeps documented in chapter 8; those interventions rarely move
the fulfillment spine when registry-backed predicate groups remain uncatalogued.

## 13.11 Spine predicate cluster catalog refresh

The correlation registry lists predicate groups; entries marked for spine
participation must each carry dependency-class extended catalog objects after
any schema migration that touches region or zone columns. Partial coverage
— for example cataloguing lane/carrier pairs while omitting shipment or
inventory snapshot groups — leaves residual estimate gaps on sibling joins
even when one bridge ratio looks healthy.

Per-column sample depth on every column listed in a spine predicate group
should be raised well above the default ops bundle shipped with the schema
(commonly one hundred) before the analyze refresh pass. A single analyze
wave across dimension and fact tables in the registry is required; analyzing
only the bridge table is insufficient because the fifteen-table spine repeats
the same region/zone literal pair on fact_shipment and fact_inventory_snapshot
join paths.

After catalog objects exist and analyze completes, invalidate any prepared
handles for the spine template and rerun the plan audit harness. Acceptable
replans show hash-style drivers on the shipment-to-bridge subtree and
estimate ratios within the acceptance bands declared in the workload matrix
for both bridge and inventory snapshot nodes.

## 13.12 False positives during spine investigations

Creating extended catalog objects for non-spine registry entries (lane/carrier
pairs, carrier service tiers, or standalone facility capacity columns) does not
satisfy spine replanning requirements. Increasing work_mem or toggling
enable_nestloop may shift costs but will not repair dependency gaps on
region/zone tuples. Index additions on lane_id alone are similarly unrelated.
""".strip()

CHAPTER_8_RED_HERRING = """
Many teams attempt to fix wide join latency by raising work_mem into the
hundreds of megabytes or by lowering random_page_cost toward one. On the
fulfillment spine those changes adjust absolute costs but preserve incorrect
join implementation choices when correlated region and zone filters still
use independent selectivity. Treat buffer and cost-constant tuning as
secondary only after registry spine predicate groups pass the catalog refresh
procedure in chapter 13 section 13.11.
""".strip()

OPENERS = [
    "During early planning",
    "At execution time",
    "When cardinality estimates skew",
    "Under heavy concurrent load",
    "For wide fact tables",
    "On partitioned relations",
    "Inside prepared-statement reuse",
    "While equivalence classes merge",
    "After a major version upgrade",
    "During autovacuum-driven refresh",
    "When histogram buckets truncate",
    "If correlation stats are absent",
    "On logistics-style star schemas",
    "Within nested-loop rescans",
    "During parallel worker startup",
]

VERBS = [
    "re-evaluates", "propagates", "materializes", "invalidates", "reorders",
    "annotates", "prunes", "rescans", "prefetches", "serializes", "batches",
    "short-circuits", "rebinds", "normalizes", "recomputes", "stabilizes",
]

SUBJECTS = [
    "the path generator", "join rel caching", "clause selectivity", "index predicates",
    "bitmap page chains", "workfile spill nodes", "gather merge boundaries",
    "memoize entries", "foreign-key proofs", "partition bounds", "path target lists",
    "placeholder variables", "runtime keys", "tid scans", "incremental sort stages",
    "aggregate transition states", "window frame boundaries", "lateral subplans",
    "initplans attached to joins", "subquery pull-up artifacts",
]

OBJECTS = [
    "heap fetch cost", "startup latency", "rescan penalties", "parallel safety",
    "selectivity clamps", "default statistics targets", "extended stat kinds",
    "functional dependency proofs", "multivariate ndistinct", "mcv list overlap",
    "buffer pin churn", "shared memory quotas", "plan cache entries",
    "custom versus generic plans", "cursor sensitivity", "snapshot horizons",
]

OUTCOMES = [
    "planners may underestimate intermediate widths",
    "hash tables can resize mid-execution",
    "nestloop inner scans dominate wall time",
    "bitmap heap scans lose index-only benefits",
    "gather nodes serialize unexpectedly",
    "prepared plans fail to replan after DDL",
    "autovacuum may not advance relfrozenxid in time",
    "extended stats may remain unused until analyze",
    "join order memo can retain stale winners",
    "partial indexes may never be considered",
]

CONNECTORS = [
    "Consequently", "In practice", "By contrast", "Historically", "On PostgreSQL 15",
    "For fulfillment workloads", "When auditing EXPLAIN", "During regression triage",
    "Under default cost constants", "Without registry alignment",
]

DETAILS = [
    "review pg_statistic and pg_stats_ext before changing GUC knobs",
    "capture EXPLAIN ANALYZE output with BUFFERS on representative literals",
    "compare estimated versus actual rows at each join boundary",
    "confirm all spine tables share analyze timestamps",
    "verify dependency-class objects cover every registry tuple",
    "avoid tuning random_page_cost until selectivity is trustworthy",
    "document replan deltas in the workload matrix appendix",
    "invalidate prepared statements after catalog refresh",
    "watch for probe filters appearing only at execution",
    "ensure autovacuum is not starved on large fact tables",
]

FACETS = [
    "autovacuum freeze thresholds",
    "visibility map bits",
    "buffer access strategy rings",
    "shared buffer lookup churn",
    "backend type cache invalidation",
    "relcache entry lifetimes",
    "plan invalidation callbacks",
    "extended stats dependency graphs",
    "multivariate histogram buckets",
    "parallel leader coordination",
    "backend wait event spikes",
    "lock manager tranche pressure",
    "snapshot too old sentinels",
    "prepared plan generation counters",
    "tablespace placement hints",
]

HEADINGS = [
    "Interaction with {topic}",
    "Operational notes on {topic}",
    "Failure modes involving {topic}",
    "Cost-model implications for {topic}",
    "Catalog dependencies for {topic}",
    "Executor behavior during {topic}",
    "Statistics sensitivity in {topic}",
    "Migration checklist for {topic}",
    "Monitoring signals around {topic}",
    "Regression patterns tied to {topic}",
]

TOPIC_SHORT = {
    "buffer management": "buffer pools",
    "visibility map pruning": "visibility pruning",
    "index-only scans": "index-only access",
    "bitmap heap paths": "bitmap heap access",
    "aggregate pushdown": "aggregate pushdown",
    "window function costing": "window costing",
    "parallel gather merge": "gather merge",
    "incremental sort": "incremental sorting",
    "memoize nodes": "memoization",
    "foreign-key join removal": "FK join removal",
    "prepared statement planning": "prepared planning",
    "generic versus custom plans": "plan reuse",
    "partitionwise joins": "partitionwise joins",
    "subquery pull-up": "subquery pull-up",
    "lateral join expansion": "lateral expansion",
    "table statistics": "table stats",
    "extended statistics catalog": "extended stats",
    "join order enumeration": "join ordering",
    "join implementation tradeoffs": "join methods",
}


def paragraph(topic: str, chapter: int, part: int, rng: random.Random) -> str:
    short = TOPIC_SHORT.get(topic, topic)
    s, o, v, out, conn, det, facet = (
        rng.choice(SUBJECTS),
        rng.choice(OBJECTS),
        rng.choice(VERBS),
        rng.choice(OUTCOMES),
        rng.choice(CONNECTORS),
        rng.choice(DETAILS),
        rng.choice(FACETS),
    )
    templates = [
        (
            f"{conn} chapter {chapter}.{part} records how {s} {v} {o} while "
            f"{short} workloads run; {out}."
        ),
        (
            f"Reviewers auditing {facet} during {short} investigations noticed "
            f"{out} whenever {s} {v} {o}."
        ),
        (
            f"Unlike ad-hoc GUC sweeps, {short} work must {det} before {s} "
            f"can safely {v} {o}; otherwise {out}."
        ),
        (
            f"When {s} {v} {o}, fulfillment dashboards may show {out} even "
            f"though {short} settings appear stable."
        ),
        (
            f"Legacy playbooks for {short} rarely mention {facet}, yet "
            f"{conn.lower()} {out} once {s} begins to {v} {o}."
        ),
        (
            f"Field note {chapter}-{part:02d}: {det}; watch {facet} because "
            f"{s} may {v} {o} and trigger {out}."
        ),
        (
            f"During regression triage on {short}, compare {o} against "
            f"{facet} while confirming {s} no longer {v} stale paths."
        ),
        (
            f"Autovacuum and analyze cadence influence {short}: {out} if "
            f"{s} cannot {v} {o} under default targets."
        ),
        (
            f"Prepared-statement reuse hides {out} until {s} {v} {o}; "
            f"teams should {det} after {short} migrations."
        ),
        (
            f"Parallel workers amplify {out} when {s} {v} {o}; "
            f"{conn.lower()} capture {facet} metrics during {short} tests."
        ),
        (
            f"Histogram drift on {short} columns correlates with {out}; "
            f"inspect {s} before assuming {o} is misconfigured."
        ),
        (
            f"Index-only opportunities disappear if {out}; {det} while "
            f"evaluating {s} and {facet} together."
        ),
    ]
    return rng.choice(templates)


def comma_free(text: str) -> str:
    return text.replace(",", "")


def subsection(topic: str, chapter: int, part: int, seed: int) -> str:
    rng = random.Random(seed + part * 7919)
    heading = comma_free(rng.choice(HEADINGS).format(topic=TOPIC_SHORT.get(topic, topic)))
    lead = comma_free(paragraph(topic, chapter, part, rng))
    rng2 = random.Random(seed + part * 3571)
    follow = comma_free(paragraph(topic, chapter, part + 1000, rng2))
    return f"## {chapter}.{part} {heading}\n\n{lead}\n\n{follow}"


def section(title: str, body: str) -> str:
    return f"# {title}\n\n{body}\n"


def filler(topic: str, chapter: int, seed: int) -> str:
    blocks = [subsection(topic, chapter, part, seed ^ (hash(topic) & 0xFFFF)) for part in range(90)]
    return "\n\n".join(blocks)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    stale_chapter = OUT / "chapter_08.md"
    if stale_chapter.exists():
        stale_chapter.unlink()
    topics = [
        "buffer management",
        "visibility map pruning",
        "index-only scans",
        "bitmap heap paths",
        "aggregate pushdown",
        "window function costing",
        "parallel gather merge",
        "incremental sort",
        "memoize nodes",
        "foreign-key join removal",
        "prepared statement planning",
        "generic versus custom plans",
        "partitionwise joins",
        "subquery pull-up",
        "lateral join expansion",
    ]
    for i, topic in enumerate(topics, start=1):
        if i == 8:
            continue
        text = section(f"Chapter {i}: {topic.replace(' ', '_')}", filler(topic, i, i * 9973))
        (OUT / f"chapter_{i:02d}.md").write_text(text + "\n", encoding="utf-8")

    stats_body = filler("table statistics", 7, 7001)
    stats_body += "\n\n" + CHAPTER_7_3 + "\n\n"
    stats_body += filler("extended statistics catalog", 7, 7019)
    (OUT / "chapter_07_statistics.md").write_text(
        section("Chapter 7: Table statistics and selectivity", stats_body) + "\n",
        encoding="utf-8",
    )

    join_body = filler("join order enumeration", 8, 8003)
    join_body += "\n\n" + CHAPTER_8_RED_HERRING + "\n\n"
    join_body += filler("join implementation tradeoffs", 8, 8021)
    (OUT / "chapter_08_join_order.md").write_text(
        section("Chapter 8: Join ordering and implementation", join_body) + "\n",
        encoding="utf-8",
    )

    for j in range(9, 16):
        topic = topics[(j - 1) % len(topics)]
        text = section(f"Chapter {j}: advanced_{topic.replace(' ', '_')}", filler(topic, j, j * 9973))
        (OUT / f"chapter_{j:02d}.md").write_text(text + "\n", encoding="utf-8")

    (OUT / "chapter_13_maintenance.md").write_text(CHAPTER_13_MAINT + "\n", encoding="utf-8")

    index = [
        "# Planner internals reference index\n\n"
        "The corpus spans buffer management through lateral join expansion. "
        "Start with chapter_07_statistics.md section 7.3 for correlated "
        "predicate symptoms and chapter_13_maintenance.md section 13.11 for "
        "spine replanning procedures. Predicate groups live in "
        "/app/docs/correlation_registry.md.\n\n"
        "Chapters available under this directory include "
    ]
    names = sorted(path.stem for path in OUT.glob("chapter_*.md"))
    index.append(", ".join(names[:-1]) + f", and {names[-1]}.\n")
    (OUT / "INDEX.md").write_text("".join(index), encoding="utf-8")

    total_words = sum(len(p.read_text(encoding="utf-8").split()) for p in OUT.glob("*.md"))
    print(f"generated {len(list(OUT.glob('*.md')))} files, ~{total_words} words")


if __name__ == "__main__":
    main()

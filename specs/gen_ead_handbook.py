#!/usr/bin/env python3
"""Authoring-time corpus builder. Run from repo root — do not ship."""

from __future__ import annotations

import random
from pathlib import Path

OUT = (
    Path(__file__).resolve().parent.parent
    / "tasks/cpp-ead-authority-reconcile/environment/docs/handbook"
)

SECTION_8_4 = """
## 8.4 Dual creator precedence in controlaccess blocks

When a finding aid lists both a corporate body and a personal name within the
same `<controlaccess>` element, catalogers must treat the corporate body as the
primary creator for downstream authority reconciliation. Personal names in that
shared block are associated creators for display only and must not win when the
CLI selects a single `creator_primary` value for CSV export or API linking.

This rule applies even when the personal name appears first in document order.
Bench teams sometimes misread legacy worksheets that prioritized personal names
for photograph collections; those worksheets were superseded by the 2019
reconciliation memo. If both names resolve in the authority service, the
corporate identifier is the link target.
""".strip()

SECTION_12_2 = """
## 12.2 Subject heading normalization before authority lookup

Library of Congress Subject Headings copied from `<subject>` elements often
carry subdivision text after a double hyphen (`--`). The reconciliation CLI must
take only the heading stem before the first `--` when querying the local subject
authority tier. Do not send the full LCSH string including photographic or era
subdivisions.

Examples from the bench corpus: `College buildings--Photographs` resolves via
the stem `College buildings`; `Women authors--19th century` resolves via
`Women authors`. Subdivision text may remain in the archival export JSONL for
display, but the lookup head sent to `/api/v1/subjects/resolve` is always the
stem.
""".strip()

SECTION_15_7 = """
## 15.7 Approximate geographic headings and fuzzy tiers

Geographic names carrying an `approx` attribute on `<geogname>` require the
secondary fuzzy tier when calling the place authority service. Tier-one exact
match is reserved for headings without approximation markers. Approximate county
and regional headings frequently fail tier-one tables even when the string match
looks exact to a human reader.

Strip parenthetical qualifiers such as `(Mich.)` before tier-one lookup only.
Approximate headings must not be downgraded to tier one merely because the
approx attribute value is the literal string `approx`.
""".strip()

SECTION_14_3 = """
## 14.3 University archives accession wire form

University archives collections whose identifiers use dot segmentation (`UA.NN.NNN`)
must keep that dot form in accession validation for materials described after 1950.
Do not rewrite UA identifiers to hyphenated manuscript patterns. The bench policy
table may suggest alternate wire forms for other collection families; those defaults
do not override this section for UA materials.
""".strip()

SECTION_22_1 = """
## 22.1 Manuscript collection accession invariants

Manuscript collections identified with the `MS-` prefix must retain that prefix
and hyphen form in accession validation regardless of date span or bench policy
knobs. Converting manuscript identifiers to `MSS-` dotted variants is never valid
for accession QA even when `/app/config/bench_policy.toml` sets `ms_use_dot`.

When handbook section 22.1 conflicts with bench_policy accession defaults,
section 22.1 wins. Section 14.3 UA dot rules do not inherit this override —
bench_policy may still govern non-manuscript families.
""".strip()


def filler(seed: int, topic: str, n_paragraphs: int = 120) -> str:
    rng = random.Random(seed)
    chunks = [f"# {topic}\n"]
    for i in range(n_paragraphs):
        words = [
            "finding", "aid", "accession", "reconciliation", "authority",
            "catalog", "repository", "EAD", "controlaccess", "geogname",
            "unitdate", "curator", "workflow", "batch", "export", "compliance",
        ]
        sentence = " ".join(rng.choice(words) for _ in range(rng.randint(18, 28)))
        sentence = sentence[0].upper() + sentence[1:] + "."
        chunks.append(sentence + "\n")
    return "\n".join(chunks)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [
        ("part_01_intro.md", filler(1, "Introduction to archival reconciliation")),
        ("part_02_ead_structure.md", filler(2, "EAD structure reference")),
        ("part_03_controlaccess.md", SECTION_8_4 + "\n\n" + filler(3, "Control access patterns")),
        ("part_04_unitdate.md", filler(4, "Unitdate normalization")),
        ("part_05_subjects.md", SECTION_12_2 + "\n\n" + filler(5, "Subject heading practice")),
        ("part_06_places.md", SECTION_15_7 + "\n\n" + filler(6, "Geographic headings")),
        ("part_07_accession_ua.md", SECTION_14_3 + "\n\n" + filler(7, "UA accession practice")),
        ("part_08_accession_ms.md", SECTION_22_1 + "\n\n" + filler(8, "Manuscript accession practice")),
        ("part_09_compliance.md", filler(9, "Compliance reporting")),
        ("part_10_unresolved.md", filler(10, "Unresolved entity queues")),
        ("part_11_batch_ops.md", filler(11, "Batch operations")),
        ("part_12_api_notes.md", filler(12, "Authority API usage")),
    ]
    total = 0
    for name, body in parts:
        path = OUT / name
        path.write_text(body + "\n", encoding="utf-8")
        total += len(body)
    index = OUT / "INDEX.md"
    index.write_text(
        "# Curator handbook index\n\n"
        + "\n".join(f"- [{Path(name).stem}]({name})" for name, _ in parts)
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(parts)} parts, ~{total} chars (~{total // 4} tokens)")


if __name__ == "__main__":
    main()

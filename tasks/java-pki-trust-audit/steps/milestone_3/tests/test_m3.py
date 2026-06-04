"""Milestone 3 — Graphviz trust diagram styling."""

import subprocess
from pathlib import Path

MATRIX = Path("/app/data/cases/case_matrix.json")
CORPUS = Path("/app/output/corpus_index.json")
AUDIT = Path("/app/output/audit_results.json")
DOT = Path("/app/output/trust.dot")
SVG = Path("/app/output/trust.svg")


def _ensure_audit() -> None:
    if not CORPUS.exists():
        subprocess.run(
            ["/app/bin/trustaudit", "corpus", "--matrix", str(MATRIX)],
            check=True,
            timeout=120,
        )
    if not AUDIT.exists():
        subprocess.run(
            [
                "/app/bin/trustaudit",
                "policy",
                "--matrix",
                str(MATRIX),
                "--corpus",
                str(CORPUS),
            ],
            check=True,
            timeout=120,
        )


def _run_graph() -> str:
    _ensure_audit()
    subprocess.run(
        ["/app/bin/trustaudit", "graph", "--audit", str(AUDIT)],
        check=True,
        timeout=120,
    )
    assert DOT.is_file()
    assert SVG.is_file()
    assert SVG.stat().st_size > 500
    return DOT.read_text(encoding="utf-8")


class TestMilestone3:
    def test_dot_declares_digraph(self) -> None:
        """trust.dot begins with a digraph trust declaration."""
        dot = _run_graph()
        assert dot.lstrip().startswith("digraph trust")

    def test_valid_chain_green_fill(self) -> None:
        """Accepted path nodes use the annex light-green fillcolor."""
        dot = _run_graph()
        block = _case_block(dot, "valid_chain")
        assert 'fillcolor="#e8f5e9"' in block or "fillcolor=\"#e8f5e9\"" in block

    def test_valid_chain_forestgreen_edge(self) -> None:
        """valid_chain subgraph edges use forestgreen."""
        dot = _run_graph()
        assert "color=forestgreen" in dot or 'color="forestgreen"' in dot

    def test_expired_root_gray_dashed(self) -> None:
        """expired_root anchor node is gray with dashed style."""
        dot = _run_graph()
        block = _case_block(dot, "expired_root")
        assert "fillcolor=gray" in block or 'fillcolor="gray"' in block
        assert "style=dashed" in block or 'style="dashed"' in block

    def test_revoked_intermediate_red_pen(self) -> None:
        """revoked_intermediate styling uses red with penwidth and peripheries 2."""
        dot = _run_graph()
        block = _case_block(dot, "revoked_intermediate")
        node_line = [
            ln for ln in block.splitlines() if "bench_int_revoked_revoked_intermediate" in ln
        ][0]
        assert "color" in node_line and "red" in node_line
        assert "penwidth" in node_line and "2" in node_line
        assert "peripheries" in node_line and "2" in node_line

    def test_rejected_leaf_orange(self) -> None:
        """path_too_deep rejected leaf uses orange fillcolor and style filled."""
        dot = _run_graph()
        block = _case_block(dot, "path_too_deep")
        assert 'style="filled"' in block or "style=filled" in block
        leaf_line = [
            ln for ln in block.splitlines() if "bench_leaf_deep_path_too_deep" in ln
        ][0]
        assert "fillcolor" in leaf_line and "orange" in leaf_line

    def test_svg_references_nodes(self) -> None:
        """trust.svg is non-trivial SVG output from dot."""
        _run_graph()
        svg = SVG.read_text(encoding="utf-8")
        assert "<svg" in svg

    def test_hard_not_yet_valid_leaf_orange_node(self) -> None:
        """not_yet_valid_leaf end entity is orange filled."""
        dot = _run_graph()
        assert "bench_leaf_future_not_yet_valid_leaf" in dot
        assert 'fillcolor="orange"' in dot or "fillcolor=orange" in dot

    def test_hard_dual_crl_supersede_still_forestgreen(self) -> None:
        """dual_crl_supersede accepted path keeps forestgreen edges."""
        dot = _run_graph()
        block = _case_block(dot, "dual_crl_supersede")
        assert "color=forestgreen" in block or 'color="forestgreen"' in block


def _case_block(dot: str, case_id: str) -> str:
    lines = [ln for ln in dot.splitlines() if case_id in ln]
    return "\n".join(lines)

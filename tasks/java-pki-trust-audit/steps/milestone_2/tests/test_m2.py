"""Milestone 2 — policy evaluation against dossier rules."""

import json
import subprocess
from pathlib import Path

MATRIX = Path("/app/data/cases/case_matrix.json")
CORPUS = Path("/app/output/corpus_index.json")
AUDIT = Path("/app/output/audit_results.json")
NOVEL_CASE_ID = "verifier_alt_valid"
NOVEL_CORPUS = Path("/app/data/certs/corpus-alt-valid.pem")
NOVEL_CHAIN = ["bench-root-live", "bench-int-alt", "bench-leaf-alt"]
TRUSTAUDIT_BIN = Path("/app/bin/trustaudit")


def _ensure_corpus() -> None:
    if not CORPUS.exists():
        subprocess.run(
            ["/app/bin/trustaudit", "corpus", "--matrix", str(MATRIX)],
            check=True,
            timeout=120,
        )


def _run_policy(matrix: Path = MATRIX) -> dict:
    _ensure_corpus()
    subprocess.run(
        [
            "/app/bin/trustaudit",
            "policy",
            "--matrix",
            str(matrix),
            "--corpus",
            str(CORPUS),
        ],
        check=True,
        timeout=120,
    )
    return json.loads(AUDIT.read_text(encoding="utf-8"))


def _run_corpus(matrix: Path) -> None:
    subprocess.run(
        ["/app/bin/trustaudit", "corpus", "--matrix", str(matrix)],
        check=True,
        timeout=120,
    )


def _run_policy_with_matrix(matrix: Path) -> dict:
    _run_corpus(matrix)
    return _run_policy(matrix)


def _case(doc: dict, case_id: str) -> dict:
    for row in doc["cases"]:
        if row["case_id"] == case_id:
            return row
    raise AssertionError(f"missing case {case_id}")


class TestMilestone2:
    def test_trustaudit_invokes_java_jar(self) -> None:
        """trustaudit wrapper delegates to the packaged CLI JAR."""
        wrapper = TRUSTAUDIT_BIN.read_text(encoding="utf-8")
        assert "java -jar" in wrapper

    def test_schema_version(self) -> None:
        """audit_results.json declares schema_version 1."""
        doc = _run_policy()
        assert doc["schema_version"] == 1

    def test_valid_chain_accept(self) -> None:
        """valid_chain receives verdict accept with null reason."""
        row = _case(_run_policy(), "valid_chain")
        assert row["verdict"] == "accept"
        assert row["reason"] is None

    def test_expired_root_reject(self) -> None:
        """expired_root is reject with reason expired_root."""
        row = _case(_run_policy(), "expired_root")
        assert row["verdict"] == "reject"
        assert row["reason"] == "expired_root"

    def test_revoked_intermediate_reject(self) -> None:
        """revoked_intermediate is reject with reason revoked_intermediate."""
        row = _case(_run_policy(), "revoked_intermediate")
        assert row["verdict"] == "reject"
        assert row["reason"] == "revoked_intermediate"

    def test_path_too_deep_reject(self) -> None:
        """path_too_deep is reject with reason path_length."""
        row = _case(_run_policy(), "path_too_deep")
        assert row["verdict"] == "reject"
        assert row["reason"] == "path_length"

    def test_valid_chain_preserves_chain_cn(self) -> None:
        """valid_chain audit row carries the exact three-element chain_cn."""
        row = _case(_run_policy(), "valid_chain")
        assert row["chain_cn"] == [
            "bench-root-live",
            "bench-int-clean",
            "bench-leaf-valid",
        ]

    def test_reject_rows_carry_exact_chain(self) -> None:
        """Reject cases carry the exact expected chain_cn without extraneous CNs."""
        doc = _run_policy()
        assert _case(doc, "expired_root")["chain_cn"] == [
            "bench-root-expired",
            "bench-int-expired",
            "bench-leaf-expired",
        ]
        assert _case(doc, "revoked_intermediate")["chain_cn"] == [
            "bench-root-live",
            "bench-int-revoked",
            "bench-leaf-revoked-int",
        ]
        assert _case(doc, "path_too_deep")["chain_cn"] == [
            "bench-root-live",
            "bench-int-clean",
            "bench-int-extra",
            "bench-int-deep2",
            "bench-leaf-deep",
        ]

    def test_hard_dual_crl_supersede_accepts_despite_stale_revocation(self) -> None:
        """dual_crl_supersede accepts after newer CRL clears stale revocation."""
        row = _case(_run_policy(), "dual_crl_supersede")
        assert row["verdict"] == "accept"
        assert row["reason"] is None
        assert row["chain_cn"] == [
            "bench-root-live",
            "bench-int-clean",
            "bench-leaf-valid",
        ]

    def test_hard_expired_intermediate_reject(self) -> None:
        """expired_intermediate is reject with reason expired_intermediate."""
        row = _case(_run_policy(), "expired_intermediate")
        assert row["verdict"] == "reject"
        assert row["reason"] == "expired_intermediate"
        assert "bench-int-stale" in row["chain_cn"]

    def test_hard_not_yet_valid_leaf_reject(self) -> None:
        """not_yet_valid_leaf is reject with reason not_yet_valid."""
        row = _case(_run_policy(), "not_yet_valid_leaf")
        assert row["verdict"] == "reject"
        assert row["reason"] == "not_yet_valid"
        assert row["chain_cn"][-1] == "bench-leaf-future"

    def test_hard_missing_link_parse_fail(self) -> None:
        """missing_link is reject with reason parse_fail."""
        row = _case(_run_policy(), "missing_link")
        assert row["verdict"] == "reject"
        assert row["reason"] == "parse_fail"

    def test_pem_fork_noise_excludes_side_branches(self) -> None:
        """pem_fork_noise accepts and chain_cn contains only the issuer-walk CNs."""
        row = _case(_run_policy(), "pem_fork_noise")
        assert row["verdict"] == "accept"
        assert row["reason"] is None
        assert row["chain_cn"] == [
            "bench-root-live",
            "bench-int-clean",
            "bench-leaf-valid",
        ]

    def test_novel_case_evaluation(self, tmp_path: Path) -> None:
        """A matrix case absent from the milestone instruction is evaluated by policy logic."""
        matrix_doc = json.loads(MATRIX.read_text(encoding="utf-8"))
        matrix_doc["cases"].append(
            {
                "case_id": NOVEL_CASE_ID,
                "corpus_pem": str(NOVEL_CORPUS),
                "trust_anchor_cn": "bench-root-live",
                "leaf_cn": "bench-leaf-alt",
                "bench_path": True,
            }
        )
        matrix_path = tmp_path / "novel_matrix.json"
        matrix_path.write_text(json.dumps(matrix_doc), encoding="utf-8")
        doc = _run_policy_with_matrix(matrix_path)
        row = _case(doc, NOVEL_CASE_ID)
        assert row["verdict"] == "accept"
        assert row["reason"] is None
        assert row["chain_cn"] == NOVEL_CHAIN

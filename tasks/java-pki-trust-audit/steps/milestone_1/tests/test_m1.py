"""Milestone 1 — PEM corpus index and chain assembly."""

import json
import subprocess
from pathlib import Path

CORPUS = Path("/app/output/corpus_index.json")
MATRIX = Path("/app/data/cases/case_matrix.json")
VALID_CHAIN = ["bench-root-live", "bench-int-clean", "bench-leaf-valid"]
PATH_TOO_DEEP_CHAIN = [
    "bench-root-live",
    "bench-int-clean",
    "bench-int-extra",
    "bench-int-deep2",
    "bench-leaf-deep",
]
STEP_P4 = Path("/app/cli/src/main/java/trust/parse/step_p4.java")
TRUSTAUDIT_BIN = Path("/app/bin/trustaudit")


def _run_corpus() -> None:
    subprocess.run(
        ["/app/bin/trustaudit", "corpus", "--matrix", str(MATRIX)],
        check=True,
        timeout=120,
    )


def _load() -> dict:
    _run_corpus()
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def _case(doc: dict, case_id: str) -> dict:
    for row in doc["cases"]:
        if row["case_id"] == case_id:
            return row
    raise AssertionError(f"missing case {case_id}")


class TestMilestone1:
    def test_trustaudit_invokes_java_jar(self) -> None:
        """trustaudit wrapper delegates to the packaged CLI JAR."""
        wrapper = TRUSTAUDIT_BIN.read_text(encoding="utf-8")
        assert "java -jar" in wrapper

    def test_step_p4_no_offpath_remainder_append(self) -> None:
        """step_p4 must not append off-path certificates after the issuer walk."""
        source = STEP_P4.read_text(encoding="utf-8")
        assert "remainder" not in source, (
            "step_p4.java still contains the off-path append bug"
        )

    def test_schema_version(self) -> None:
        """corpus_index.json declares schema_version 1."""
        doc = _load()
        assert doc["schema_version"] == 1

    def test_nine_cases_present(self) -> None:
        """All nine bench case_id values appear in the corpus index."""
        doc = _load()
        ids = {c["case_id"] for c in doc["cases"]}
        assert ids == {
            "valid_chain",
            "expired_root",
            "revoked_intermediate",
            "path_too_deep",
            "dual_crl_supersede",
            "pem_fork_noise",
            "expired_intermediate",
            "not_yet_valid_leaf",
            "missing_link",
        }

    def test_valid_chain_order(self) -> None:
        """valid_chain chain_cn lists anchor through leaf in issuance order."""
        row = _case(_load(), "valid_chain")
        assert row["chain_cn"] == VALID_CHAIN

    def test_valid_chain_flags(self) -> None:
        """valid_chain has chain_ok and aki_link_ok true."""
        row = _case(_load(), "valid_chain")
        assert row["chain_ok"] is True
        assert row["aki_link_ok"] is True

    def test_expired_root_parses_anchor(self) -> None:
        """expired_root chain_cn spans the expired anchor chain and chain_ok is true."""
        row = _case(_load(), "expired_root")
        assert row["chain_cn"][0] == "bench-root-expired"
        assert row["chain_cn"][-1] == "bench-leaf-expired"
        assert row["chain_ok"] is True

    def test_revoked_intermediate_includes_revoked_int(self) -> None:
        """revoked_intermediate chain_cn follows issuer walk with chain_ok and aki_link_ok true."""
        row = _case(_load(), "revoked_intermediate")
        assert row["chain_cn"] == [
            "bench-root-live",
            "bench-int-revoked",
            "bench-leaf-revoked-int",
        ]
        assert row["chain_ok"] is True
        assert row["aki_link_ok"] is True

    def test_path_too_deep_exact_chain(self) -> None:
        """path_too_deep chain_cn is the exact issuer walk without off-path CNs."""
        row = _case(_load(), "path_too_deep")
        assert row["chain_cn"] == PATH_TOO_DEEP_CHAIN
        assert row["chain_ok"] is False
        assert row["aki_link_ok"] is True

    def test_hard_pem_fork_noise_issuer_walk_chain(self) -> None:
        """pem_fork_noise chain_cn follows the live walk and excludes alternate branch CNs."""
        row = _case(_load(), "pem_fork_noise")
        assert row["chain_cn"] == VALID_CHAIN
        assert "bench-int-alt" not in row["chain_cn"]
        assert "bench-leaf-alt" not in row["chain_cn"]
        assert row["chain_ok"] is True
        assert row["aki_link_ok"] is True

    def test_hard_missing_link_not_a_complete_walk(self) -> None:
        """missing_link marks chain_ok false and chain_cn empty when signer is absent."""
        row = _case(_load(), "missing_link")
        assert row["chain_ok"] is False
        assert row["chain_cn"] == []

    def test_dual_crl_supersede_flags(self) -> None:
        """dual_crl_supersede has a valid chain_cn, chain_ok true, and aki_link_ok true."""
        row = _case(_load(), "dual_crl_supersede")
        assert row["chain_cn"] == VALID_CHAIN
        assert row["chain_ok"] is True
        assert row["aki_link_ok"] is True

    def test_expired_intermediate_flags(self) -> None:
        """expired_intermediate assembles the stale-int chain correctly."""
        row = _case(_load(), "expired_intermediate")
        assert row["chain_cn"] == [
            "bench-root-live",
            "bench-int-stale",
            "bench-leaf-stale-int",
        ]
        assert row["chain_ok"] is True
        assert row["aki_link_ok"] is True

    def test_not_yet_valid_leaf_flags(self) -> None:
        """not_yet_valid_leaf assembles the future-leaf chain correctly."""
        row = _case(_load(), "not_yet_valid_leaf")
        assert row["chain_cn"] == [
            "bench-root-live",
            "bench-int-clean",
            "bench-leaf-future",
        ]
        assert row["chain_ok"] is True
        assert row["aki_link_ok"] is True

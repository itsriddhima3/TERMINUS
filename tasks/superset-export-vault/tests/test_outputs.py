"""Verifier for Superset export vault audit report."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
REPORT = APP / "output" / "vault_report.json"
AUDIT = APP / "scripts" / "vault_audit.sh"
MATRIX = APP / "data" / "scenario_matrix.json"


def run_checked(cmd: list[str], *, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def load_matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def run_audit() -> dict:
    (APP / "output").mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)])
    return json.loads(REPORT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


@pytest.fixture(scope="module")
def matrix() -> dict:
    return load_matrix()


def expected(report: dict, matrix: dict, scenario: str, field: str):
    spec = matrix["scenarios"][scenario]
    if field not in spec:
        pytest.skip(f"matrix row {scenario} has no {field}")
    return spec[field], report["scenarios"][scenario][field]


def test_report_schema_version(report: dict, matrix: dict) -> None:
    """Report schema_version matches the matrix header."""
    assert report["schema_version"] == matrix["schema_version"]


def test_all_scenarios_present(report: dict, matrix: dict) -> None:
    """Report includes every matrix scenario row."""
    for name in matrix["scenarios"]:
        assert name in report["scenarios"]


def test_acme_seal_no_plaintext(report: dict, matrix: dict) -> None:
    """acme_seal_clean plaintext_hits matches the matrix band."""
    exp, got = expected(report, matrix, "acme_seal_clean", "plaintext_hits")
    assert got == exp


def test_acme_seal_manifest_ok(report: dict, matrix: dict) -> None:
    """acme_seal_clean manifest_ok matches the matrix band."""
    exp, got = expected(report, matrix, "acme_seal_clean", "manifest_ok")
    assert got is exp


def test_nested_seal_no_plaintext(report: dict, matrix: dict) -> None:
    """nested_seal_clean plaintext_hits matches the matrix band."""
    exp, got = expected(report, matrix, "nested_seal_clean", "plaintext_hits")
    assert got == exp


def test_nested_seal_manifest_ok(report: dict, matrix: dict) -> None:
    """nested_seal_clean manifest_ok matches the matrix band."""
    exp, got = expected(report, matrix, "nested_seal_clean", "manifest_ok")
    assert got is exp


def test_tamper_reject(report: dict, matrix: dict) -> None:
    """tamper_reject verify_ok matches the matrix band."""
    exp, got = expected(report, matrix, "tamper_reject", "verify_ok")
    assert got is exp


def test_roundtrip_acme_digest_match(report: dict, matrix: dict) -> None:
    """roundtrip_acme digest_match matches the matrix band."""
    exp, got = expected(report, matrix, "roundtrip_acme", "digest_match")
    assert got is exp


def test_roundtrip_oauth_digest_match(report: dict, matrix: dict) -> None:
    """roundtrip_oauth digest_match matches the matrix band."""
    exp, got = expected(report, matrix, "roundtrip_oauth", "digest_match")
    assert got is exp


def test_roundtrip_acme_digests_equal(report: dict) -> None:
    """roundtrip_acme restored tarball digest equals the source fixture."""
    row = report["scenarios"]["roundtrip_acme"]
    assert row["source_digest"] == row["restored_digest"]


def test_json_array_seal_no_plaintext(report: dict, matrix: dict) -> None:
    """json_array_seal_clean plaintext_hits matches the matrix band."""
    exp, got = expected(report, matrix, "json_array_seal_clean", "plaintext_hits")
    assert got == exp


def test_json_array_seal_manifest_ok(report: dict, matrix: dict) -> None:
    """json_array_seal_clean manifest_ok matches the matrix band."""
    exp, got = expected(report, matrix, "json_array_seal_clean", "manifest_ok")
    assert got is exp


def test_yaml_replica_seal_no_plaintext(report: dict, matrix: dict) -> None:
    """yaml_replica_seal_clean plaintext_hits matches the matrix band."""
    exp, got = expected(report, matrix, "yaml_replica_seal_clean", "plaintext_hits")
    assert got == exp


def test_yaml_replica_seal_manifest_ok(report: dict, matrix: dict) -> None:
    """yaml_replica_seal_clean manifest_ok matches the matrix band."""
    exp, got = expected(report, matrix, "yaml_replica_seal_clean", "manifest_ok")
    assert got is exp


def test_cross_member_swap(report: dict, matrix: dict) -> None:
    """cross_member_swap verify_ok matches the matrix band."""
    exp, got = expected(report, matrix, "cross_member_swap", "verify_ok")
    assert got is exp


def test_metadata_digest_tamper(report: dict, matrix: dict) -> None:
    """metadata_digest_tamper verify_ok matches the matrix band."""
    exp, got = expected(report, matrix, "metadata_digest_tamper", "verify_ok")
    assert got is exp


def test_roundtrip_json_array_digest_match(report: dict, matrix: dict) -> None:
    """roundtrip_json_array digest_match matches the matrix band."""
    exp, got = expected(report, matrix, "roundtrip_json_array", "digest_match")
    assert got is exp


def test_roundtrip_json_array_digests_equal(report: dict) -> None:
    """roundtrip_json_array restored tarball digest equals the source fixture."""
    row = report["scenarios"]["roundtrip_json_array"]
    assert row["source_digest"] == row["restored_digest"]


def test_vaultctl_binary_exists() -> None:
    """Built vaultctl binary is present for audit harness."""
    assert (APP / "bin" / "vaultctl").is_file()

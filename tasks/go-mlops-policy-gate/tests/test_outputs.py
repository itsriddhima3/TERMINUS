"""Verifier for Go MLOps policy gate bench verdicts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output" / "bench_verdicts.json"
AUDIT = APP / "app" / "bench_audit.sh"
MATRIX = APP / "data" / "bench_matrix.json"


def run_checked(cmd: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def load_matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def run_audit() -> dict:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    run_checked(["bash", str(AUDIT)])
    return json.loads(OUT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report() -> dict:
    return run_audit()


@pytest.fixture(scope="module")
def matrix() -> dict:
    return load_matrix()


def row(report: dict, key: str) -> dict:
    assert key in report["cases"]
    return report["cases"][key]


def test_schema_version(report: dict) -> None:
    """Output declares schema_version 1."""
    assert report["schema_version"] == 1


def test_all_matrix_keys_present(report: dict, matrix: dict) -> None:
    """Every bench_matrix key has a verdict row."""
    for key in matrix["cases"]:
        assert key in report["cases"]


def test_cls_clean_a1_pass(report: dict) -> None:
    """cls_clean_a1 is pass with low risk_score."""
    r = row(report, "cls_clean_a1")
    assert r["verdict"] == "pass"
    assert r["risk_score"] <= 25


def test_cls_drift_b4_warn(report: dict) -> None:
    """cls_drift_b4 is warn with A1-CLS-DRIFT cite."""
    r = row(report, "cls_drift_b4")
    assert r["verdict"] == "warn"
    assert "A1-CLS-DRIFT" in r["cited_rules"]


def test_reg_exp_c2_warn(report: dict) -> None:
    """reg_exp_c2 is warn under experimental tier bands."""
    r = row(report, "reg_exp_c2")
    assert r["verdict"] == "warn"


def test_reg_core_d1_pass(report: dict) -> None:
    """reg_core_d1 passes compendium RMSE band check."""
    r = row(report, "reg_core_d1")
    assert r["verdict"] == "pass"


def test_emb_lane_e3_pass(report: dict) -> None:
    """emb_lane_e3 uses vector-lane annex and passes."""
    r = row(report, "emb_lane_e3")
    assert r["verdict"] == "pass"


def test_emb_prod_f5_fail(report: dict) -> None:
    """emb_prod_f5 fails on production tier."""
    r = row(report, "emb_prod_f5")
    assert r["verdict"] == "fail"


def test_mix_g7_cited_rules(report: dict) -> None:
    """mix_g7 warns and cites A3-REG-07 for regression sidecar."""
    r = row(report, "mix_g7")
    assert r["verdict"] == "warn"
    assert "A3-REG-07" in r["cited_rules"]


def test_hidden_h1_fail(report: dict) -> None:
    """hidden_h1 fails with classification rule cite."""
    r = row(report, "hidden_h1")
    assert r["verdict"] == "fail"
    assert "A1-CLS-02" in r["cited_rules"] or "A1-CLS-01" in r["cited_rules"]


def test_hidden_h2_risk_cap(report: dict) -> None:
    """hidden_h2 fails with risk_score at or above 85."""
    r = row(report, "hidden_h2")
    assert r["verdict"] == "fail"
    assert r["risk_score"] >= 85


def test_hidden_h3_pass(report: dict) -> None:
    """hidden_h3 passes regression ratio check."""
    r = row(report, "hidden_h3")
    assert r["verdict"] == "pass"


def test_reg_mae_warn_j6(report: dict) -> None:
    """RMSE within pass band but MAE ratio alone triggers regression warn."""
    r = row(report, "reg_mae_warn_j6")
    assert r["verdict"] == "warn"
    assert "A2-REG-04" in r["cited_rules"]
    assert r["risk_score"] == 45


def test_reg_dual_slot_m8(report: dict) -> None:
    """Both RMSE and MAE slots exceed fail ceilings with compounded risk."""
    r = row(report, "reg_dual_slot_m8")
    assert r["verdict"] == "fail"
    assert "A2-REG-03" in r["cited_rules"]
    assert r["risk_score"] == 100


def test_emb_ndcg_only_p4(report: dict) -> None:
    """Production vector lane: recall ok, ndcg in warn band — tier rule promotes warn to fail."""
    r = row(report, "emb_ndcg_only_p4")
    assert r["verdict"] == "fail"
    assert r["risk_score"] == 45


def test_emb_stg_warn_q1(report: dict) -> None:
    """Staging vector lane keeps warn when recall sits in warn band only."""
    r = row(report, "emb_stg_warn_q1")
    assert r["verdict"] == "warn"
    assert r["risk_score"] == 45


def test_reg_stg_ratio_s3(report: dict) -> None:
    """Staging tier multiplier places RMSE ratio in warn pocket with pass MAE."""
    r = row(report, "reg_stg_ratio_s3")
    assert r["verdict"] == "warn"
    assert "A2-REG-03" in r["cited_rules"]


def test_cls_f1_band_t5(report: dict) -> None:
    """Headline and calibration metrics sit exactly on pass band edges."""
    r = row(report, "cls_f1_band_t5")
    assert r["verdict"] == "pass"
    assert "A1-CLS-01" in r["cited_rules"]
    assert r["risk_score"] <= 25


def test_cls_drift_cap_u7(report: dict) -> None:
    """High calibration with tiny population shift uses drift cap not hard fail."""
    r = row(report, "cls_drift_cap_u7")
    assert r["verdict"] == "warn"
    assert "A1-CLS-DRIFT" in r["cited_rules"]


def test_reg_exp_narrow_n3(report: dict) -> None:
    """Experimental tier widens RMSE ceiling so borderline ratio still passes."""
    r = row(report, "reg_exp_narrow_n3")
    assert r["verdict"] == "pass"
    assert r["risk_score"] <= 25

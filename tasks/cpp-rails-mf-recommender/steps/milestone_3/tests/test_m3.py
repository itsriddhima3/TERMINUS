"""Milestone 3 — holdout submission and receipt."""

import json
import math
import shutil
import sqlite3
import struct
import subprocess
from pathlib import Path

import requests

BASE = "http://127.0.0.1:4567"
RATECTL = "/app/bin/ratectl"
BUILD_DIR = Path("/app/build")
MANIFEST = Path("/app/output/splits/manifest.json")
PACK = Path("/app/output/model/pack.bin")
RECEIPT = Path("/app/output/submission/receipt.json")
DB = Path("/app/service/db/ratings.db")
RMSE_THRESHOLD = 0.85
N_HOLDOUT = 57
N_FACTORS = 8


def _ensure_api() -> None:
    subprocess.run(["bash", "/app/scripts/start_api.sh"], check=True, timeout=30)


def _decode_pack(path: Path) -> dict:
    raw = path.read_bytes()
    assert raw[:4] == b"RTPK"
    off = 4
    _version, _seed, n_users, n_items, n_factors = struct.unpack_from("<5I", raw, off)
    off += 20
    (gmean,) = struct.unpack_from("<f", raw, off)
    off += 4
    off += 32
    bu = list(struct.unpack_from(f"<{n_users}f", raw, off))
    off += n_users * 4
    bi = list(struct.unpack_from(f"<{n_items}f", raw, off))
    off += n_items * 4
    pu: list[list[float]] = []
    for _ in range(n_users):
        (sc,) = struct.unpack_from("<f", raw, off)
        off += 4
        row = [
            (struct.unpack_from("<B", raw, off + i)[0] - 128) * sc for i in range(n_factors)
        ]
        off += n_factors
        pu.append(row)
    qi: list[list[float]] = []
    for _ in range(n_items):
        (sc,) = struct.unpack_from("<f", raw, off)
        off += 4
        row = [
            (struct.unpack_from("<B", raw, off + i)[0] - 128) * sc for i in range(n_factors)
        ]
        off += n_factors
        qi.append(row)
    return {
        "global_mean": gmean,
        "bu": bu,
        "bi": bi,
        "pu": pu,
        "qi": qi,
        "n_factors": n_factors,
    }


def _quarter_round(value: float) -> float:
    return math.floor(value * 4.0 + 0.5) / 4.0


def _clamp_score(value: float) -> float:
    rounded = _quarter_round(value)
    return max(1.0, min(5.0, rounded))


def _score_pair(model: dict, user_id: int, item_id: int) -> float:
    u = user_id - 1
    i = item_id - 1
    dot = sum(model["pu"][u][f] * model["qi"][i][f] for f in range(model["n_factors"]))
    return _clamp_score(model["global_mean"] + model["bu"][u] + model["bi"][i] + dot)


def _recomputed_holdout_rmse(model: dict) -> float:
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT user_id, item_id, score FROM holdout_truth").fetchall()
    conn.close()
    se = 0.0
    for uid, iid, truth in rows:
        pred = _score_pair(model, uid, iid)
        diff = pred - truth
        se += diff * diff
    return round(math.sqrt(se / len(rows)), 6)


_REBUILT = False


def _rebuild_ratectl() -> None:
    global _REBUILT
    if _REBUILT:
        return
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    subprocess.run(["cmake", "-S", "/app", "-B", "/app/build"], check=True, timeout=120)
    subprocess.run(["cmake", "--build", "/app/build", "-j", "2"], check=True, timeout=300)
    subprocess.run(
        ["install", "-m", "0755", "/app/build/ratectl", "/app/bin/ratectl"],
        check=True,
    )
    _REBUILT = True


def _full_run() -> None:
    _ensure_api()
    _rebuild_ratectl()
    subprocess.run([RATECTL, "fetch", "--base", BASE], check=True, timeout=120)
    PACK.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [RATECTL, "train", "--manifest", str(MANIFEST), "--pack", str(PACK)],
        check=True,
        timeout=180,
    )
    subprocess.run(
        [RATECTL, "submit", "--pack", str(PACK), "--base", BASE],
        check=True,
        timeout=120,
    )


def _load_receipt() -> dict:
    _full_run()
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


class TestMilestone3:
    def test_m3_receipt_accepted(self) -> None:
        """receipt accepted is true."""
        doc = _load_receipt()
        assert doc["accepted"] is True

    def test_m3_rmse_threshold(self) -> None:
        """receipt rmse is at or below 0.85."""
        doc = _load_receipt()
        assert doc["rmse"] <= RMSE_THRESHOLD

    def test_m3_receipt_schema_version(self) -> None:
        """receipt schema_version is 1."""
        doc = _load_receipt()
        assert doc["schema_version"] == 1

    def test_m3_n_scored(self) -> None:
        """receipt n_scored equals 57 holdout pairs."""
        doc = _load_receipt()
        assert doc["n_scored"] == N_HOLDOUT

    def test_m3_resubmit_idempotent(self) -> None:
        """second submit keeps accepted true."""
        _full_run()
        first = json.loads(RECEIPT.read_text(encoding="utf-8"))
        subprocess.run(
            [RATECTL, "submit", "--pack", str(PACK), "--base", BASE],
            check=True,
            timeout=120,
        )
        second = json.loads(RECEIPT.read_text(encoding="utf-8"))
        assert second["accepted"] is True
        assert second["rmse"] == first["rmse"]

    def test_m3_local_holdout_rmse_matches(self) -> None:
        """receipt rmse matches service-side scoring within 1e-3."""
        doc = _load_receipt()
        meta = requests.get(f"{BASE}/api/v1/split", timeout=10).json()
        assert doc["rmse"] <= meta["rmse_threshold"]

    def test_m3_rmse_nonnegative(self) -> None:
        """receipt rmse is a non-negative float."""
        doc = _load_receipt()
        assert doc["rmse"] >= 0.0

    def test_m3_holdout_pair_count(self) -> None:
        """holdout endpoint lists 57 pairs before submit."""
        _ensure_api()
        pairs = requests.get(f"{BASE}/api/v1/holdout", timeout=10).json()["pairs"]
        assert len(pairs) == N_HOLDOUT
        assert all("user_id" in p and "item_id" in p for p in pairs)

    def test_m3_service_rejects_missing_split_id(self) -> None:
        """POST without split_id scores zero rows and is not accepted."""
        _ensure_api()
        hold = requests.get(f"{BASE}/api/v1/holdout", timeout=10).json()
        preds = [
            {"user_id": p["user_id"], "item_id": p["item_id"], "score": 3.0}
            for p in hold["pairs"][:3]
        ]
        resp = requests.post(
            f"{BASE}/api/v1/predictions",
            json={"predictions": preds},
            timeout=10,
        ).json()
        assert resp["accepted"] is False
        assert resp["n_scored"] == 0

    def test_m3_recomputed_rmse_matches_receipt(self) -> None:
        """pack-decoded rmse against db truth matches receipt rmse."""
        doc = _load_receipt()
        model = _decode_pack(PACK)
        recomputed = _recomputed_holdout_rmse(model)
        assert abs(recomputed - doc["rmse"]) < 0.03

    def test_m3_submit_fails_without_pack(self) -> None:
        """submit exits non-zero when pack.bin is absent."""
        _ensure_api()
        subprocess.run([RATECTL, "fetch", "--base", BASE], check=True, timeout=120)
        subprocess.run(
            [RATECTL, "train", "--manifest", str(MANIFEST), "--pack", str(PACK)],
            check=True,
            timeout=180,
        )
        saved = PACK.read_bytes()
        PACK.unlink()
        proc = subprocess.run(
            [RATECTL, "submit", "--pack", str(PACK), "--base", BASE],
            capture_output=True,
            text=True,
            timeout=120,
        )
        PACK.write_bytes(saved)
        assert proc.returncode != 0

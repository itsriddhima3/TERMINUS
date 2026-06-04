"""Milestone 1 — remote training row fetch and split manifest."""

import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

BASE = "http://127.0.0.1:4567"
RATECTL = "/app/bin/ratectl"
BUILD_DIR = Path("/app/build")
OUT = Path("/app/output/splits")
MANIFEST = OUT / "manifest.json"
TRAIN = OUT / "train.jsonl"
SPLIT_ID = "bench-split-a7"
N_TRAIN = 504
DB = Path("/app/service/db/ratings.db")


def _ensure_api() -> None:
    subprocess.run(["bash", "/app/scripts/start_api.sh"], check=True, timeout=30)


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


def _fetch() -> None:
    _ensure_api()
    _rebuild_ratectl()
    if OUT.exists():
        for p in OUT.iterdir():
            p.unlink()
    else:
        OUT.mkdir(parents=True)
    subprocess.run([RATECTL, "fetch", "--base", BASE], check=True, timeout=120)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _load_manifest() -> dict:
    _fetch()
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class TestMilestone1:
    def test_m1_manifest_schema_version(self) -> None:
        """manifest.json declares schema_version 1."""
        doc = _load_manifest()
        assert doc["schema_version"] == 1

    def test_m1_split_id_matches_bench(self) -> None:
        """manifest split_id is bench-split-a7."""
        doc = _load_manifest()
        assert doc["split_id"] == SPLIT_ID

    def test_m1_train_row_count(self) -> None:
        """train.jsonl line count matches manifest n_train 504."""
        _fetch()
        doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
        lines = [ln for ln in TRAIN.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert doc["n_train"] == N_TRAIN
        assert len(lines) == N_TRAIN

    def test_m1_train_sha256_matches_body(self) -> None:
        """manifest train_sha256 matches sha256 of train.jsonl."""
        _fetch()
        doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
        body = TRAIN.read_text(encoding="utf-8")
        assert doc["train_sha256"] == _sha256_text(body)

    def test_m1_pagination_exhaust(self) -> None:
        """Fetched rows equal API n_train from split metadata."""
        import requests

        meta = requests.get(f"{BASE}/api/v1/split", timeout=10).json()
        _fetch()
        lines = [ln for ln in TRAIN.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == meta["n_train"]

    def test_m1_fetch_idempotent_checksum(self) -> None:
        """Second fetch leaves train_sha256 unchanged."""
        _fetch()
        first = json.loads(MANIFEST.read_text(encoding="utf-8"))["train_sha256"]
        subprocess.run([RATECTL, "fetch", "--base", BASE], check=True, timeout=120)
        second = json.loads(MANIFEST.read_text(encoding="utf-8"))["train_sha256"]
        assert first == second

    def test_m1_user_item_counts(self) -> None:
        """manifest records 24 users and 32 items."""
        doc = _load_manifest()
        assert doc["n_users"] == 24
        assert doc["n_items"] == 32

    def test_m1_no_holdout_leak(self) -> None:
        """train.jsonl contains no row marked holdout in the service db."""
        _fetch()
        holdout = set()
        conn = sqlite3.connect(DB)
        for uid, iid in conn.execute(
            "SELECT user_id, item_id FROM ratings WHERE is_holdout = 1",
        ):
            holdout.add((uid, iid))
        conn.close()
        for line in TRAIN.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            assert (row["user_id"], row["item_id"]) not in holdout

    def test_m1_manifest_fit_hyperparams(self) -> None:
        """manifest copies fit_seed 42, fit_epochs 30, n_factors 8 from split."""
        doc = _load_manifest()
        assert doc["fit_seed"] == 42
        assert doc["fit_epochs"] == 30
        assert doc["n_factors"] == 8
        assert abs(doc["lr_base"] - 0.02) < 1e-6
        assert abs(doc["lr_decay"] - 0.05) < 1e-6

    def test_m1_lane_ceiling_thirty(self) -> None:
        """manual pagination ceiling for 504 rows at width 17 is 30 lanes."""
        import requests

        meta = requests.get(f"{BASE}/api/v1/split", timeout=10).json()
        per_page = meta["per_page"]
        ceiling = (meta["n_train"] + per_page - 1) // per_page
        assert ceiling == 30
        _fetch()
        lines = [ln for ln in TRAIN.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == meta["n_train"]

    def test_m1_manual_pagination_parity(self) -> None:
        """train.jsonl multiset matches manually paginated API pulls."""
        import requests

        _fetch()
        meta = requests.get(f"{BASE}/api/v1/split", timeout=10).json()
        per_page = meta["per_page"]
        total_pages = (meta["n_train"] + per_page - 1) // per_page
        manual: list[tuple[int, int, float]] = []
        for page in range(1, total_pages + 1):
            doc = requests.get(
                f"{BASE}/api/v1/train_ratings",
                params={"page": page, "per_page": per_page},
                timeout=10,
            ).json()
            for row in doc["ratings"]:
                manual.append((row["user_id"], row["item_id"], row["score"]))
        cli: list[tuple[int, int, float]] = []
        for line in TRAIN.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cli.append((row["user_id"], row["item_id"], row["score"]))
        assert sorted(manual) == sorted(cli)

    def test_m1_unique_pair_cardinality(self) -> None:
        """504 jsonl rows are 504 distinct user/item pairs."""
        _fetch()
        pairs = set()
        for line in TRAIN.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = (row["user_id"], row["item_id"])
            assert key not in pairs
            pairs.add(key)
        assert len(pairs) == N_TRAIN

    def test_m1_train_score_bounds(self) -> None:
        """every cached training star value lies between 1 and 5 inclusive."""
        _fetch()
        for line in TRAIN.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            score = json.loads(line)["score"]
            assert 1.0 <= score <= 5.0

"""Milestone 2 — seeded fit and pack artifact."""

import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path

BASE = "http://127.0.0.1:4567"
RATECTL = "/app/bin/ratectl"
BUILD_DIR = Path("/app/build")
MANIFEST = Path("/app/output/splits/manifest.json")
TRAIN = Path("/app/output/splits/train.jsonl")
PACK = Path("/app/output/model/pack.bin")
FIT_SEED = 42
N_FACTORS = 8


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


def _pipeline() -> None:
    _ensure_api()
    _rebuild_ratectl()
    subprocess.run([RATECTL, "fetch", "--base", BASE], check=True, timeout=120)
    PACK.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [RATECTL, "train", "--manifest", str(MANIFEST), "--pack", str(PACK)],
        check=True,
        timeout=180,
    )


def _read_header() -> dict:
    raw = PACK.read_bytes()
    assert raw[:4] == b"RTPK"
    off = 4
    version, seed, n_users, n_items, n_factors = struct.unpack_from("<5I", raw, off)
    off += 20
    (gmean,) = struct.unpack_from("<f", raw, off)
    off += 4
    train_sha = raw[off : off + 32].decode("ascii")
    off += 32
    return {
        "version": version,
        "seed": seed,
        "n_users": n_users,
        "n_items": n_items,
        "n_factors": n_factors,
        "global_mean": gmean,
        "train_sha256": train_sha,
        "raw": raw,
    }


def _pack_fingerprint() -> str:
    return hashlib.sha256(PACK.read_bytes()).hexdigest()


def _train_mean() -> float:
    vals = []
    for line in TRAIN.read_text(encoding="utf-8").splitlines():
        if line.strip():
            vals.append(json.loads(line)["score"])
    return sum(vals) / len(vals)


def _expected_pack_size(n_users: int, n_items: int, n_factors: int) -> int:
    header = 4 + 20 + 4 + 32
    biases = (n_users + n_items) * 4
    user_blocks = n_users * (4 + n_factors)
    item_blocks = n_items * (4 + n_factors)
    return header + biases + user_blocks + item_blocks


def _user_row_scales(raw: bytes, hdr: dict) -> list[float]:
    off = 60 + hdr["n_users"] * 4 + hdr["n_items"] * 4
    scales: list[float] = []
    for _ in range(hdr["n_users"]):
        (sc,) = struct.unpack_from("<f", raw, off)
        scales.append(sc)
        off += 4 + hdr["n_factors"]
    return scales


def _first_item_scale_offset(hdr: dict) -> int:
    return 60 + hdr["n_users"] * 4 + hdr["n_items"] * 4 + hdr["n_users"] * (4 + hdr["n_factors"])


class TestMilestone2:
    def test_m2_pack_magic_version(self) -> None:
        """pack.bin starts with RTPK magic and version 1."""
        _pipeline()
        hdr = _read_header()
        assert hdr["version"] == 1

    def test_m2_header_seed(self) -> None:
        """pack header seed is 42."""
        _pipeline()
        assert _read_header()["seed"] == FIT_SEED

    def test_m2_train_sha256_match(self) -> None:
        """pack header train_sha256 prefix matches manifest."""
        _pipeline()
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        hdr = _read_header()
        assert hdr["train_sha256"] == man["train_sha256"][:32]

    def test_m2_global_mean(self) -> None:
        """pack global mean is close to train.jsonl mean."""
        _pipeline()
        hdr = _read_header()
        tm = _train_mean()
        assert abs(hdr["global_mean"] - tm) < 0.15

    def test_m2_pack_fingerprint_stable(self) -> None:
        """Re-training yields identical pack fingerprint."""
        _pipeline()
        first = _pack_fingerprint()
        subprocess.run(
            [RATECTL, "train", "--manifest", str(MANIFEST), "--pack", str(PACK)],
            check=True,
            timeout=180,
        )
        assert _pack_fingerprint() == first

    def test_m2_latent_dim(self) -> None:
        """pack header n_factors is 8."""
        _pipeline()
        assert _read_header()["n_factors"] == N_FACTORS

    def test_m2_dequant_dot_sanity(self) -> None:
        """dequantized first user/item dot is finite and non-zero."""
        _pipeline()
        raw = PACK.read_bytes()
        hdr = _read_header()
        off = 60 + hdr["n_users"] * 4 + hdr["n_items"] * 4
        sc_u, = struct.unpack_from("<f", raw, off)
        off += 4
        pu = [
            (struct.unpack_from("<B", raw, off + i)[0] - 128) * sc_u for i in range(N_FACTORS)
        ]
        off += hdr["n_users"] * (4 + N_FACTORS)
        sc_i, = struct.unpack_from("<f", raw, off)
        off += 4
        qi = [
            (struct.unpack_from("<B", raw, off + i)[0] - 128) * sc_i for i in range(N_FACTORS)
        ]
        dot = sum(a * b for a, b in zip(pu, qi, strict=True))
        assert dot != 0.0
        assert all(abs(v) < 5 for v in pu + qi)

    def test_m2_bias_nonzero(self) -> None:
        """pack stores non-zero bias vectors."""
        _pipeline()
        raw = PACK.read_bytes()
        off = 4 + 20 + 4 + 32
        bu = struct.unpack_from(f"<{24}f", raw, off)
        off += 24 * 4
        bi = struct.unpack_from(f"<{32}f", raw, off)
        assert any(abs(v) > 1e-4 for v in bu)
        assert any(abs(v) > 1e-4 for v in bi)

    def test_m2_pack_on_disk_size(self) -> None:
        """pack byte length matches catalog row-block layout formula."""
        _pipeline()
        hdr = _read_header()
        expected = _expected_pack_size(hdr["n_users"], hdr["n_items"], hdr["n_factors"])
        assert len(PACK.read_bytes()) == expected

    def test_m2_distinct_user_quant_scales(self) -> None:
        """at least two user row scales differ (not one global scale)."""
        _pipeline()
        raw = PACK.read_bytes()
        hdr = _read_header()
        scales = _user_row_scales(raw, hdr)
        rounded = {round(s, 8) for s in scales}
        assert len(rounded) >= 2

    def test_m2_item_block_base_offset(self) -> None:
        """first item scale float sits after all user row blocks."""
        _pipeline()
        raw = PACK.read_bytes()
        hdr = _read_header()
        off = _first_item_scale_offset(hdr)
        (item_scale,) = struct.unpack_from("<f", raw, off)
        user_scales = _user_row_scales(raw, hdr)
        assert item_scale > 0.0
        assert off + 4 + hdr["n_factors"] <= len(raw)
        assert item_scale not in user_scales or len(user_scales) > 1

    def test_m2_wire_offset_bytes_present(self) -> None:
        """latent wire bytes use offset-binary band (many bytes differ from raw int8 cast)."""
        _pipeline()
        raw = PACK.read_bytes()
        hdr = _read_header()
        off = 60 + hdr["n_users"] * 4 + hdr["n_items"] * 4
        wire_bytes: list[int] = []
        for _ in range(hdr["n_users"]):
            off += 4
            for _ in range(hdr["n_factors"]):
                wire_bytes.append(raw[off])
                off += 1
        assert any(b >= 128 for b in wire_bytes)
        assert len({b for b in wire_bytes}) > 4

    def test_m2_header_seed_from_manifest(self) -> None:
        """pack header seed matches manifest fit_seed not a stale literal."""
        _pipeline()
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert _read_header()["seed"] == man["fit_seed"]

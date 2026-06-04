#!/usr/bin/env python3
"""Generate deterministic bench PEM corpora and CRL fixtures via openssl."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CERT_DIR = ROOT / "data" / "certs"
CRL_DIR = ROOT / "data" / "crls"

# Matrix eval_instant is 20240615120000Z — issue the live bench tree under datefudge.
BENCH_EPOCH = "2023-06-01"
FUTURE_LEAF_EPOCH = "2025-01-01"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, check=True, cwd=cwd, capture_output=True, text=True)


def run_datefudge(date: str, cmd: list[str]) -> None:
    try:
        run(["datefudge", date] + cmd)
    except (FileNotFoundError, subprocess.CalledProcessError):
        run(cmd)


def _gen_expired_root() -> None:
    key = CERT_DIR / "bench-root-expired.key.pem"
    cert = CERT_DIR / "bench-root-expired.pem"
    cmd = [
        "openssl",
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-keyout",
        str(key),
        "-out",
        str(cert),
        "-days",
        "30",
        "-subj",
        "/CN=bench-root-expired",
        "-addext",
        "subjectKeyIdentifier=hash",
        "-addext",
        "basicConstraints=critical,CA:true",
    ]
    run_datefudge("2020-01-15", cmd)


def gen_ca(name: str, days: int, out: Path, *, fudge_date: str | None = None) -> None:
    key = out / f"{name}.key.pem"
    cmd = [
        "openssl",
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-keyout",
        str(key),
        "-out",
        str(out / f"{name}.pem"),
        "-days",
        str(days),
        "-subj",
        f"/CN={name}",
        "-addext",
        "subjectKeyIdentifier=hash",
        "-addext",
        "basicConstraints=critical,CA:true",
    ]
    if fudge_date:
        run_datefudge(fudge_date, cmd)
    else:
        run(cmd)


def gen_signed(
    name: str,
    issuer_name: str,
    issuer_dir: Path,
    days: int,
    ca: bool,
    out: Path,
    *,
    fudge_date: str | None = None,
) -> None:
    csr = out / f"{name}.csr.pem"
    key_cmd = [
        "openssl",
        "req",
        "-new",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-keyout",
        str(out / f"{name}.key.pem"),
        "-out",
        str(csr),
        "-subj",
        f"/CN={name}",
    ]
    ext = ["subjectKeyIdentifier=hash", "authorityKeyIdentifier=keyid"]
    if ca:
        ext.append("basicConstraints=critical,CA:true")
    ext_file = out / f"{name}.ext"
    ext_file.write_text("\n".join(ext) + "\n", encoding="utf-8")
    sign_cmd = [
        "openssl",
        "x509",
        "-req",
        "-in",
        str(csr),
        "-CA",
        str(issuer_dir / f"{issuer_name}.pem"),
        "-CAkey",
        str(issuer_dir / f"{issuer_name}.key.pem"),
        "-CAcreateserial",
        "-out",
        str(out / f"{name}.pem"),
        "-days",
        str(days),
        "-extfile",
        str(ext_file),
    ]
    if fudge_date:
        run_datefudge(fudge_date, key_cmd)
        run_datefudge(fudge_date, sign_cmd)
    else:
        run(key_cmd)
        run(sign_cmd)


def _crl_config(db: Path, issuer: str) -> Path:
    cfg = db.parent / "openssl.cnf"
    cfg.write_text(
        f"""[ca]
default_ca = CA_default
[CA_default]
database = {db}
certificate = {CERT_DIR}/{issuer}.pem
private_key = {CERT_DIR}/{issuer}.key.pem
default_crl_days = 30
default_md = sha256
crl_extensions = crl_ext
[crl_ext]
authorityKeyIdentifier=keyid:always
""",
        encoding="utf-8",
    )
    return cfg


def gen_crl(issuer: str, revoked_cert: Path, out: Path, *, fudge_date: str | None = None) -> None:
    """Emit PEM CRL revoking the given certificate."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        db = tdp / "index.txt"
        db.write_text("", encoding="utf-8")
        (tdp / "index.txt.attr").write_text("unique_subject = no\n", encoding="utf-8")
        cfg = _crl_config(db, issuer)
        revoke = [
            "openssl",
            "ca",
            "-config",
            str(cfg),
            "-revoke",
            str(revoked_cert),
        ]
        publish = [
            "openssl",
            "ca",
            "-config",
            str(cfg),
            "-gencrl",
            "-crldays",
            "30",
            "-out",
            str(out),
        ]
        if fudge_date:
            run_datefudge(fudge_date, revoke)
            run_datefudge(fudge_date, publish)
        else:
            run(revoke)
            run(publish)


def gen_crl_empty(issuer: str, out: Path, *, fudge_date: str | None = None) -> None:
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        db = tdp / "index.txt"
        db.write_text("", encoding="utf-8")
        (tdp / "index.txt.attr").write_text("unique_subject = no\n", encoding="utf-8")
        cfg = _crl_config(db, issuer)
        publish = [
            "openssl",
            "ca",
            "-config",
            str(cfg),
            "-gencrl",
            "-crldays",
            "30",
            "-out",
            str(out),
        ]
        if fudge_date:
            run_datefudge(fudge_date, publish)
        else:
            run(publish)


def concat_pem(parts: list[Path], dest: Path) -> None:
    dest.write_text("".join(p.read_text(encoding="utf-8") for p in parts), encoding="utf-8")


def main() -> None:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    CRL_DIR.mkdir(parents=True, exist_ok=True)

    _gen_expired_root()
    gen_ca(
        "bench-root-live",
        3650,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-int-revoked",
        "bench-root-live",
        CERT_DIR,
        800,
        True,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-int-clean",
        "bench-root-live",
        CERT_DIR,
        800,
        True,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-leaf-valid",
        "bench-int-clean",
        CERT_DIR,
        400,
        False,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-int-extra",
        "bench-int-clean",
        CERT_DIR,
        400,
        True,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-int-deep2",
        "bench-int-extra",
        CERT_DIR,
        400,
        True,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-leaf-deep",
        "bench-int-deep2",
        CERT_DIR,
        400,
        False,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-leaf-revoked-int",
        "bench-int-revoked",
        CERT_DIR,
        400,
        False,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-int-expired",
        "bench-root-expired",
        CERT_DIR,
        400,
        True,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-leaf-expired",
        "bench-int-expired",
        CERT_DIR,
        400,
        False,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-int-alt",
        "bench-root-live",
        CERT_DIR,
        800,
        True,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )
    gen_signed(
        "bench-leaf-alt",
        "bench-int-alt",
        CERT_DIR,
        400,
        False,
        CERT_DIR,
        fudge_date=BENCH_EPOCH,
    )

    run_datefudge(
        "2019-06-01",
        [
            "openssl",
            "req",
            "-new",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(CERT_DIR / "bench-int-stale.key.pem"),
            "-out",
            str(CERT_DIR / "bench-int-stale.csr.pem"),
            "-subj",
            "/CN=bench-int-stale",
        ],
    )
    ext_stale = CERT_DIR / "bench-int-stale.ext"
    ext_stale.write_text(
        "subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid\n"
        "basicConstraints=critical,CA:true\n",
        encoding="utf-8",
    )
    run_datefudge(
        "2019-06-01",
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            str(CERT_DIR / "bench-int-stale.csr.pem"),
            "-CA",
            str(CERT_DIR / "bench-root-live.pem"),
            "-CAkey",
            str(CERT_DIR / "bench-root-live.key.pem"),
            "-CAcreateserial",
            "-out",
            str(CERT_DIR / "bench-int-stale.pem"),
            "-days",
            "90",
            "-extfile",
            str(ext_stale),
        ],
    )
    run_datefudge(
        "2019-07-01",
        [
            "openssl",
            "req",
            "-new",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(CERT_DIR / "bench-leaf-stale-int.key.pem"),
            "-out",
            str(CERT_DIR / "bench-leaf-stale-int.csr.pem"),
            "-subj",
            "/CN=bench-leaf-stale-int",
        ],
    )
    ext_leaf_stale = CERT_DIR / "bench-leaf-stale-int.ext"
    ext_leaf_stale.write_text(
        "subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid\n", encoding="utf-8"
    )
    run_datefudge(
        "2019-07-01",
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            str(CERT_DIR / "bench-leaf-stale-int.csr.pem"),
            "-CA",
            str(CERT_DIR / "bench-int-stale.pem"),
            "-CAkey",
            str(CERT_DIR / "bench-int-stale.key.pem"),
            "-CAcreateserial",
            "-out",
            str(CERT_DIR / "bench-leaf-stale-int.pem"),
            "-days",
            "60",
            "-extfile",
            str(ext_leaf_stale),
        ],
    )

    gen_signed(
        "bench-leaf-future",
        "bench-int-clean",
        CERT_DIR,
        400,
        False,
        CERT_DIR,
        fudge_date=FUTURE_LEAF_EPOCH,
    )

    gen_crl(
        "bench-root-live",
        CERT_DIR / "bench-int-revoked.pem",
        CRL_DIR / "bench-int-revoked-v1.crl",
    )
    gen_crl(
        "bench-root-live",
        CERT_DIR / "bench-int-clean.pem",
        CRL_DIR / "bench-int-clean-crl-2023.crl",
        fudge_date="2023-01-10",
    )
    gen_crl_empty(
        "bench-root-live",
        CRL_DIR / "bench-int-clean-crl-2024.crl",
        fudge_date="2024-06-01",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-int-clean.pem",
            CERT_DIR / "bench-leaf-valid.pem",
        ],
        CERT_DIR / "corpus-valid.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-expired.pem",
            CERT_DIR / "bench-int-expired.pem",
            CERT_DIR / "bench-leaf-expired.pem",
        ],
        CERT_DIR / "corpus-expired-root.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-int-revoked.pem",
            CERT_DIR / "bench-leaf-revoked-int.pem",
        ],
        CERT_DIR / "corpus-revoked-int.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-int-clean.pem",
            CERT_DIR / "bench-int-extra.pem",
            CERT_DIR / "bench-int-deep2.pem",
            CERT_DIR / "bench-leaf-deep.pem",
        ],
        CERT_DIR / "corpus-deep.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-int-clean.pem",
            CERT_DIR / "bench-leaf-valid.pem",
            CERT_DIR / "bench-int-alt.pem",
            CERT_DIR / "bench-leaf-alt.pem",
        ],
        CERT_DIR / "corpus-fork-noise.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-leaf-valid.pem",
        ],
        CERT_DIR / "corpus-missing-link.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-int-clean.pem",
            CERT_DIR / "bench-leaf-valid.pem",
        ],
        CERT_DIR / "corpus-dual-crl.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-int-stale.pem",
            CERT_DIR / "bench-leaf-stale-int.pem",
        ],
        CERT_DIR / "corpus-expired-intermediate.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-int-clean.pem",
            CERT_DIR / "bench-leaf-future.pem",
        ],
        CERT_DIR / "corpus-not-yet-valid.pem",
    )
    concat_pem(
        [
            CERT_DIR / "bench-root-live.pem",
            CERT_DIR / "bench-int-alt.pem",
            CERT_DIR / "bench-leaf-alt.pem",
        ],
        CERT_DIR / "corpus-alt-valid.pem",
    )
    print("bench certs and CRLs written")


if __name__ == "__main__":
    main()

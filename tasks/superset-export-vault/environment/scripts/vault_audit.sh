#!/bin/bash
set -euo pipefail

KEY="/app/keys/test_master.key"
CTL="/app/bin/vaultctl"
OUT="/app/output"
WORK="/app/work"
CATALOG="/app/data/fixture_catalog.json"
MATRIX="/app/data/scenario_matrix.json"

mkdir -p "$OUT" "$WORK"
bash /app/scripts/build.sh

python3 - <<'PY'
import hashlib
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path

key = Path("/app/keys/test_master.key")
ctl = Path("/app/bin/vaultctl")
out = Path("/app/output")
work = Path("/app/work")
catalog = json.loads(Path("/app/data/fixture_catalog.json").read_text())
matrix = json.loads(Path("/app/data/scenario_matrix.json").read_text())

ENC = re.compile(r"ENC:v1:[A-Za-z0-9+/=]+")


def run(cmd):
    subprocess.run(cmd, check=True, text=True, capture_output=True)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plaintext_hits(path: Path, needles: list[str]) -> int:
    count = 0
    with tarfile.open(path, "r:gz") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            text = tf.extractfile(member).read().decode("utf-8", errors="replace")
            for needle in needles:
                if needle in text:
                    count += 1
    return count


def rewrite_tar(src: Path, dst: Path, mutator):
    buf = io.BytesIO()
    with tarfile.open(src, "r:gz") as src_tf:
        with tarfile.open(fileobj=buf, mode="w:gz") as dst_tf:
            for member in src_tf.getmembers():
                data = src_tf.extractfile(member).read()
                if member.isfile():
                    data = mutator(member.name, data)
                info = tarfile.TarInfo(name=member.name)
                info.size = len(data)
                info.mtime = 0
                info.mode = 0o644
                dst_tf.addfile(info, io.BytesIO(data))
    dst.write_bytes(buf.getvalue())


def tamper_intra_member_swap(member_name: str, data: bytes) -> bytes:
    if member_name != "metadata/databases.yaml":
        return data
    tokens = ENC.findall(data.decode("utf-8"))
    if len(tokens) < 2:
        return data
    swapped = data.decode("utf-8").replace(tokens[0], "TMP_SWAP", 1)
    swapped = swapped.replace(tokens[1], tokens[0], 1)
    swapped = swapped.replace("TMP_SWAP", tokens[1], 1)
    return swapped.encode("utf-8")


def tamper_cross_member_swap(member_name: str, data: bytes, *, token_a: str, token_b: str) -> bytes:
    text = data.decode("utf-8")
    if member_name == "metadata/databases.yaml" and token_a in text:
        return text.replace(token_a, token_b, 1).encode("utf-8")
    if member_name == "metadata/providers.json" and token_b in text:
        return text.replace(token_b, token_a, 1).encode("utf-8")
    return data


def tamper_metadata_append(member_name: str, data: bytes) -> bytes:
    if not member_name.startswith("metadata/"):
        return data
    if member_name.endswith((".yaml", ".yml", ".json")):
        return data + b"\n# audit-marker\n"
    return data


def build_tampered(sealed: Path, tampered: Path, mode: str) -> None:
    if mode == "intra_member_swap":
        rewrite_tar(sealed, tampered, tamper_intra_member_swap)
        return
    if mode == "cross_member_swap":
        with tarfile.open(sealed, "r:gz") as tf:
            db_data = tf.extractfile("metadata/databases.yaml").read().decode("utf-8")
            prov_data = tf.extractfile("metadata/providers.json").read().decode("utf-8")
        db_tokens = ENC.findall(db_data)
        prov_tokens = ENC.findall(prov_data)
        if not db_tokens or not prov_tokens:
            raise RuntimeError("cross_member_swap fixture missing ENC tokens")
        token_a = db_tokens[0]
        token_b = prov_tokens[0]

        def mutator(member_name, data):
            return tamper_cross_member_swap(member_name, data, token_a=token_a, token_b=token_b)

        rewrite_tar(sealed, tampered, mutator)
        return
    if mode == "metadata_append":
        rewrite_tar(sealed, tampered, tamper_metadata_append)
        return
    raise RuntimeError(f"unknown tamper mode: {mode}")


report = {"schema_version": 1, "scenarios": {}}

for name, spec in matrix["scenarios"].items():
    fixture_key = spec["fixture"]
    src = Path(catalog["fixtures"][fixture_key])
    needles = catalog["needles"][fixture_key]
    sealed = work / f"{name}_sealed.tgz"
    restored = work / f"{name}_restored.tgz"
    run([str(ctl), "seal", "--key-file", str(key), "--in", str(src), "--out", str(sealed)])

    if "plaintext_hits" in spec:
        hits = plaintext_hits(sealed, needles)
        manifest_ok = False
        try:
            run([str(ctl), "verify", "--key-file", str(key), "--bundle", str(sealed)])
            manifest_ok = True
        except subprocess.CalledProcessError:
            manifest_ok = False
        report["scenarios"][name] = {
            "plaintext_hits": hits,
            "manifest_ok": manifest_ok,
        }
    elif "tamper" in spec:
        tampered = work / f"{name}_tampered.tgz"
        build_tampered(sealed, tampered, spec["tamper"])
        verify_ok = True
        try:
            run([str(ctl), "verify", "--key-file", str(key), "--bundle", str(tampered)])
        except subprocess.CalledProcessError:
            verify_ok = False
        report["scenarios"][name] = {"verify_ok": verify_ok}
    elif "digest_match" in spec:
        run([str(ctl), "decrypt", "--key-file", str(key), "--bundle", str(sealed), "--out", str(restored)])
        match = sha256_file(src) == sha256_file(restored)
        report["scenarios"][name] = {
            "digest_match": match,
            "source_digest": sha256_file(src),
            "restored_digest": sha256_file(restored),
        }

(out / "vault_report.json").write_text(json.dumps(report, indent=2) + "\n")

failed = False
for name, spec in matrix["scenarios"].items():
    row = report["scenarios"][name]
    if "plaintext_hits" in spec and row.get("plaintext_hits") != spec["plaintext_hits"]:
        failed = True
    if "manifest_ok" in spec and row.get("manifest_ok") is not spec["manifest_ok"]:
        failed = True
    if "verify_ok" in spec and row.get("verify_ok") is not spec["verify_ok"]:
        failed = True
    if spec.get("digest_match") is True and row.get("digest_match") is not True:
        failed = True

if failed:
    raise SystemExit(1)
PY

#!/bin/bash
set -euo pipefail

python3 <<'PY'
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path("/app/cases")


def mk_name(cn: str):
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])


def sign_cert(
    subject_cn,
    issuer_name,
    issuer_key,
    subject_key,
    days_start,
    days_end,
    serial,
    *,
    is_ca=False,
    path_length=None,
):
    now = datetime.now(timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(mk_name(subject_cn))
        .issuer_name(issuer_name)
        .public_key(subject_key.public_key())
        .serial_number(serial)
        .not_valid_before(now + timedelta(days=days_start))
        .not_valid_after(now + timedelta(days=days_end))
        .add_extension(
            x509.BasicConstraints(ca=is_ca, path_length=path_length),
            critical=True,
        )
    )
    cert = builder.sign(issuer_key, hashes.SHA256())
    return cert


def write_pem(path: Path, cert, key):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
        + key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )


def gen_root(pack_dir, cn="anchor-root"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = mk_name(cn)
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now - timedelta(days=30))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
        .sign(key, hashes.SHA256())
    )
    write_pem(pack_dir / "certs/root.pem", cert, key)
    return cert, key, name


def gen_intermediate(pack_dir, root_cert, root_key, root_name, cn="intermediate-ca"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = sign_cert(cn, root_name, root_key, key, -20, 1800, 2, is_ca=True, path_length=0)
    write_pem(pack_dir / "certs/intermediate.pem", cert, key)
    return cert, key, mk_name(cn)


def gen_leaf(pack_dir, filename, issuer_name, issuer_key, cn, days_start, days_end, serial):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = sign_cert(cn, issuer_name, issuer_key, key, days_start, days_end, serial)
    write_pem(pack_dir / ("certs/" + filename), cert, key)
    return cert, key


# alpha: valid svc_b chain + revoked leaf on deny ledger
alpha = ROOT / "alpha"
root_cert, root_key, root_name = gen_root(alpha)
inter_cert, inter_key, inter_name = gen_intermediate(alpha, root_cert, root_key, root_name)
gen_leaf(alpha, "leaf.pem", inter_name, inter_key, "svc-b-leaf", -10, 365, 10)
gen_leaf(alpha, "revoked.pem", inter_name, inter_key, "svc-a-revoked", -10, 365, 11)

# beta: leaf not yet valid
beta = ROOT / "beta"
root_cert, root_key, root_name = gen_root(beta)
gen_leaf(beta, "leaf.pem", root_name, root_key, "beta-preopen", 3650, 4000, 20)

# gamma: leaf signed by mismatched issuer credential
gamma = ROOT / "gamma"
root_cert, root_key, root_name = gen_root(gamma)
rogue = rsa.generate_private_key(public_exponent=65537, key_size=2048)
rogue_name = mk_name("rogue-signer")
cert = sign_cert("gamma-broken", rogue_name, rogue, rogue, -5, 365, 30)
write_pem(gamma / "certs/broken_leaf.pem", cert, rogue)

# delta: good three-level chain
delta = ROOT / "delta"
root_cert, root_key, root_name = gen_root(delta)
inter_cert, inter_key, inter_name = gen_intermediate(delta, root_cert, root_key, root_name)
gen_leaf(delta, "leaf.pem", inter_name, inter_key, "delta-leaf", -15, 800, 40)

# epsilon: anchor only (root is also service row)
epsilon = ROOT / "epsilon"
gen_root(epsilon, cn="epsilon-anchor")

# iota: serves hop from row to credential node, then trusts chain
iota = ROOT / "iota"
root_cert, root_key, root_name = gen_root(iota)
inter_cert, inter_key, inter_name = gen_intermediate(iota, root_cert, root_key, root_name)
gen_leaf(iota, "leaf.pem", inter_name, inter_key, "iota-leaf", -12, 500, 55)

# zeta: expired leaf
zeta = ROOT / "zeta"
root_cert, root_key, root_name = gen_root(zeta)
gen_leaf(zeta, "leaf.pem", root_name, root_key, "zeta-expired", -400, -30, 60)

print("regen_cases: wrote PEM trees under", ROOT)
PY

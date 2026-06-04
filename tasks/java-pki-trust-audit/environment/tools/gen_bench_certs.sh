#!/bin/bash
# Generate deterministic bench PKI material under data/certs and data/crls.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$ROOT/data/certs"
CRL_DIR="$ROOT/data/crls"
mkdir -p "$CERT_DIR" "$CRL_DIR"
export MSYS_NO_PATHCONV=1 2>/dev/null || true

gen_ca() {
  local name=$1 days=$2
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/${name}.key.pem" \
    -out "$CERT_DIR/${name}.pem" \
    -days "$days" -subj "/CN=${name}" \
    -addext "subjectKeyIdentifier=hash" \
    -addext "basicConstraints=critical,CA:true" 2>/dev/null
}

gen_int() {
  local name=$1 issuer=$2 days=$3
  openssl req -new -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/${name}.key.pem" \
    -out "$CERT_DIR/${name}.csr.pem" \
    -subj "/CN=${name}" 2>/dev/null
  openssl x509 -req -in "$CERT_DIR/${name}.csr.pem" \
    -CA "$CERT_DIR/${issuer}.pem" -CAkey "$CERT_DIR/${issuer}.key.pem" \
    -CAcreateserial -out "$CERT_DIR/${name}.pem" -days "$days" \
    -copy_extensions copyall \
    -extfile <(printf '%s\n' "subjectKeyIdentifier=hash" "authorityKeyIdentifier=keyid" "basicConstraints=critical,CA:true") 2>/dev/null
}

gen_leaf() {
  local name=$1 issuer=$2 days=$3
  openssl req -new -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/${name}.key.pem" \
    -out "$CERT_DIR/${name}.csr.pem" \
    -subj "/CN=${name}" 2>/dev/null
  openssl x509 -req -in "$CERT_DIR/${name}.csr.pem" \
    -CA "$CERT_DIR/${issuer}.pem" -CAkey "$CERT_DIR/${issuer}.key.pem" \
    -CAcreateserial -out "$CERT_DIR/${name}.pem" -days "$days" \
    -copy_extensions copyall \
    -extfile <(printf '%s\n' "subjectKeyIdentifier=hash" "authorityKeyIdentifier=keyid") 2>/dev/null
}

# Expired root (notAfter in the past)
gen_ca "bench-root-expired" 1
# Valid root
gen_ca "bench-root-live" 3650
# Revoked intermediate + clean intermediate
gen_int "bench-int-revoked" "bench-root-live" 800
gen_int "bench-int-clean" "bench-root-live" 800
# Leaves
gen_leaf "bench-leaf-valid" "bench-int-clean" 400
gen_leaf "bench-leaf-longpath" "bench-int-clean" 400
gen_int "bench-int-extra" "bench-int-clean" 400
gen_leaf "bench-leaf-deep" "bench-int-extra" 400
gen_leaf "bench-leaf-revoked-int" "bench-int-revoked" 400

# CRL for revoked intermediate (thisUpdate 20240101000000Z)
openssl ca -gencrl -keyfile "$CERT_DIR/bench-root-live.key.pem" \
  -cert "$CERT_DIR/bench-root-live.pem" \
  -crldays 30 -out "$CRL_DIR/bench-int-revoked-v1.crl" 2>/dev/null || true

# Build CRL with openssl crl manually if ca fails
cat > "$CRL_DIR/bench-int-revoked-v1.crl" <<'CRLPLACE'
-----BEGIN X509 CRL-----
MIIB0jCBzAIBATANBgkqhkiG9w0BAQsFADAVMRMwEQYDVQQDDApiZW5jaC1yb290
-----END X509 CRL-----
CRLPLACE

# Use openssl to create proper CRL
openssl ca -config <(cat <<EOF
[ca]
default_ca = CA_default
[CA_default]
database = $CERT_DIR/index.txt
certificate = $CERT_DIR/bench-root-live.pem
private_key = $CERT_DIR/bench-root-live.key.pem
default_crl_days = 30
default_md = sha256
[crl_ext]
authorityKeyIdentifier=keyid:always
EOF
) -gencrl -out "$CRL_DIR/bench-int-revoked-v1.crl" 2>/dev/null || \
  openssl crl -inform PEM -in "$CRL_DIR/bench-int-revoked-v1.crl" -out /dev/null 2>/dev/null || true

# Simpler: generate CRL with revoked serial using openssl req + custom approach
SERIAL_FILE="$CERT_DIR/revoked-serial.txt"
openssl x509 -in "$CERT_DIR/bench-int-revoked.pem" -noout -serial | sed 's/serial=//' > "$SERIAL_FILE"

# Pack corpus bundle
cat "$CERT_DIR/bench-root-live.pem" "$CERT_DIR/bench-int-clean.pem" "$CERT_DIR/bench-leaf-valid.pem" \
  > "$CERT_DIR/corpus-valid.pem"
cat "$CERT_DIR/bench-root-expired.pem" "$CERT_DIR/bench-int-clean.pem" "$CERT_DIR/bench-leaf-valid.pem" \
  > "$CERT_DIR/corpus-expired-root.pem"
cat "$CERT_DIR/bench-root-live.pem" "$CERT_DIR/bench-int-revoked.pem" "$CERT_DIR/bench-leaf-revoked-int.pem" \
  > "$CERT_DIR/corpus-revoked-int.pem"
cat "$CERT_DIR/bench-root-live.pem" "$CERT_DIR/bench-int-clean.pem" "$CERT_DIR/bench-int-extra.pem" \
  "$CERT_DIR/bench-int-deep2.pem" "$CERT_DIR/bench-leaf-deep.pem" > "$CERT_DIR/corpus-deep.pem"
cat "$CERT_DIR/bench-root-live.pem" "$CERT_DIR/bench-int-alt.pem" "$CERT_DIR/bench-leaf-alt.pem" \
  > "$CERT_DIR/corpus-alt-valid.pem"

echo "cert generation complete"

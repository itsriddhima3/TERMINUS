#!/bin/bash
set -euo pipefail

pem="${1:-}"
mode="${2:-sha256}"
if [[ -z "$pem" || ! -f "$pem" ]]; then
  echo "usage: openssl_helper.sh <pem> [sha256|sha1]" >&2
  exit 2
fi
openssl x509 -in "$pem" -noout -fingerprint -"$mode" | sed 's/.*=//' | tr -d ':' | tr 'A-Z' 'a-z'

#!/bin/bash
set -euo pipefail

command -v lua5.4 >/dev/null
command -v openssl >/dev/null
command -v dot >/dev/null
python3 -c 'import cryptography' >/dev/null
echo ok

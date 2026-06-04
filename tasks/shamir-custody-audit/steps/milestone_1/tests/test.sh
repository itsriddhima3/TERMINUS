#!/bin/bash

# Edition 2 template: do not add set -e or set -euo pipefail — errexit skips the reward block.
# Keep the five-line footer below; $? must refer to the uvx/pytest command on the preceding line.

source $HOME/.local/bin/env

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
    exit 1
fi

uvx \
  -p 3.13 \
  -w pytest==8.4.1 \
  -w pytest-json-ctrf==0.3.5 \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_m1.py -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

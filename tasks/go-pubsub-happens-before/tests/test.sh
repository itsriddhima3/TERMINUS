#!/bin/bash

# Offline verifier: Dockerfile warms uv into /opt/uv-cache at build; UV_OFFLINE=1 here.
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

source $HOME/.local/bin/env

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
    exit 1
fi

# Don't change anything below this line except for adding additional Python dependencies
# Produce reward file (REQUIRED) — $? is read on the next line immediately after pytest
install -D -m 0644 /tests/fixtures/scenario_matrix.json /app/data/scenario_matrix.json && UV_OFFLINE=1 uvx \
  -p 3.13 \
  -w pytest==8.4.1 \
  -w pytest-json-ctrf==0.3.5 \
  -w pytest-randomly==3.16.0 \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

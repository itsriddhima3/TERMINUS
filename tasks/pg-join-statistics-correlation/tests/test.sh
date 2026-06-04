#!/bin/bash

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

# Verifier deps are preinstalled in environment/Dockerfile (allow_internet=false).
/opt/tbench-verifier/bin/pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA -p randomly

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

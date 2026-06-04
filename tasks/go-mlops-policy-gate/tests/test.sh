#!/bin/bash

# Offline verifier: Dockerfile warms pytest into /opt/uv-cache; UV_OFFLINE=1 at runtime.
source $HOME/.local/bin/env

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
    exit 1
fi

# Don't change anything below this line except for adding additional Python dependencies
# Produce reward file (REQUIRED) — $? is read on the next line immediately after pytest
install -m 0644 /tests/fixtures/cases/hidden_h1.json /app/data/reports/hidden_h1.json && \
install -m 0644 /tests/fixtures/cases/hidden_h2.json /app/data/reports/hidden_h2.json && \
install -m 0644 /tests/fixtures/cases/hidden_h3.json /app/data/reports/hidden_h3.json && \
install -m 0644 /tests/fixtures/cases/reg_mae_warn_j6.json /app/data/reports/reg_mae_warn_j6.json && \
install -m 0644 /tests/fixtures/cases/reg_dual_slot_m8.json /app/data/reports/reg_dual_slot_m8.json && \
install -m 0644 /tests/fixtures/cases/emb_ndcg_only_p4.json /app/data/reports/emb_ndcg_only_p4.json && \
install -m 0644 /tests/fixtures/cases/emb_stg_warn_q1.json /app/data/reports/emb_stg_warn_q1.json && \
install -m 0644 /tests/fixtures/cases/reg_stg_ratio_s3.json /app/data/reports/reg_stg_ratio_s3.json && \
install -m 0644 /tests/fixtures/cases/cls_f1_band_t5.json /app/data/reports/cls_f1_band_t5.json && \
install -m 0644 /tests/fixtures/cases/cls_drift_cap_u7.json /app/data/reports/cls_drift_cap_u7.json && \
install -m 0644 /tests/fixtures/cases/reg_exp_narrow_n3.json /app/data/reports/reg_exp_narrow_n3.json && \
UV_OFFLINE=1 uvx \
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

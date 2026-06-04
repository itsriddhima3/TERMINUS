FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

LABEL org.opencontainers.image.title="wandb-secret-auditor"
LABEL org.opencontainers.image.description="Terminal-Bench offline run security auditor (Kotlin)"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench-3"
LABEL org.opencontainers.image.version="2.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV SOURCE_DATE_EPOCH=1700000000
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"

WORKDIR /app

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

COPY platform/verifier-requirements.txt /tmp/verifier-requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    curl \
    openjdk-17-jdk-headless \
    kotlin \
    tmux \
 && mkdir -p /root/.local/bin "${UV_CACHE_DIR}" \
 && chmod 777 "${UV_CACHE_DIR}" \
 && curl -fsSL "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" -o /tmp/uv.tar.gz \
 && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/uv.tar.gz -C /root/.local/bin --strip-components=1 \
 && rm /tmp/uv.tar.gz \
 && printf '%s\n' \
      'export PATH="/root/.local/bin:${PATH}"' \
      'export UV_CACHE_DIR="/opt/uv-cache"' \
      > /root/.local/bin/env \
 && . /root/.local/bin/env \
 && UV_OFFLINE=0 uv python install 3.13 \
 && UV_OFFLINE=0 uv venv /opt/venv --python 3.13 \
 && UV_OFFLINE=0 uv pip install --python /opt/venv/bin/python -r /tmp/verifier-requirements.txt \
 && PATH="/opt/venv/bin:${PATH}" python -m pytest --version \
 && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/venv/bin:/root/.local/bin:${PATH}"
ENV UV_OFFLINE=1

COPY cli /app/cli
COPY core /app/core
COPY docs /app/docs
COPY fixtures /app/fixtures
COPY scripts /app/scripts
COPY README.md /app/README.md

RUN mkdir -p /app/output /app/bin /app/build \
 && chmod +x /app/scripts/*.sh

CMD ["sleep", "infinity"]

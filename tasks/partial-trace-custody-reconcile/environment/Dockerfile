FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

LABEL org.opencontainers.image.title="partial-trace-custody-reconcile"
LABEL org.opencontainers.image.description="Terminal-Bench custody trace reconciliation batch"
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
COPY Cargo.toml /app/Cargo.toml
COPY Cargo.lock /app/Cargo.lock
COPY Makefile /app/Makefile

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema=2.2.0-1 \
    build-essential=12.9 \
    ca-certificates=20230311+deb12u1 \
    curl=7.88.1-10+deb12u14 \
    pkg-config=1.8.1-1 \
    rustc=1.63.0+dfsg1-2 \
    cargo=0.66.0+ds1-1 \
    tmux=3.3a-3 \
 && mkdir -p /root/.local/bin \
 && curl -fsSL "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" -o /tmp/uv.tar.gz \
 && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
 && mkdir -p /tmp/uv-unpack \
 && tar -xzf /tmp/uv.tar.gz -C /tmp/uv-unpack \
 && install -m 0755 /tmp/uv-unpack/uv-x86_64-unknown-linux-gnu/uv /root/.local/bin/uv \
 && install -m 0755 /tmp/uv-unpack/uv-x86_64-unknown-linux-gnu/uvx /root/.local/bin/uvx \
 && rm -rf /tmp/uv.tar.gz /tmp/uv-unpack \
 && mkdir -p "${UV_CACHE_DIR}" \
 && chmod 777 "${UV_CACHE_DIR}" \
 && printf '%s\n' \
      'export PATH="/root/.local/bin:${PATH}"' \
      'export UV_CACHE_DIR="/opt/uv-cache"' \
      > /root/.local/bin/env \
 && . /root/.local/bin/env \
 && specs="" \
 && while IFS= read -r line || [ -n "$line" ]; do \
      case "$line" in ''|\#*) continue;; esac; specs="$specs -w $line"; \
    done < /tmp/verifier-requirements.txt \
 && UV_OFFLINE=0 uv tool install --python 3.13 pytest==8.4.1 --with pytest-json-ctrf==0.3.5 \
 && UV_OFFLINE=0 uvx -p 3.13 $specs pytest --version \
 && rm -rf /var/lib/apt/lists/*

ENV UV_OFFLINE=1

COPY src /app/src
COPY merge-src /app/merge-src
COPY resolve-src /app/resolve-src
COPY graph-src /app/graph-src
COPY seal-src /app/seal-src
COPY decoy-src /app/decoy-src
COPY cases /app/cases
COPY config /app/config
COPY docs /app/docs
COPY --chmod=0755 scripts /app/scripts
COPY --chmod=0755 platform /app/platform
COPY README.md /app/README.md

RUN make route_pack \
 && rm -rf /app/target \
 && mkdir -p /app/output

CMD ["sleep", "infinity"]

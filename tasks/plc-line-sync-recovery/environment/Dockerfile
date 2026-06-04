FROM golang:1.22-bookworm@sha256:1f298b0c9fecdf504389a0329236f948cc04a566a2bb32337207cbaaa2f8177c

LABEL org.opencontainers.image.title="plc-line-sync-recovery"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

ENV PATH="/root/.local/bin:/usr/bin:/usr/local/go/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"
ENV UV_OFFLINE=1
ENV SOURCE_DATE_EPOCH=0
ENV CGO_ENABLED=1

# 1. OS packages + offline verifier toolchain (allow_internet=false)
# cargo-web: bookworm rustc/cargo toolchain (virtual "cargo" provider; not the deprecated crate)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
        tmux=3.3a-3 \
        cargo-web=1.85.0+dfsg3-1~deb12u3 \
    && mkdir -p /root/.local/bin \
    && curl -fsSL "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" -o /tmp/uv.tar.gz \
    && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
    && mkdir -p /tmp/uv-unpack \
    && tar -xzf /tmp/uv.tar.gz -C /tmp/uv-unpack \
    && install -m 0755 /tmp/uv-unpack/uv-x86_64-unknown-linux-gnu/uv /root/.local/bin/uv \
    && install -m 0755 /tmp/uv-unpack/uv-x86_64-unknown-linux-gnu/uvx /root/.local/bin/uvx \
    && rm -rf /tmp/uv.tar.gz /tmp/uv-unpack \
    && printf '%s\n' \
        'export PATH="/root/.local/bin:${PATH}"' \
        'export UV_CACHE_DIR="/opt/uv-cache"' \
        > /root/.local/bin/env \
    && . /root/.local/bin/env \
    && mkdir -p "${UV_CACHE_DIR}" \
    && chmod 777 "${UV_CACHE_DIR}" \
    && UV_OFFLINE=0 uv tool install --python 3.13 pytest==8.4.1 --with pytest-json-ctrf==0.3.5 \
    && UV_OFFLINE=0 uvx -p 3.13 -w pytest==8.4.1 -w pytest-json-ctrf==0.3.5 pytest --version \
    && rm -rf /var/lib/apt/lists/*

# 3. Project manifests (least volatile)
COPY go.mod /app/go.mod
COPY sync_core/Cargo.toml /app/sync_core/Cargo.toml
COPY sync_core/Cargo.lock /app/sync_core/Cargo.lock

# 4. Source and task files (narrow COPY; no solution/ or tests/)
COPY cmd /app/cmd
COPY internal /app/internal
COPY pkg /app/pkg
COPY sync_core/src /app/sync_core/src
COPY sync_core/bridge.go /app/sync_core/bridge.go
COPY sync_core/doc.go /app/sync_core/doc.go
COPY sync_core/core.h /app/sync_core/core.h
COPY --chmod=0755 scripts /app/scripts
COPY docs /app/docs
COPY data /app/data
COPY schemas /app/schemas
COPY harness /app/harness
COPY profiles /app/profiles
COPY ops /app/ops
COPY tools /app/tools

# 5. Prebuild agent binary; drop build caches in the same layer
RUN mkdir -p /app/output /app/bin \
    && bash /app/scripts/build.sh \
    && rm -rf /app/sync_core/target /root/.cache/go-build

ENV PATH="/app/bin:${PATH}"

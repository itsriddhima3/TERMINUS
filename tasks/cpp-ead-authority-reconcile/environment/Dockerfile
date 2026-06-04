# syntax=docker/dockerfile:1

FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3 AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        cmake=3.25.1-1 \
        libcurl4-openssl-dev=7.88.1-10+deb12u14 \
        libxml2-dev=2.9.14+dfsg-1.3~deb12u5 \
    && rm -rf /var/lib/apt/lists/*

COPY cli /app/cli
COPY decoy /app/decoy

RUN mkdir -p /app/bin /app/cli/build \
    && cd /app/cli/build \
    && cmake -DCMAKE_BUILD_TYPE=Release .. \
    && cmake --build . -j"$(nproc)" \
    && install -m 0755 arcctl /app/bin/arcctl

FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

LABEL org.opencontainers.image.title="cpp-ead-authority-reconcile"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.revision="ead-reconcile-v1"
LABEL org.opencontainers.image.created="2026-06-03T00:00:00Z"

ENV DEBIAN_FRONTEND=noninteractive
ENV SOURCE_DATE_EPOCH=1700000000
ENV PATH="/root/.local/bin:/app/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"
ENV UV_OFFLINE=1
ENV TEST_DIR=/tests

WORKDIR /app

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

COPY platform/verifier-requirements.txt /tmp/verifier-requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        cmake=3.25.1-1 \
        curl=7.88.1-10+deb12u14 \
        libcurl4=7.88.1-10+deb12u14 \
        libcurl4-openssl-dev=7.88.1-10+deb12u14 \
        libxml2=2.9.14+dfsg-1.3~deb12u5 \
        libxml2-dev=2.9.14+dfsg-1.3~deb12u5 \
        nodejs=18.20.4+dfsg-1~deb12u2 \
        npm=9.2.0~ds1-1 \
        patch=2.7.6-7 \
        tmux=3.3a-3 \
    && mkdir -p /root/.local/bin \
    && curl -fsSL --retry 5 --retry-all-errors --retry-delay 2 \
        "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
        -o /tmp/uv.tar.gz \
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
    && specs="" \
    && while IFS= read -r line || [ -n "$line" ]; do \
         case "$line" in ''|\#*) continue;; esac; specs="$specs -w $line"; \
       done < /tmp/verifier-requirements.txt \
    && UV_OFFLINE=0 uv tool install --python 3.13 pytest==8.4.1 \
        --with pytest-json-ctrf==0.3.5 \
    && UV_OFFLINE=0 uvx -p 3.13 $specs pytest --version \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json /app/
RUN npm ci --prefix /app

COPY --from=builder /app/bin/arcctl /app/bin/arcctl
COPY api /app/api
COPY cli /app/cli
COPY config /app/config
COPY data /app/data
COPY decoy /app/decoy
COPY docs /app/docs
COPY platform /app/platform
COPY --chmod=0755 scripts /app/scripts
COPY README.md /app/README.md

RUN bash /app/scripts/init-workspace.sh \
    && rm -rf /app/cli/build

CMD ["sleep", "infinity"]

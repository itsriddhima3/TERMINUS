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
    && rm -rf /var/lib/apt/lists/*

COPY CMakeLists.txt /app/
COPY cmd /app/cmd
COPY client /app/client
COPY core /app/core
COPY decoy /app/decoy
COPY lib /app/lib

RUN mkdir -p /app/build /app/bin \
    && cmake -S /app -B /app/build \
    && cmake --build /app/build -j"$(nproc)" \
    && install -m 0755 /app/build/ratectl /app/bin/ratectl

FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

LABEL org.opencontainers.image.title="cpp-rails-mf-recommender"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.revision="bench-split-a7"
LABEL org.opencontainers.image.created="2026-06-03T00:00:00Z"

WORKDIR /app

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:/app/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"
ENV UV_OFFLINE=1
ENV TEST_DIR=/tests

COPY platform/verifier-requirements.txt /tmp/verifier-requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        cmake=3.25.1-1 \
        curl=7.88.1-10+deb12u14 \
        jq=1.6-2.1+deb12u1 \
        libcurl4=7.88.1-10+deb12u14 \
        libcurl4-openssl-dev=7.88.1-10+deb12u14 \
        patch=2.7.6-7 \
        python3=3.11.2-1+b1 \
        ruby=1:3.1 \
        ruby-sqlite3=1.4.2-4+b3 \
        sqlite3=3.40.1-2+deb12u2 \
        tmux=3.3a-3 \
    && gem install --no-document rack:2.2.8 \
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

COPY --from=builder /app/bin/ratectl /app/bin/ratectl
COPY CMakeLists.txt /app/
COPY cmd /app/cmd
COPY client /app/client
COPY core /app/core
COPY decoy /app/decoy
COPY lib /app/lib
COPY --chmod=0755 scripts /app/scripts
COPY --chmod=0755 app /app/app
COPY service /app/service
COPY data /app/data
COPY docs /app/docs
COPY config /app/config
COPY platform /app/platform

RUN bash /app/scripts/init_workspace.sh \
    && rm -rf /app/build

CMD ["bash", "-c", "/app/scripts/start_api.sh && exec sleep infinity"]

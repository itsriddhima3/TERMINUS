FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3 AS uvdeps

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

ENV UV_CACHE_DIR="/opt/uv-cache"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
    && mkdir -p /root/.local/bin "${UV_CACHE_DIR}" \
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
    && install -d -m 0777 "${UV_CACHE_DIR}" \
    && UV_OFFLINE=0 uv tool install --python 3.13 pytest==8.4.1 \
        --with pytest-json-ctrf==0.3.5 \
    && UV_OFFLINE=0 uvx -p 3.13 -w pytest==8.4.1 -w pytest-json-ctrf==0.3.5 pytest --version \
    && rm -rf /var/lib/apt/lists/*

FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3 AS builder

WORKDIR /app

ARG SQLITE_VERSION=3430200
ARG SQLITE_ZIP=sqlite-amalgamation-3430200.zip
ARG SQLITE_SHA256=a17ac8792f57266847d57651c5259001d1e4e4b46be96ec0d985c953925b2a1c

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
        unzip=6.0-28 \
    && mkdir -p /app/sqlite /app/bin \
    && curl -fsSL --retry 5 --retry-all-errors --retry-delay 2 \
        "https://www.sqlite.org/2023/${SQLITE_ZIP}" -o "/tmp/${SQLITE_ZIP}" \
    && echo "${SQLITE_SHA256}  /tmp/${SQLITE_ZIP}" | sha256sum -c - \
    && unzip -q "/tmp/${SQLITE_ZIP}" -d /tmp \
    && cp "/tmp/sqlite-amalgamation-${SQLITE_VERSION}/sqlite3.c" /app/sqlite/ \
    && cp "/tmp/sqlite-amalgamation-${SQLITE_VERSION}/sqlite3.h" /app/sqlite/ \
    && cp "/tmp/sqlite-amalgamation-${SQLITE_VERSION}/sqlite3ext.h" /app/sqlite/ \
    && rm -rf "/tmp/${SQLITE_ZIP}" "/tmp/sqlite-amalgamation-${SQLITE_VERSION}" \
    && rm -rf /var/lib/apt/lists/*

COPY Makefile /app/Makefile
COPY include /app/include
COPY gate /app/gate
COPY src /app/src
COPY journal /app/journal
COPY decoy /app/decoy
COPY --chmod=0755 scripts /app/scripts
COPY config /app/config
COPY data /app/data
COPY docs /app/docs
COPY schemas /app/schemas
COPY ops /app/ops
COPY harness /app/harness

RUN bash /app/scripts/build.sh \
    && rm -rf /app/build

FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

LABEL org.opencontainers.image.title="c-sqlite-wal-powerloss"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_CACHE_DIR="/opt/uv-cache"
ENV UV_OFFLINE=1
ENV PATH="/root/.local/bin:/app/bin:${PATH}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux=3.3a-3 \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        build-essential=12.9 \
        sqlite3=3.40.1-2+deb12u2 \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _image_probe \
    && tmux kill-session -t _image_probe \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uvdeps /root/.local /root/.local
COPY --from=uvdeps /opt/uv-cache /opt/uv-cache

COPY --from=builder /app/bin/datalog /app/bin/datalog
COPY --from=builder /app/sqlite /app/sqlite
COPY Makefile /app/Makefile
COPY include /app/include
COPY gate /app/gate
COPY src /app/src
COPY journal /app/journal
COPY decoy /app/decoy
COPY --chmod=0755 scripts /app/scripts
COPY config /app/config
COPY data /app/data
COPY docs /app/docs
COPY schemas /app/schemas
COPY ops /app/ops
COPY harness /app/harness

RUN mkdir -p /app/output

CMD ["sleep", "infinity"]

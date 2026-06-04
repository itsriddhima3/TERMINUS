# syntax=docker/dockerfile:1

FROM golang:1.22-bookworm@sha256:3d699e4d15d0f8f13c9195c0632a16702b8cbdece2955af1c23b37ae5d55a253 AS gobuild

WORKDIR /app

ENV GOMODCACHE=/root/go/pkg/mod
ENV GOCACHE=/root/.cache/go-build
ENV CGO_ENABLED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates=20230311+deb12u1 \
        gcc=4:12.2.0-3 \
        libc6-dev=2.36-9+deb12u14 \
        sqlite3=3.40.1-2+deb12u2 \
    && rm -rf /var/lib/apt/lists/*

COPY go.mod go.sum /app/
RUN go mod download

COPY cmd /app/cmd
COPY internal /app/internal
COPY configs /app/configs
COPY --chmod=0755 scripts /app/scripts
COPY docs /app/docs
COPY data /app/data

RUN bash /app/scripts/build.sh \
    && bash /app/scripts/init-db.sh \
    && rm -rf /root/.cache/go-build

FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

LABEL org.opencontainers.image.title="shamir-custody-audit"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

ENV PATH="/root/.local/bin:/usr/local/go/bin:/app/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"
ENV UV_OFFLINE=1
ENV GOMODCACHE=/root/go/pkg/mod
ENV GOCACHE=/root/.cache/go-build
ENV CGO_ENABLED=1

# OS packages + offline verifier toolchain (allow_internet=false at runtime).
# Apt versions are pinned to Bookworm point releases for reproducible builds; refresh pins if mirrors drop packages.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
        gcc=4:12.2.0-3 \
        jq=1.6-2.1+deb12u1 \
        libc6-dev=2.36-9+deb12u14 \
        sqlite3=3.40.1-2+deb12u2 \
        patch=2.7.6-7 \
        python3=3.11.2-1+b1 \
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
    && UV_OFFLINE=0 uv tool install --python 3.13 pytest==8.4.1 \
        --with pytest-json-ctrf==0.3.5 \
    && UV_OFFLINE=0 uvx -p 3.13 -w pytest==8.4.1 -w pytest-json-ctrf==0.3.5 pytest --version \
    && rm -rf /var/lib/apt/lists/*

COPY --from=gobuild /usr/local/go /usr/local/go
COPY --from=gobuild /root/go/pkg/mod /root/go/pkg/mod
COPY --from=gobuild /app/bin/audit /app/bin/audit
COPY --from=gobuild /app/data /app/data

COPY go.mod go.sum /app/
COPY cmd /app/cmd
COPY internal /app/internal
COPY configs /app/configs
COPY --chmod=0755 scripts /app/scripts
COPY docs /app/docs

CMD ["sleep", "infinity"]

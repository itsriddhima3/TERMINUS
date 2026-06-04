FROM golang:1.22-bookworm@sha256:3d699e4d15d0f8f13c9195c0632a16702b8cbdece2955af1c23b37ae5d55a253

LABEL org.opencontainers.image.title="go-pubsub-happens-before"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

ENV PATH="/root/.local/bin:/usr/local/go/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"
ENV UV_OFFLINE=1
ENV GOMODCACHE=/root/go/pkg/mod
ENV GOCACHE=/root/.cache/go-build
ENV CGO_ENABLED=1

# OS packages + offline verifier toolchain (allow_internet=false at runtime).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
        gcc=4:12.2.0-3 \
        jq=1.6-2.1+deb12u1 \
        libc6-dev=2.36-9+deb12u14 \
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
        --with pytest-json-ctrf==0.3.5 --with pytest-randomly==3.16.0 \
    && UV_OFFLINE=0 uvx -p 3.13 \
        -w pytest==8.4.1 \
        -w pytest-json-ctrf==0.3.5 \
        -w pytest-randomly==3.16.0 \
        pytest --version \
    && rm -rf /var/lib/apt/lists/*

COPY go.mod /app/go.mod
COPY cmd /app/cmd
COPY hub /app/hub
COPY pkg /app/pkg
COPY internal /app/internal
COPY --chmod=0755 app /app/app
COPY --chmod=0755 lib /app/lib
COPY data /app/data
COPY docs /app/docs

RUN go mod tidy \
    && go build -o /app/bin/scenar ./cmd/scenar \
    && go build -o /app/bin/daemon ./cmd/daemon \
    && rm -rf /root/.cache/go-build

CMD ["sleep", "infinity"]

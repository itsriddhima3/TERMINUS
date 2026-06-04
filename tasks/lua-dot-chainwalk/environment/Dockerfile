FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

LABEL org.opencontainers.image.title="lua-dot-chainwalk"
LABEL org.opencontainers.image.description="Terminal-Bench DOT layout TLS chain audit (Lua)"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench-3"
LABEL org.opencontainers.image.version="2.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV SOURCE_DATE_EPOCH=1700000000
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"

WORKDIR /app

# task.toml sets allow_internet=false; bake verifier deps at image build time.
COPY platform/verifier-requirements.txt /tmp/verifier-requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    curl \
    graphviz \
    lua5.4 \
    openssl \
    patch \
    python3 \
    python3-cryptography \
    tar \
    tmux \
 && UV_VERSION="0.9.5" \
 && arch="$(dpkg --print-architecture)" \
 && case "${arch}" in \
      amd64) uv_target="x86_64-unknown-linux-gnu" ;; \
      arm64) uv_target="aarch64-unknown-linux-gnu" ;; \
      *) echo "Unsupported architecture: ${arch}" >&2; exit 1 ;; \
    esac \
 && uv_tgz="uv-${uv_target}.tar.gz" \
 && uv_base_url="https://github.com/astral-sh/uv/releases/download/${UV_VERSION}" \
 && mkdir -p /root/.local/bin \
 && curl -fsSL "${uv_base_url}/${uv_tgz}" -o "/tmp/${uv_tgz}" \
 && curl -fsSL "${uv_base_url}/${uv_tgz}.sha256" -o "/tmp/${uv_tgz}.sha256" \
 && (cd /tmp && sha256sum -c "${uv_tgz}.sha256") \
 && rm -rf /tmp/uv-extract \
 && mkdir -p /tmp/uv-extract \
 && tar -xzf "/tmp/${uv_tgz}" -C /tmp/uv-extract \
 && uv_src="/tmp/uv-extract/uv" \
 && [ -f "${uv_src}" ] || uv_src="$(ls /tmp/uv-extract/*/uv)" \
 && uvx_src="/tmp/uv-extract/uvx" \
 && [ -f "${uvx_src}" ] || uvx_src="$(ls /tmp/uv-extract/*/uvx)" \
 && install -m 0755 "${uv_src}" /root/.local/bin/uv \
 && install -m 0755 "${uvx_src}" /root/.local/bin/uvx \
 && rm -rf "/tmp/${uv_tgz}" "/tmp/${uv_tgz}.sha256" /tmp/uv-extract \
 && mkdir -p "${UV_CACHE_DIR}" \
 && chmod 777 "${UV_CACHE_DIR}" \
 && printf '%s\n' \
      'export PATH="/root/.local/bin:${PATH}"' \
      'export UV_CACHE_DIR="/opt/uv-cache"' \
      > /root/.local/bin/env \
 && . /root/.local/bin/env \
 && UV_OFFLINE=0 uv python install 3.13 \
 && . /root/.local/bin/env \
 && uv tool install --python 3.13 pytest==8.4.1 --with pytest-json-ctrf==0.3.5 \
 && rm -rf /var/lib/apt/lists/*

ENV UV_OFFLINE=1

COPY config /app/config
COPY docs /app/docs
COPY platform /app/platform
COPY scripts /app/scripts
COPY graph-src /app/graph-src
COPY openssl-src /app/openssl-src
COPY policy-src /app/policy-src
COPY emit-src /app/emit-src
COPY pem-src /app/pem-src
COPY flow-src /app/flow-src
COPY decoy-src /app/decoy-src
COPY lib /app/lib
COPY cases /app/cases
COPY README.md /app/README.md

RUN mkdir -p /app/output /app/output/marked \
 && chmod +x /app/platform/chainwalk /app/platform/*.sh /app/scripts/*.sh \
 && bash /app/scripts/regen_cases.sh

CMD ["sleep", "infinity"]

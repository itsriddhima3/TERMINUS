FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

LABEL org.opencontainers.image.title="java-pki-trust-audit"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"
ARG TARGETARCH=amd64
ARG UV_VERSION=0.9.5

WORKDIR /app

COPY platform/verifier-requirements.txt /tmp/verifier-requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema=2.2.0-1 \
    ca-certificates=20230311+deb12u1 \
    curl=7.88.1-10+deb12u14 \
    datefudge=1.24 \
    graphviz=2.42.2-7+deb12u1 \
    jq=1.6-2.1+deb12u1 \
    openjdk-17-jdk-headless=17.0.19+10-1~deb12u2 \
    maven=3.8.7-1 \
    openssl=3.0.20-1~deb12u1 \
    patch=2.7.6-7 \
    python3=3.11.2-1+b1 \
    tar=1.34+dfsg-1.2+deb12u1 \
    tmux=3.3a-3 \
 && case "${TARGETARCH}" in \
      amd64) uv_target="x86_64-unknown-linux-gnu" ;; \
      arm64) uv_target="aarch64-unknown-linux-gnu" ;; \
      *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
 && uv_tgz="uv-${uv_target}.tar.gz" \
 && uv_base_url="https://github.com/astral-sh/uv/releases/download/${UV_VERSION}" \
 && curl -fsSL --retry 5 --retry-all-errors --retry-delay 2 \
    "${uv_base_url}/${uv_tgz}" -o "/tmp/${uv_tgz}" \
 && curl -fsSL --retry 5 --retry-all-errors --retry-delay 2 \
    "${uv_base_url}/${uv_tgz}.sha256" -o "/tmp/${uv_tgz}.sha256" \
 && (cd /tmp && sha256sum -c "${uv_tgz}.sha256") \
 && rm -rf /tmp/uv-extract \
 && mkdir -p /tmp/uv-extract \
 && tar -xzf "/tmp/${uv_tgz}" -C /tmp/uv-extract \
 && uv_src="/tmp/uv-extract/uv" \
 && [ -f "${uv_src}" ] || uv_src="$(ls /tmp/uv-extract/*/uv)" \
 && uvx_src="/tmp/uv-extract/uvx" \
 && [ -f "${uvx_src}" ] || uvx_src="$(ls /tmp/uv-extract/*/uvx)" \
 && install -m 0755 "${uv_src}" /usr/local/bin/uv \
 && install -m 0755 "${uvx_src}" /usr/local/bin/uvx \
 && rm -rf "/tmp/${uv_tgz}" "/tmp/${uv_tgz}.sha256" /tmp/uv-extract \
 && mkdir -p "${UV_CACHE_DIR}" \
 && chmod 777 "${UV_CACHE_DIR}" \
 && mkdir -p /root/.local/bin \
 && printf '%s\n' \
        'export PATH="/root/.local/bin:${PATH}"' \
        'export UV_CACHE_DIR="/opt/uv-cache"' \
        > /root/.local/bin/env \
 && . /root/.local/bin/env \
 && specs="" \
 && while IFS= read -r line || [ -n "$line" ]; do \
      case "$line" in ''|\#*) continue;; esac; specs="$specs -w $line"; \
    done < /tmp/verifier-requirements.txt \
 && UV_OFFLINE=0 uv python install 3.13 \
 && UV_OFFLINE=0 uv tool install --python 3.13 pytest==8.4.1 --with pytest-json-ctrf==0.3.5 \
 && UV_OFFLINE=0 uvx -p 3.13 $specs pytest --version \
 && rm -rf /var/lib/apt/lists/*

COPY cli/pom.xml /app/cli/pom.xml
RUN mkdir -p /opt/m2 && chmod 777 /opt/m2 \
 && mkdir -p /app/cli/src/main/java \
 && cd /app/cli && mvn -q -Dmaven.repo.local=/opt/m2 dependency:resolve dependency:resolve-plugins

COPY cli/src /app/cli/src
COPY config /app/config
COPY data /app/data
COPY decoy /app/decoy
COPY docs /app/docs
COPY --chmod=0755 lib /app/lib
COPY platform /app/platform
COPY --chmod=0755 scripts /app/scripts
COPY tools /app/tools
COPY --chmod=0755 app /app/app
COPY --chmod=0755 ci /app/ci
COPY README.md /app/README.md

RUN python3 /app/tools/gen_bench_certs.py \
 && bash /app/scripts/init-workspace.sh \
 && bash /app/scripts/build-audit.sh

ENV UV_OFFLINE=1

CMD ["sleep", "infinity"]

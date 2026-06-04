FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

LABEL org.opencontainers.image.title="java-meter-ndjson-reconcile"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"
ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

WORKDIR /app

# task.toml sets allow_internet=false; warm uv's Python 3.13 + verifier deps at
# image build (network available). Per-step test.sh sets UV_OFFLINE=1 at runtime.
COPY platform/verifier-requirements.txt /tmp/verifier-requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema=2.2.0-1 \
    ca-certificates=20230311+deb12u1 \
    curl=7.88.1-10+deb12u14 \
    tmux=3.3a-3 \
    openjdk-17-jdk-headless=17.0.19+10-1~deb12u2 \
    maven=3.8.7-1 \
    patch=2.7.6-7 \
 && curl -fsSL --retry 5 --retry-all-errors --retry-delay 2 \
    "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
    -o /tmp/uv.tar.gz \
 && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
 && mkdir -p /tmp/uv \
 && tar -xzf /tmp/uv.tar.gz -C /tmp/uv --strip-components=1 \
 && install -m 0755 /tmp/uv/uv /usr/local/bin/uv \
 && install -m 0755 /tmp/uv/uvx /usr/local/bin/uvx \
 && rm -rf /tmp/uv /tmp/uv.tar.gz \
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

ENV UV_OFFLINE=1

COPY api/pom.xml /app/api/pom.xml
RUN mkdir -p /opt/m2 \
 && chmod 777 /opt/m2 \
 && mkdir -p /app/api/src/main/java \
 && cd /app/api \
 && mvn -q -Dmaven.repo.local=/opt/m2 dependency:resolve dependency:resolve-plugins
COPY api/src /app/api/src
COPY api/fixtures /app/api/fixtures
COPY cli/pom.xml /app/cli/pom.xml
RUN mkdir -p /app/cli/src/main/java \
 && cd /app/cli \
 && mvn -q -Dmaven.repo.local=/opt/m2 dependency:resolve dependency:resolve-plugins
COPY cli/src /app/cli/src
COPY config /app/config
COPY data /app/data
COPY decoy /app/decoy
COPY docs /app/docs
COPY platform /app/platform
COPY --chmod=0755 scripts /app/scripts
COPY README.md /app/README.md

RUN bash /app/scripts/init-workspace.sh \
 && bash /app/scripts/build-api.sh \
 && (cd /app/cli && mvn -q -Dmaven.repo.local=/opt/m2 package -DskipTests) \
 && bash /app/scripts/build-cli.sh

CMD ["bash", "-c", "/app/scripts/start-api.sh && exec sleep infinity"]

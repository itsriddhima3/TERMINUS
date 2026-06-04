FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"

WORKDIR /app

# task.toml sets allow_internet=false; warm uv's Python 3.13 + verifier deps at
# image build (network available). Per-step test.sh sets UV_OFFLINE=1 at runtime.
COPY platform/verifier-requirements.txt /tmp/verifier-requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema=2.2.0-1 \
    ca-certificates=20230311+deb12u1 \
    curl=7.88.1-10+deb12u14 \
    openssl=3.0.20-1~deb12u1 \
    php-cli=2:8.2+93 \
    php-curl=2:8.2+93 \
    php-sqlite3=2:8.2+93 \
    tmux=3.3a-3 \
 && curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh \
 && mkdir -p "${UV_CACHE_DIR}" \
 && chmod 777 "${UV_CACHE_DIR}" \
 && printf '%s\n' \
        'export PATH="/root/.local/bin:${PATH}"' \
        'export UV_CACHE_DIR="/opt/uv-cache"' \
        > /root/.local/bin/env \
 && . /root/.local/bin/env \
 && UV_OFFLINE=0 uv python install 3.13 \
 && specs="" \
 && while IFS= read -r line || [ -n "$line" ]; do \
      case "$line" in ''|\#*) continue;; esac; specs="$specs -w $line"; \
    done < /tmp/verifier-requirements.txt \
 && UV_OFFLINE=0 uvx -p 3.13 $specs pytest --version \
 && rm -rf /var/lib/apt/lists/*

ENV UV_OFFLINE=1

COPY api /app/api
COPY cli /app/cli
COPY config /app/config
COPY data /app/data
COPY decoy /app/decoy
COPY docs /app/docs
COPY platform /app/platform
COPY platform/tmux.conf /root/.tmux.conf
COPY scripts /app/scripts
COPY README.md /app/README.md

RUN mkdir -p /app/output /app/keys /app/var \
 && chmod +x /app/scripts/init-db.sh /app/scripts/start-api.sh /app/cli/guardctl \
 && bash /app/scripts/init-db.sh

CMD ["sleep", "infinity"]

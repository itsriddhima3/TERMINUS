FROM mongo:7.0-jammy@sha256:f11d03e9d23a4fa6131dd6a840cb5fb6bbfb557861f9c20f4b5a501192ac1584

LABEL org.opencontainers.image.title="mongo-agg-pipeline-memory"
LABEL org.opencontainers.image.description="Terminal-Bench MongoDB spine aggregation memory task"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="2.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

COPY platform/verifier-requirements.txt /tmp/verifier-requirements.txt

# Agent runtime (tmux, asciinema) and offline verifier toolchain warmed at build time.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.1.0-1 \
        ca-certificates=20240203~22.04.1 \
        curl=7.81.0-1ubuntu1.24 \
        python3=3.10.6-1~22.04.1 \
        tmux=3.2a-4ubuntu0.2 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /root/.local/bin "${UV_CACHE_DIR}" \
    && chmod 777 "${UV_CACHE_DIR}" \
    && curl -fsSL --retry 5 --retry-all-errors --retry-delay 2 \
        "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
        -o /tmp/uv.tar.gz \
    && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/uv.tar.gz -C /root/.local/bin --strip-components=1 \
    && rm -f /tmp/uv.tar.gz \
    && printf '%s\n' \
        'export PATH="/root/.local/bin:${PATH}"' \
        'export UV_CACHE_DIR="/opt/uv-cache"' \
        > /root/.local/bin/env \
    && . /root/.local/bin/env \
    && UV_OFFLINE=0 uv tool install --python 3.13 pytest==8.4.1 \
        --with pytest-json-ctrf==0.3.5 --with pytest-randomly==3.16.0 \
    && UV_OFFLINE=0 uvx -p 3.13 \
        -w pytest==8.4.1 \
        -w pytest-json-ctrf==0.3.5 \
        -w pytest-randomly==3.16.0 \
        pytest --version

ENV UV_OFFLINE=1

WORKDIR /app

COPY --chmod=0755 init/docker-entrypoint-wrapper.sh /usr/local/bin/docker-entrypoint-wrapper.sh
COPY --chmod=0755 init/ensure_mongo.sh /app/init/ensure_mongo.sh
COPY --chmod=0755 init/bootstrap.sh /app/init/bootstrap.sh
COPY init/bootstrap.js /app/init/bootstrap.js
COPY --chmod=0755 init/post_boot.sh /app/init/post_boot.sh
COPY --chmod=0755 app /app/app
COPY --chmod=0755 lib /app/lib
COPY --chmod=0755 runners /app/runners
COPY x9 /app/x9
COPY m4 /app/m4
COPY r7 /app/r7
COPY store /app/store
COPY migrations /app/migrations
COPY config /app/config
COPY data /app/data
COPY docs /app/docs
COPY decoy /app/decoy
COPY hub /app/hub
COPY pipelines /app/pipelines
COPY platform /app/platform
COPY tools/gen_seed.py /app/tools/gen_seed.py

RUN python3 /app/tools/gen_seed.py

ENTRYPOINT ["docker-entrypoint-wrapper.sh"]
CMD ["sleep", "infinity"]

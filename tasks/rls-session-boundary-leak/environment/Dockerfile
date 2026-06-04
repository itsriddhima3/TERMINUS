FROM postgres:15-bookworm@sha256:9010f897603ef2bd8aa668ecde230fc9eb4d564961569fee243bc919b1f07b3e

LABEL org.opencontainers.image.title="rls-session-boundary-leak"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"

ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=saas_db
ENV PATH="/root/.local/bin:${PATH}" \
    UV_CACHE_DIR="/opt/uv-cache" \
    UV_OFFLINE=1

# uv tool install is performed offline via pinned tarball extraction below
ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

# OS packages + verifier toolchain pre-installed for offline test execution.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
        jq=1.6-2.1+deb12u1 \
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
    && UV_OFFLINE=0 uvx -p 3.13 \
        -w pytest==8.4.1 \
        -w pytest-json-ctrf==0.3.5 \
        -w pytest-randomly==3.16.0 \
        pytest --version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --chmod=0755 init/bootstrap_once.sh /app/init/bootstrap_once.sh
COPY --chmod=0755 init/docker-entrypoint-wrapper.sh /usr/local/bin/docker-entrypoint-wrapper.sh
COPY --chmod=0755 init/ensure_pg.sh /app/init/ensure_pg.sh
COPY --chmod=0755 init/bootstrap.sh /app/init/bootstrap.sh
COPY --chmod=0755 init/post_boot.sh /app/init/post_boot.sh
COPY store /app/store
COPY q /app/q
COPY v /app/v
COPY config /app/config
COPY --chmod=0755 app /app/app
COPY --chmod=0755 lib /app/lib
COPY data /app/data
COPY migrations /app/migrations
COPY views /app/views
COPY docs /app/docs

ENTRYPOINT ["docker-entrypoint-wrapper.sh"]
CMD ["sleep", "infinity"]

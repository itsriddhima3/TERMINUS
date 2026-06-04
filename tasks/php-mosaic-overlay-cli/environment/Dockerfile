FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema=2.2.0-1 \
    ca-certificates=20230311+deb12u1 \
    curl=7.88.1-10+deb12u14 \
    imagemagick-6.q16=8:6.9.11.60+dfsg-1.6+deb12u9 \
    imagemagick-6-common=8:6.9.11.60+dfsg-1.6+deb12u9 \
    libmagickcore-6.q16-6=8:6.9.11.60+dfsg-1.6+deb12u9 \
    libmagickwand-6.q16-6=8:6.9.11.60+dfsg-1.6+deb12u9 \
    jq=1.6-2.1+deb12u1 \
    php-cli=2:8.2+93 \
    php-sqlite3=2:8.2+93 \
    sqlite3=3.40.1-2+deb12u2 \
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
 && UV_OFFLINE=0 uvx -p 3.13 \
        -w pytest==8.4.1 \
        -w pytest-json-ctrf==0.3.5 \
        pytest --version \
 && sed -i 's@<policy domain="coder" rights="none" pattern="PNG"/>@<policy domain="coder" rights="read|write" pattern="PNG"/>@' /etc/ImageMagick-6/policy.xml || true \
 && rm -rf /var/lib/apt/lists/*

# uv tool install: pytest warmed into /opt/uv-cache at image build (verifier runs uvx offline).
ENV UV_OFFLINE=1

COPY README.md /app/README.md
COPY composer.json /app/composer.json
COPY docs /app/docs
COPY config /app/config
COPY assets /app/assets
COPY cli /app/cli
COPY loop /app/loop
COPY imaging /app/imaging
COPY game /app/game
COPY lifecycle /app/lifecycle
COPY persistence /app/persistence

RUN mkdir -p /app/state /app/runtime \
 && chmod +x /app/cli/overlay-inspect /app/assets/seed/bootstrap.sh \
 && bash /app/assets/seed/bootstrap.sh

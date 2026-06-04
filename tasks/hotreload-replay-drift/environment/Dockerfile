FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_CACHE_DIR="/opt/uv-cache"

WORKDIR /app

# task.toml sets allow_internet=false; warm uv's Python 3.13 + pytest tool env at
# image build (network available) so test.sh uvx invocations work offline.
# tests/test.sh sets UV_OFFLINE=1 to enforce no network during verifier runtime.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates=20230311+deb12u1 \
    curl=7.88.1-10+deb12u14 \
    cmake=3.25.1-1 \
    make=4.3-4.1 \
    g++=4:12.2.0-3 \
    tmux=3.3a-3 \
    asciinema=2.2.0-1 \
 && curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh \
 && mkdir -p "${UV_CACHE_DIR}" \
 && chmod 777 "${UV_CACHE_DIR}" \
 && printf '%s\n' \
        'export PATH="/root/.local/bin:${PATH}"' \
        'export UV_CACHE_DIR="/opt/uv-cache"' \
        > /root/.local/bin/env \
 && . /root/.local/bin/env \
 && UV_OFFLINE=0 uvx -p 3.13 \
    -w pytest==8.4.1 \
    -w pytest-json-ctrf==0.3.5 \
    pytest --version \
 && rm -rf /var/lib/apt/lists/*

ENV UV_OFFLINE=1

COPY CMakeLists.txt /app/CMakeLists.txt
COPY include /app/include
COPY src /app/src
COPY flow /app/flow
COPY numeric /app/numeric
COPY arena /app/arena
COPY script /app/script
COPY text /app/text
COPY inspect /app/inspect
COPY decoy /app/decoy
COPY captures /app/captures
COPY docs /app/docs
COPY config /app/config

RUN mkdir -p /app/bin /app/output

CMD ["sleep", "infinity"]

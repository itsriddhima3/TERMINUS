FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3 AS build-api

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates=20230311+deb12u1 \
        maven=3.8.7-1 \
        openjdk-17-jdk-headless=17.0.19+10-1~deb12u2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY api/pom.xml api/pom.xml
RUN mvn -f api/pom.xml -q dependency:go-offline
COPY api/src api/src
RUN mvn -f api/pom.xml -q -DskipTests package

FROM postgres:15-bookworm@sha256:9010f897603ef2bd8aa668ecde230fc9eb4d564961569fee243bc919b1f07b3e

LABEL org.opencontainers.image.title="java-batch-lane-reconcile"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=lane_db
ENV PATH="/root/.local/bin:${PATH}" \
    UV_CACHE_DIR="/opt/uv-cache" \
    UV_OFFLINE=1 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
        jq=1.6-2.1+deb12u1 \
        patch=2.7.6-7 \
        openjdk-17-jre-headless=17.0.19+10-1~deb12u2 \
        maven=3.8.7-1 \
        openjdk-17-jdk-headless=17.0.19+10-1~deb12u2 \
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
    && UV_OFFLINE=0 uv tool install pytest==8.4.1 --with pytest-json-ctrf==0.3.5 \
    && pytest --version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=build-api /root/.m2 /root/.m2
COPY --from=build-api /build/api/target/lane-api.jar /app/api/lane-api.jar
COPY api/pom.xml /app/api/pom.xml
COPY api/src /app/api/src
COPY db/migration /app/db/migration
COPY db/functions /app/db/functions
COPY api/src/main/resources/application.yml /app/api/application.yml
COPY api/src/main/resources/application-prod.yml /app/api/application-prod.yml
COPY --chmod=0755 init /app/init
COPY --chmod=0755 app /app/app
COPY --chmod=0755 lib /app/lib
COPY data /app/data
COPY config /app/config
COPY docs /app/docs
COPY decoy /app/decoy

COPY --chmod=0755 init/docker-entrypoint-wrapper.sh /usr/local/bin/docker-entrypoint-wrapper.sh

ENTRYPOINT ["docker-entrypoint-wrapper.sh"]
CMD ["sleep", "infinity"]

# DOT audit workspace

Pre-built Lua audit driver over graph sketches and PEM material under `/app/cases/`.
Registry order and sweep driver live under `/app/config/` and `/app/platform/`.
Schema for emitted JSON rows is in `/app/docs/bundle_schema.md`.
Case PEM material lives under paths such as `/app/cases/delta/certs/leaf.pem`.
The image preinstalls verifier Python tooling under `/opt/uv-cache`; `tests/test.sh` sets `UV_OFFLINE=1` when invoking pytest.

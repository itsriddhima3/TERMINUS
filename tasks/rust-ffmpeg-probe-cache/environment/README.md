# clipvault workspace

Rust ingest desk packaging stream facts from `/app/data/clips` into per-lane sqlite catalogs during stress runs. Build with `/app/scripts/build.sh`.

The Harbor verifier runs pytest with `UV_OFFLINE=1` (uv and pytest are preloaded in the image).

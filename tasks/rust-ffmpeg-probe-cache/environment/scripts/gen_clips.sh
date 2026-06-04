#!/usr/bin/env bash
set -euo pipefail
OUT=/app/data/clips
mkdir -p "$OUT"
for id in a b c d; do
  for n in $(seq 1 8); do
    f="${OUT}/${id}$(printf '%02d' "${n}").mp4"
    freq=$((440 + n))
    hue=$((n * 37))
    ffmpeg -y -f lavfi -i "testsrc=duration=0.25:size=160x120:rate=10,hue=h=${hue}" \
      -f lavfi -i "sine=frequency=${freq}:duration=0.25" \
      -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$f" 2>/dev/null
  done
done

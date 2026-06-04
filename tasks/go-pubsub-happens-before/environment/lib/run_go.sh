#!/bin/bash
set -eu
cd /app
exec /app/bin/scenar "$@"

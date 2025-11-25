#!/usr/bin/env bash
set -euo pipefail

# Install Python dependencies via uv
echo "[setup] syncing python deps"
uv sync

# Install frontend dependencies via Bun
echo "[setup] installing frontend deps"
(cd frontend && bun install)

echo "[setup] done"

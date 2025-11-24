#!/usr/bin/env bash
set -euo pipefail

# Start FastAPI and Bun dev servers
python_cmd="uv run uvicorn alex_agent.infra.server:app --reload --host 0.0.0.0 --port 8000"
frontend_cmd="cd frontend && bun --bun vite"

echo "[dev] starting backend: $python_cmd"
$python_cmd &
bpid=$!

echo "[dev] starting frontend: $frontend_cmd"
$frontend_cmd &
fbpid=$!

echo "[dev] backend pid=$bpid, frontend pid=$fbpid"

trap "echo '[dev] shutting down'; kill $bpid $fbpid" INT TERM
wait

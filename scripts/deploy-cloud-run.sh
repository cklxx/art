#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}
SERVICE_NAME=${SERVICE_NAME:-alex-agent-api}
REGION=${REGION:-us-central1}
IMAGE=${IMAGE:-gcr.io/${PROJECT_ID}/${SERVICE_NAME}}

if [[ -z "${PROJECT_ID}" ]]; then
  echo "[deploy] PROJECT_ID is not set and gcloud has no active project" >&2
  exit 1
fi

echo "[deploy] building image: ${IMAGE}"
gcloud builds submit --tag "${IMAGE}" .

# Parse .env into comma-separated list for --set-env-vars
SET_ENV=""
if [[ -f .env ]]; then
  ENV_VARS=$(grep -v '^#' .env | xargs || true)
  if [[ -n "${ENV_VARS}" ]]; then
    ENV_STRING=$(echo "${ENV_VARS}" | tr ' ' ',')
    SET_ENV="--set-env-vars ${ENV_STRING}"
  fi
fi

echo "[deploy] deploying service: ${SERVICE_NAME} in ${REGION}"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --min-instances 0 \
  --max-instances 3 \
  ${SET_ENV}

echo "[deploy] done"

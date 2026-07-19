#!/usr/bin/env bash
# Deploy the retention stack to GCP Cloud Run as two services (api + web).
#
# Strategy: build both images locally and push to Artifact Registry, then `gcloud run deploy --image`.
# The web image needs the monorepo ROOT as its build context (-f apps/web/Dockerfile), which per-service
# --source deploys handle poorly — building locally keeps it reliable and verifiable.
#
# Deploy settings (deliberate, documented in README):
#   --min-instances=0  scale to zero (cold start on first hit)
#   --max-instances=1  single instance → preserves the bulk progress queue's in-process affinity
#   default CPU throttling — bulk fan-out gets CPU while the SSE /stream request is held open
#   api runs REAL Gemini via Vertex ADC (the runtime service account), not mock
#
# Prereqs: gcloud auth login + application-default login; Docker running.
# Usage: PROJECT=easy-struct REGION=asia-southeast1 deploy/deploy.sh
set -euo pipefail

PROJECT="${PROJECT:-easy-struct}"
REGION="${REGION:-asia-southeast1}"
REPO="${REPO:-retention}"
TAG="$(git rev-parse --short HEAD 2>/dev/null || echo latest)"
AR_HOST="${REGION}-docker.pkg.dev"
IMAGE_BASE="${AR_HOST}/${PROJECT}/${REPO}"
RUNTIME_SA="$(gcloud projects describe "${PROJECT}" --format='value(projectNumber)')-compute@developer.gserviceaccount.com"

echo "==> Project=${PROJECT} Region=${REGION} Tag=${TAG}"

echo "==> Enabling APIs (idempotent)"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  aiplatform.googleapis.com --project "${PROJECT}"

echo "==> Ensuring Artifact Registry repo '${REPO}'"
gcloud artifacts repositories describe "${REPO}" --location "${REGION}" --project "${PROJECT}" >/dev/null 2>&1 \
  || gcloud artifacts repositories create "${REPO}" --repository-format=docker \
       --location "${REGION}" --project "${PROJECT}" --description "Retention app images"

echo "==> Granting Vertex AI User to the Cloud Run runtime service account (for real Gemini via ADC)"
gcloud projects add-iam-policy-binding "${PROJECT}" \
  --member "serviceAccount:${RUNTIME_SA}" --role roles/aiplatform.user --condition=None >/dev/null

echo "==> Configuring Docker auth for ${AR_HOST}"
gcloud auth configure-docker "${AR_HOST}" --quiet

echo "==> Building + pushing images (${TAG})"
docker build -t "${IMAGE_BASE}/api:${TAG}" ./apps/api
docker build -t "${IMAGE_BASE}/web:${TAG}" -f ./apps/web/Dockerfile .
docker push "${IMAGE_BASE}/api:${TAG}"
docker push "${IMAGE_BASE}/web:${TAG}"

echo "==> Deploying api (real Gemini, min=0/max=1)"
gcloud run deploy retention-api \
  --project "${PROJECT}" --region "${REGION}" --image "${IMAGE_BASE}/api:${TAG}" \
  --allow-unauthenticated --min-instances=0 --max-instances=1 --timeout=300 \
  --set-env-vars "LLM_MODE=gemini,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=global"

API_URL="$(gcloud run services describe retention-api --project "${PROJECT}" --region "${REGION}" --format='value(status.url)')"
echo "==> api URL: ${API_URL}"

echo "==> Deploying web (BFF → api)"
gcloud run deploy retention-web \
  --project "${PROJECT}" --region "${REGION}" --image "${IMAGE_BASE}/web:${TAG}" \
  --allow-unauthenticated --min-instances=0 --max-instances=1 --timeout=300 \
  --set-env-vars "API_BASE_URL=${API_URL}"

WEB_URL="$(gcloud run services describe retention-web --project "${PROJECT}" --region "${REGION}" --format='value(status.url)')"
echo ""
echo "==> DONE"
echo "    web (share this): ${WEB_URL}"
echo "    api:              ${API_URL}"

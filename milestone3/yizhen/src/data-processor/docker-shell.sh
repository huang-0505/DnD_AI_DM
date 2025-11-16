#!/bin/bash
set -e

# ============================================================
# 🚀 DnD Data Processor Docker Shell Script
# ============================================================

export IMAGE_NAME="dnd-data-processor"

export BASE_DIR=$(pwd)

export SECRETS_DIR=$(pwd)/../../../secrets/
export PERSISTENT_DIR=$(pwd)/../../../persistent-folder/

export GCP_PROJECT="ac215"
export GCS_BUCKET_NAME="ac215-ml-workflow"

echo "============================================"
echo "Building Docker image for Data Processor..."
echo "Image Name: $IMAGE_NAME"
echo "Project: $GCP_PROJECT"
echo "Bucket: $GCS_BUCKET_NAME"
echo "============================================"

# ============================================================
# 🧱 Build image (use amd64 for M1/M2 Macs)
# ============================================================
docker build --platform=linux/amd64 -t $IMAGE_NAME -f Dockerfile .

# ============================================================
# 🧩 Run container
# ============================================================
echo "Starting DnD Data Processor container..."

docker run --rm --name $IMAGE_NAME -ti \
  -v "$BASE_DIR":/app \
  -v "$SECRETS_DIR":/secrets \
  -v "$PERSISTENT_DIR":/persistent \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/ml-workflow.json \
  -e GCP_PROJECT=$GCP_PROJECT \
  -e GCS_BUCKET_NAME=$GCS_BUCKET_NAME \
  $IMAGE_NAME

#!/bin/bash
set -e

echo "==============================================="
echo "🚀 Building & Launching DnD Workflow Container"
echo "==============================================="

# ----- Configuration -----
export IMAGE_NAME="dnd-workflow"
export BASE_DIR=$(pwd)
export SECRETS_DIR="$HOME/Desktop/secrets"
export GCP_PROJECT="even-turbine-471117-u0"
export GCP_REGION="us-central1"
export GCS_BUCKET_NAME="ac215-ml-workflow-central1"
export GCS_PACKAGE_URI="gs://ac215-ml-workflow-central1/model-training"
export GCS_SERVICE_ACCOUNT="ml-workflow@even-turbine-471117-u0.iam.gserviceaccount.com"

echo "🧩 Project: $GCP_PROJECT"
echo "📍 Region: $GCP_REGION"
echo "🪣 Bucket: $GCS_BUCKET_NAME"
echo "🔐 Service Account: $GCS_SERVICE_ACCOUNT"
echo "-----------------------------------------------"

# ----- Build Docker image -----
echo "🐳 Building Docker image..."
docker build -t $IMAGE_NAME --platform=linux/amd64 -f Dockerfile .

# ----- Run Docker container -----
echo "🚀 Starting container..."

docker run --rm -it \
    --name $IMAGE_NAME \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$BASE_DIR":/app \
    -v "$SECRETS_DIR":/secrets \
    -v "$BASE_DIR/../data-collector":/data-collector \
    -v "$BASE_DIR/../data-processor":/data-processor \
    -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/ml-workflow.json \
    -e GCP_PROJECT=$GCP_PROJECT \
    -e GCP_REGION=$GCP_REGION \
    -e GCS_BUCKET_NAME=$GCS_BUCKET_NAME \
    -e GCS_PACKAGE_URI=$GCS_PACKAGE_URI \
    -e GCS_SERVICE_ACCOUNT=$GCS_SERVICE_ACCOUNT \
    -e WANDB_KEY=$WANDB_KEY \
    $IMAGE_NAME

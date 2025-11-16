#!/bin/bash
set -e

echo "============================================"
echo "🚀 Starting DnD Model Trainer container..."
echo "============================================"
echo "Architecture: $(uname -m)"
echo "Python version: $(python --version)"
echo "UV version: $(uv --version)"
echo "Project ID: $GCP_PROJECT_ID"
echo "Region: $GCP_REGION"
echo "GCS Package URI: $GCS_PACKAGE_URI"
echo "Bucket: $GCS_BUCKET_NAME"
echo "Credentials: $GOOGLE_APPLICATION_CREDENTIALS"
echo "--------------------------------------------"

# Activate virtual environment
echo "Activating virtual environment..."
source /.venv/bin/activate

# Authenticate with Google Cloud
echo "Authenticating with GCP..."
if [[ -n "$GOOGLE_APPLICATION_CREDENTIALS" && -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
    gcloud auth activate-service-account --key-file "$GOOGLE_APPLICATION_CREDENTIALS"
    gcloud config set project "$GCP_PROJECT_ID"
else
    echo "⚠️ Warning: GOOGLE_APPLICATION_CREDENTIALS not found or invalid path."
fi

echo "--------------------------------------------"
echo "Container environment is ready."
echo "--------------------------------------------"

args="$@"
if [[ -z "$args" ]]; then
    echo "💡 No command provided — opening interactive shell."
    exec /bin/bash
else
    echo "🎯 Running command: uv run python $args"
    uv run python $args
fi

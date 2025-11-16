#!/bin/bash
set -e

echo "==============================================="
echo "🚀 Container is running for DnD Model Training!"
echo "==============================================="
echo "Architecture: $(uname -m)"
echo "Python version: $(python --version)"
echo "UV version: $(uv --version)"
echo "Current directory: $(pwd)"
echo "Arguments: $@"
echo "-----------------------------------------------"

# Activate virtual environment
echo "🔹 Activating virtual environment..."
source /.venv/bin/activate

# Verify credentials exist
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS not set!"
  exit 1
fi

echo "🔹 Authenticating with GCP..."
gcloud auth activate-service-account --key-file "$GOOGLE_APPLICATION_CREDENTIALS"

# Configure GCP project and region
echo "🔹 Setting GCP project and region..."
gcloud config set project "$GCP_PROJECT"
gcloud config set compute/region "$GCP_REGION"

echo "✅ Authentication complete!"
echo "Project: $GCP_PROJECT"
echo "Region: $GCP_REGION"
echo "Bucket: $GCS_BUCKET_NAME"
echo "-----------------------------------------------"

# Verify bucket access
if ! gsutil ls "gs://$GCS_BUCKET_NAME" >/dev/null 2>&1; then
  echo "⚠️  WARNING: GCS bucket gs://$GCS_BUCKET_NAME not found or inaccessible!"
  echo "   Make sure the bucket exists and your service account has permissions."
else
  echo "✅ Verified access to GCS bucket: gs://$GCS_BUCKET_NAME"
fi

# Execute any provided command (e.g. cli.py --train)
if [ $# -gt 0 ]; then
  echo "🔹 Running command: $@"
  exec "$@"
else
  echo "💡 No command provided. Opening interactive shell..."
  exec /bin/bash
fi
